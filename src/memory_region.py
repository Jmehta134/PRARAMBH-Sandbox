import sys
import re

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QLCDNumber, QApplication, QMessageBox, QGridLayout,
    QTableWidget, QTableWidgetItem, QHeaderView, QComboBox
)
from PyQt5.QtGui import QFont, QColor, QBrush
from PyQt5.QtCore import Qt, pyqtSignal

# =============================================================================
# MEMORY MAP CONFIGURATION
# =============================================================================

RAM_BASE = 0x0000
RAM_SIZE = 64

ROM_BASE = 0x0200
ROM_SIZE = 128

BYTES_PER_ROW = 4

# =============================================================================
# VALUE CONVERSION
# =============================================================================

def parse_memory_byte(value):
    if value is None: return None
    if isinstance(value, bool): return int(value)
    if isinstance(value, int): return value if 0 <= value <= 255 else None
    if isinstance(value, bytes):
        try: value = value.decode("ascii")
        except UnicodeDecodeError: return None
    if isinstance(value, str):
        text = value.strip().lower().replace("_", "")
        if not text: return None
        match = re.fullmatch(r"(?:\d+)?'([sS]?)([bBoOdDhH])([0-9a-fA-FxXzZ?]+)", text)
        if match:
            base_char = match.group(2).lower()
            digits = match.group(3)
            if any(ch in digits.lower() for ch in ("x", "z", "?")): return None
            try:
                base = {"b": 2, "o": 8, "d": 10, "h": 16}[base_char]
                result = int(digits, base)
                return result if 0 <= result <= 255 else None
            except (ValueError, KeyError): return None
        if text.startswith("0x"):
            digits = text[2:]
            if any(ch in digits for ch in ("x", "z", "?")): return None
            try:
                result = int(digits, 16)
                return result if 0 <= result <= 255 else None
            except ValueError: return None
        if text.startswith("0b"):
            digits = text[2:]
            if any(ch in digits for ch in ("x", "z", "?")): return None
            try:
                result = int(digits, 2)
                return result if 0 <= result <= 255 else None
            except ValueError: return None
        if any(ch in text for ch in ("x", "z", "?")): return None
        if len(text) == 8 and all(ch in "01" for ch in text): return int(text, 2)
        try:
            result = int(text, 16)
            return result if 0 <= result <= 255 else None
        except ValueError: return None
    return None


def parse_memory_index(key):
    if isinstance(key, int): return key
    text = str(key).strip().lower()
    match = re.fullmatch(r"(?:ram|rom)\[(.+)\]", text)
    if match: text = match.group(1).strip()
    try: return int(text, 0)
    except ValueError:
        try: return int(text, 10)
        except ValueError: return None

# =============================================================================
# COMPONENT: HEX MEMORY GRID
# =============================================================================

class HexMemoryGrid(QTableWidget):
    def __init__(self, rows=16, cols=4):
        super().__init__(rows, cols + 2)
        self.setHorizontalHeaderLabels(["ADDRESS", "0", "1", "2", "3", "ASCII"])
        self.verticalHeader().setVisible(False)
        self.setEditTriggers(QTableWidget.NoEditTriggers)
        self.setSelectionBehavior(QTableWidget.SelectItems)
        self.setSelectionMode(QTableWidget.SingleSelection)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setStyleSheet("""
            QTableWidget {
                background-color: #121212;
                gridline-color: #2D2D2D;
                color: #00FF00;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 16px;
                font-weight: bold;
                border: 2px solid #333333;
                border-radius: 6px;
            }
            QHeaderView::section {
                background-color: #1E1E1E;
                color: #00E5FF;
                font-weight: bold;
                font-family: 'Consolas', monospace;
                font-size: 15px;
                padding: 6px;
                border: 1px solid #2A2A2A;
            }
            QTableWidget::item { padding: 4px; }
            QTableWidget::item:selected { background-color: #005A9E; color: #FFFFFF; }
            QScrollBar:vertical {
                background-color: #1A1A1A;
                width: 14px;
                margin: 2px;
                border-radius: 5px;
                border: 1px solid #333333;
            }
            QScrollBar::handle:vertical { background-color: #00E5FF; min-height: 25px; border-radius: 4px; }
            QScrollBar::handle:vertical:hover { background-color: #00B8D4; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical,
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { height: 0px; background: none; }
        """)
        header = self.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Interactive)
        self.setColumnWidth(0, 115)
        header.setSectionResizeMode(5, QHeaderView.Interactive)
        self.setColumnWidth(5, 110)
        for column in range(1, 5):
            header.setSectionResizeMode(column, QHeaderView.Stretch)
        self.verticalHeader().setDefaultSectionSize(34)
        self.setShowGrid(True)


# =============================================================================
# MAIN COMPONENT: MEMORY REGION INSPECTOR
# =============================================================================

class MemoryRegionView(QWidget):
    memory_updated = pyqtSignal(int, object)

    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(15, 15, 15, 15)

        self.ram_memory = [None] * RAM_SIZE
        self.rom_memory = [None] * ROM_SIZE
        self.ram_prev = [None] * RAM_SIZE
        self.rom_prev = [None] * ROM_SIZE
        self.ram_changed = set()
        self.rom_changed = set()
        self.ram_initialized = False
        self.rom_initialized = False
        self.base_address = RAM_BASE
        self.selected_address = None
        self.last_simulation_time = None

        # --- TOP: MEMORY REGION SELECTOR ---
        ctrl_frame = QFrame()
        ctrl_frame.setStyleSheet("""
            QFrame { background-color: #151515; border: 2px solid #333333; border-radius: 8px; }
            QLabel { color: #00E5FF; font-weight: bold; font-size: 14px; border: none; }
            QComboBox {
                background-color: #1E1E1E; color: #FFFFFF; border: 1px solid #00E5FF;
                border-radius: 4px; padding: 6px 12px; font-family: 'Consolas', monospace;
                font-size: 14px; font-weight: bold;
            }
        """)
        ctrl_layout = QHBoxLayout(ctrl_frame)
        ctrl_layout.setContentsMargins(20, 10, 20, 10)
        ctrl_layout.addWidget(QLabel("MEMORY MAP REGION:"))
        self.cmb_preset = QComboBox()
        self.cmb_preset.addItems(["RAM (0x0000 - 64 Bytes)", "ROM (0x0200 - 128 Bytes)"])
        self.cmb_preset.currentIndexChanged.connect(self.on_preset_changed)
        ctrl_layout.addWidget(self.cmb_preset, stretch=1)
        self.lbl_status = QLabel("Waiting for simulator data")
        self.lbl_status.setStyleSheet("color: #FFB74D; font-size: 12px; border: none;")
        ctrl_layout.addWidget(self.lbl_status)
        self.layout.addWidget(ctrl_frame)
        self.layout.addSpacing(10)

        # --- MIDDLE: MEMORY GRID ---
        self.grid = HexMemoryGrid(rows=16, cols=BYTES_PER_ROW)
        self.grid.itemSelectionChanged.connect(self.on_cell_selected)
        self.layout.addWidget(self.grid)
        self.layout.addSpacing(10)

        # --- BOTTOM: BYTE INSPECTOR ---
        control_box = QFrame()
        control_box.setStyleSheet("QFrame { border: 2px solid #CCCCCC; border-radius: 8px; background-color: #E5E5E5; }")
        control_lay = QGridLayout(control_box)
        control_lay.setContentsMargins(15, 12, 15, 12)
        control_lay.setHorizontalSpacing(10)
        control_lay.setVerticalSpacing(6)

        lbl_style = "font-weight: 900; color: #444444; font-size: 11px; border: none; background: transparent;"
        val_style = "background-color: #FFFFFF; border: 2px solid #ADADAD; padding: 5px; border-radius: 4px; font-weight: bold; font-size: 14px; color: #005A9E; font-family: monospace;"
        bin_style = "background-color: #1E1E1E; border: 2px inset #555555; padding: 5px; border-radius: 4px; font-weight: bold; font-size: 14px; color: #FFB74D; font-family: monospace;"

        def make_label(text):
            label = QLabel(text)
            label.setStyleSheet(lbl_style)
            label.setAlignment(Qt.AlignCenter)
            return label

        def make_value(text, style):
            label = QLabel(text)
            label.setStyleSheet(style)
            label.setAlignment(Qt.AlignCenter)
            return label

        self.lbl_sel_addr = make_value("----", val_style)
        
        self.lcd_hex = QLCDNumber()
        self.lcd_hex.setDigitCount(2)
        self.lcd_hex.setFixedSize(70, 36)
        self.lcd_hex.setHexMode()
        self.lcd_hex.setStyleSheet("QLCDNumber { background-color: #1E1E1E; color: #00FF00; border: 2px inset #555555; border-radius: 4px; }")

        self.lbl_bin_val = make_value("XXXXXXXX", bin_style)

        headers = ["ADDR", "BYTE (HEX)", "BYTE (BIN)"]
        widgets = [self.lbl_sel_addr, self.lcd_hex, self.lbl_bin_val]

        for column, header_text in enumerate(headers):
            control_lay.addWidget(make_label(header_text), 0, column)
            control_lay.addWidget(widgets[column], 1, column)

        self.layout.addWidget(control_box)
        self.refresh_memory_display()

    def sync_data(self, state_dict):
        if not isinstance(state_dict, dict):
            self._set_error("Invalid simulator snapshot: expected dictionary")
            return

        errors = []
        old_ram = self.ram_memory.copy()
        old_rom = self.rom_memory.copy()

        if "ram" in state_dict:
            errors.extend(self._apply_region_data(state_dict["ram"], self.ram_memory, RAM_SIZE, "RAM"))
            self.ram_initialized = True

        if "rom" in state_dict:
            errors.extend(self._apply_region_data(state_dict["rom"], self.rom_memory, ROM_SIZE, "ROM"))
            self.rom_initialized = True

        for key, value in state_dict.items():
            if not isinstance(key, str): continue
            match = re.fullmatch(r"(ram|rom)\[(.+)\]", key.strip(), re.IGNORECASE)
            if not match: continue
            region = match.group(1).lower()
            index = parse_memory_index(match.group(2))

            if index is None:
                errors.append(f"Invalid memory index: {key}")
                continue

            memory = self.ram_memory if region == "ram" else self.rom_memory
            size = RAM_SIZE if region == "ram" else ROM_SIZE

            if not 0 <= index < size:
                errors.append(f"{region.upper()} index out of range: {index}")
                continue

            parsed = parse_memory_byte(value)
            memory[index] = parsed

            if region == "ram": self.ram_initialized = True
            else: self.rom_initialized = True

        self.ram_prev = old_ram
        self.rom_prev = old_rom
        self.ram_changed = {i for i in range(RAM_SIZE) if old_ram[i] != self.ram_memory[i]}
        self.rom_changed = {i for i in range(ROM_SIZE) if old_rom[i] != self.rom_memory[i]}

        if "simulation_time" in state_dict:
            self.last_simulation_time = state_dict["simulation_time"]
        if state_dict.get("rom_init_error"):
            errors.append("ROM initialization failed. Check rom.hex path.")

        if errors: self._set_error("; ".join(errors))
        else: self._update_status()

        self.refresh_memory_display()

    def _apply_region_data(self, source, destination, expected_size, region_name):
        errors = []
        if isinstance(source, (bytes, bytearray)): iterator = enumerate(source)
        elif isinstance(source, (list, tuple)): iterator = enumerate(source)
        elif isinstance(source, dict): iterator = source.items()
        else: return [f"Invalid {region_name} data type: {type(source).__name__}"]

        for key, value in iterator:
            index = parse_memory_index(key)
            if index is None:
                errors.append(f"Invalid {region_name} index: {key}")
                continue
            if not 0 <= index < expected_size:
                errors.append(f"{region_name} index out of range: {index}")
                continue
            destination[index] = parse_memory_byte(value)
        return errors

    def get_region_info(self, absolute_address):
        if RAM_BASE <= absolute_address < RAM_BASE + RAM_SIZE:
            return ("RAM", absolute_address - RAM_BASE, RAM_SIZE)
        if ROM_BASE <= absolute_address < ROM_BASE + ROM_SIZE:
            return ("ROM", absolute_address - ROM_BASE, ROM_SIZE)
        return None

    def inspect_address(self, absolute_address):
        info = self.get_region_info(absolute_address)
        if info is None:
            self._set_error(f"Invalid memory address: 0x{absolute_address:04X}")
            return None
        region, offset, size = info
        memory = self.ram_memory if region == "RAM" else self.rom_memory
        return memory[offset]

    def on_preset_changed(self, index):
        if index == 0: self.base_address = RAM_BASE
        elif index == 1: self.base_address = ROM_BASE
        else: return
        self.selected_address = None
        self.clear_inspector()
        self.refresh_memory_display()

    def _format_hex(self, value): return "XX" if value is None else f"{value:02X}"
    def _format_ascii(self, value):
        if value is None: return "?"
        if 32 <= value <= 126: return chr(value)
        return "."

    def _set_error(self, message):
        self.lbl_status.setText(message)
        self.lbl_status.setStyleSheet("color: #FF5252; font-size: 11px; border: none;")

    def _update_status(self):
        if self.ram_initialized or self.rom_initialized:
            parts = []
            if self.ram_initialized: parts.append("RAM synced")
            if self.rom_initialized: parts.append("ROM synced")
            if self.last_simulation_time is not None: parts.append(f"Time: {self.last_simulation_time}")
            self.lbl_status.setText(" | ".join(parts))
            self.lbl_status.setStyleSheet("color: #00C853; font-size: 11px; border: none;")
        else:
            self.lbl_status.setText("Waiting for simulator data")

    def refresh_memory_display(self):
        self.grid.blockSignals(True)

        if self.base_address == RAM_BASE:
            active_memory = self.ram_memory
            changed = self.ram_changed
            rows_needed = RAM_SIZE // BYTES_PER_ROW
        else:
            active_memory = self.rom_memory
            changed = self.rom_changed
            rows_needed = ROM_SIZE // BYTES_PER_ROW

        self.grid.setRowCount(rows_needed)

        for row in range(rows_needed):
            row_offset = row * BYTES_PER_ROW
            row_address = self.base_address + row_offset
            
            address_item = QTableWidgetItem(f"0x{row_address:04X}")
            address_item.setForeground(QBrush(QColor("#00E5FF")))
            address_item.setTextAlignment(Qt.AlignCenter)
            self.grid.setItem(row, 0, address_item)
            ascii_text = ""

            for column in range(BYTES_PER_ROW):
                index = row_offset + column
                value = active_memory[index]
                hex_item = QTableWidgetItem(self._format_hex(value))
                hex_item.setTextAlignment(Qt.AlignCenter)

                if value is None:
                    hex_item.setForeground(QBrush(QColor("#FF5252")))
                    hex_item.setBackground(QBrush(QColor("#301515")))
                    ascii_text += "?"
                elif index in changed:
                    hex_item.setForeground(QBrush(QColor("#FFFF00")))
                    hex_item.setBackground(QBrush(QColor("#333300")))
                    ascii_text += self._format_ascii(value)
                elif value != 0:
                    hex_item.setForeground(QBrush(QColor("#00FF00")))
                    ascii_text += self._format_ascii(value)
                else:
                    hex_item.setForeground(QBrush(QColor("#666666")))
                    ascii_text += "."
                self.grid.setItem(row, column + 1, hex_item)

            ascii_item = QTableWidgetItem(ascii_text)
            ascii_item.setForeground(QBrush(QColor("#FFB74D")))
            ascii_item.setTextAlignment(Qt.AlignCenter)
            self.grid.setItem(row, 5, ascii_item)

        if self.selected_address is not None:
            selected_offset = self.selected_address - self.base_address
            if 0 <= selected_offset < len(active_memory):
                row = selected_offset // BYTES_PER_ROW
                column = (selected_offset % BYTES_PER_ROW) + 1
                self.grid.setCurrentCell(row, column)

        self.grid.blockSignals(False)
        self.update_inspector()

    def clear_inspector(self):
        self.lbl_sel_addr.setText("----")
        self.lcd_hex.display("--")
        self.lbl_bin_val.setText("XXXXXXXX")

    def update_inspector(self):
        if self.selected_address is None:
            self.clear_inspector()
            return
        info = self.get_region_info(self.selected_address)
        if info is None:
            self.clear_inspector()
            return

        region, offset, _ = info
        memory = self.ram_memory if region == "RAM" else self.rom_memory
        value = memory[offset]

        self.lbl_sel_addr.setText(f"0x{self.selected_address:04X}")

        if value is None:
            self.lcd_hex.display("XX")
            self.lbl_bin_val.setText("XXXXXXXX")
        else:
            self.lcd_hex.display(f"{value:02X}")
            self.lbl_bin_val.setText(f"{value:08b}")

    def on_cell_selected(self):
        items = self.grid.selectedItems()
        if not items: return
        item = items[0]
        row = item.row()
        column = item.column()
        
        if not 1 <= column <= 4: return

        offset = row * BYTES_PER_ROW + column - 1
        absolute_address = self.base_address + offset

        info = self.get_region_info(absolute_address)
        if info is None:
            self._set_error("Selected address is outside the memory map")
            return

        self.selected_address = absolute_address
        value = self.inspect_address(absolute_address)
        self.update_inspector()
        self.memory_updated.emit(absolute_address, value)

    def set_auto_clock(self, active: bool): pass

    def clear_changed_highlights(self):
        self.ram_changed.clear()
        self.rom_changed.clear()
        self.refresh_memory_display()

    def reset_snapshot(self):
        self.ram_memory = [None] * RAM_SIZE
        self.rom_memory = [None] * ROM_SIZE
        self.ram_prev = [None] * RAM_SIZE
        self.rom_prev = [None] * ROM_SIZE
        self.ram_changed.clear()
        self.rom_changed.clear()
        self.ram_initialized = False
        self.rom_initialized = False
        self.selected_address = None
        self.last_simulation_time = None
        self.clear_inspector()
        self._update_status()
        self.refresh_memory_display()

    def show_help(self):
        msg = QMessageBox(self)
        msg.setWindowTitle("Hardware Memory Region Inspector Guide")
        msg.setText(
            "<b>Hardware Memory Region Inspector</b><br><br>"
            "<b>1. Automatic Hardware Interface SNOOPING</b><br>"
            "This interface acts as the external memory bank for your logic design. "
            "When your Verilog module includes standard write control signals (`we`, `addr`, `wdata`), "
            "the simulation engine intercepts writes dynamically without requiring internal Verilog array declarations.<br><br>"
            "<b>2. Performing Memory Writes</b><br>"
            "1. Click <b>▶ Compile</b> to launch the simulation.<br>"
            "2. In the <b>Hardware Controls</b> pane, set <code>we = 1</code>, <code>addr = &lt;target_offset&gt;</code>, and <code>wdata = &lt;value&gt;</code>.<br>"
            "3. Pulse the <code>clk</code> signal. The memory table cell will immediately update and highlight in yellow.<br><br>"
            "<b>3. Reading Data</b><br>"
            "• <b>Visual Inspection:</b> Click on any hex byte cell in the grid to view its absolute address, hex value, and binary representation in the bottom inspector.<br>"
            "• <b>In Verilog:</b> Set <code>we = 0</code> (Read mode) and output the contents of your memory array onto an <code>rdata</code> wire mapped to the Register Monitor."
        )
        msg.exec_()