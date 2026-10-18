import sys
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, 
    QLCDNumber, QApplication, QMessageBox, QGridLayout,
    QTableWidget, QTableWidgetItem, QHeaderView, QComboBox
)
from PyQt5.QtGui import QFont, QColor, QBrush
from PyQt5.QtCore import Qt, pyqtSignal

# =============================================================================
# COMPONENT: Responsive Large Hex Memory Grid Viewer (4 Data Columns)
# =============================================================================
class HexMemoryGrid(QTableWidget):
    def __init__(self, rows=16, cols=4):
        super().__init__(rows, cols + 2)  # Address + 4 Data Bytes + ASCII = 6 cols
        
        # Setup Headers (Single-digit byte offsets: 0, 1, 2, 3)
        col_headers = ["ADDRESS"] + [str(i) for i in range(4)] + ["ASCII"]
        self.setHorizontalHeaderLabels(col_headers)
        self.verticalHeader().setVisible(False)
        
        # Disable Horizontal Scrollbar Completely
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        # Kakooii Styling with High-Contrast Custom Vertical Scrollbar
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
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 15px;
                padding: 6px;
                border: 1px solid #2A2A2A;
            }
            QTableWidget::item {
                padding: 4px;
            }
            QTableWidget::item:selected {
                background-color: #005A9E;
                color: #FFFFFF;
            }
            /* High-Contrast Custom Vertical Scrollbar */
            QScrollBar:vertical {
                background-color: #1A1A1A;
                width: 14px;
                margin: 2px 2px 2px 2px;
                border-radius: 5px;
                border: 1px solid #333333;
            }
            QScrollBar::handle:vertical {
                background-color: #00E5FF;
                min-height: 25px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #00B8D4;
            }
            QScrollBar::handle:vertical:pressed {
                background-color: #008899;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
                background: none;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }
        """)
        
        # Column Resizing Logic for Side-to-Side Fit
        header = self.horizontalHeader()
        
        # Address (4 hex digits + 0x) and ASCII columns
        header.setSectionResizeMode(0, QHeaderView.Interactive)
        self.setColumnWidth(0, 115)
        
        header.setSectionResizeMode(5, QHeaderView.Interactive)
        self.setColumnWidth(5, 110)
        
        # Stretch 4 Hex Data Columns (1 through 4) evenly across remaining space
        for c in range(1, 5):
            header.setSectionResizeMode(c, QHeaderView.Stretch)
        
        self.verticalHeader().setDefaultSectionSize(34)
        self.setShowGrid(True)


# =============================================================================
# MAIN PANE: Memory Region View
# =============================================================================
class MemoryRegionView(QWidget):
    memory_updated = pyqtSignal(int, int)  # Address, Value

    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(15, 15, 15, 15)

        # --- Top Section: 2-Region Memory Map Selector Bar ---
        ctrl_frame = QFrame()
        ctrl_frame.setStyleSheet("""
            QFrame {
                background-color: #151515;
                border: 2px solid #333333;
                border-radius: 8px;
            }
            QLabel {
                color: #00E5FF;
                font-weight: bold;
                font-size: 14px;
                border: none;
                letter-spacing: 1px;
            }
            QComboBox {
                background-color: #1E1E1E;
                color: #FFFFFF;
                border: 1px solid #00E5FF;
                border-radius: 4px;
                padding: 6px 12px;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 14px;
                font-weight: bold;
            }
            QComboBox::drop-down {
                border: none;
            }
        """)
        ctrl_layout = QHBoxLayout(ctrl_frame)
        ctrl_layout.setContentsMargins(20, 10, 20, 10)

        ctrl_layout.addWidget(QLabel("MEMORY MAP REGION:"))
        
        self.cmb_preset = QComboBox()
        self.cmb_preset.addItems([
            "RAM (0x0000 - 64 Bytes)", 
            "SCRATCHPAD (0x0200 - 128 Bytes)"
        ])
        self.cmb_preset.currentIndexChanged.connect(self.on_preset_changed)
        ctrl_layout.addWidget(self.cmb_preset, stretch=1)

        self.layout.addWidget(ctrl_frame)
        self.layout.addSpacing(10)

        # --- Middle Section: Hex Memory View (4 Data Columns) ---
        self.grid = HexMemoryGrid(rows=16, cols=4)
        self.grid.itemSelectionChanged.connect(self.on_cell_selected)
        self.layout.addWidget(self.grid)

        self.layout.addSpacing(10)

        # --- Bottom Section: Live Inspector Box ---
        control_box = QFrame()
        control_box.setStyleSheet("""
            QFrame {
                border: 2px solid #CCCCCC;
                border-radius: 8px;
                background-color: #E5E5E5;
            }
        """)
        
        control_lay = QGridLayout(control_box)
        control_lay.setContentsMargins(20, 12, 20, 12)
        control_lay.setHorizontalSpacing(25)
        control_lay.setVerticalSpacing(6)

        lbl_style = "font-weight: 900; color: #444444; font-size: 12px; letter-spacing: 1px; border: none; background: transparent;"
        
        lbl_target = QLabel("SELECTED ADDRESS:")
        lbl_target.setStyleSheet(lbl_style)
        lbl_target.setAlignment(Qt.AlignCenter)
        
        lbl_hex = QLabel("BYTE (HEX):")
        lbl_hex.setStyleSheet(lbl_style)
        lbl_hex.setAlignment(Qt.AlignCenter)

        lbl_dec = QLabel("BYTE (DEC):")
        lbl_dec.setStyleSheet(lbl_style)
        lbl_dec.setAlignment(Qt.AlignCenter)

        lbl_bin = QLabel("BYTE (BIN):")
        lbl_bin.setStyleSheet(lbl_style)
        lbl_bin.setAlignment(Qt.AlignCenter)

        # Value Readouts
        self.lbl_sel_addr = QLabel("0x0000")
        self.lbl_sel_addr.setStyleSheet("""
            background-color: #FFFFFF; border: 2px solid #ADADAD;
            padding: 5px 12px; border-radius: 4px; font-weight: bold;
            font-size: 16px; color: #005A9E; font-family: monospace;
        """)
        self.lbl_sel_addr.setAlignment(Qt.AlignCenter)

        self.lcd_hex = self._create_lcd("#00FF00", 2)
        self.lcd_hex.setHexMode()
        
        self.lcd_dec = self._create_lcd("#00E5FF", 3)
        self.lcd_dec.setDecMode()

        self.lbl_bin_val = QLabel("00000000")
        self.lbl_bin_val.setStyleSheet("""
            background-color: #1E1E1E; border: 2px inset #555555;
            padding: 5px 10px; border-radius: 4px; font-weight: bold;
            font-size: 16px; color: #FFB74D; font-family: monospace;
        """)
        self.lbl_bin_val.setAlignment(Qt.AlignCenter)

        control_lay.addWidget(lbl_target, 0, 0)
        control_lay.addWidget(lbl_hex, 0, 1)
        control_lay.addWidget(lbl_dec, 0, 2)
        control_lay.addWidget(lbl_bin, 0, 3)

        control_lay.addWidget(self.lbl_sel_addr, 1, 0)
        control_lay.addWidget(self.lcd_hex, 1, 1)
        control_lay.addWidget(self.lcd_dec, 1, 2)
        control_lay.addWidget(self.lbl_bin_val, 1, 3)

        self.layout.addWidget(control_box)

        # --- Internal Memory Buffer ---
        # RAM:   0x0000 - 0x003F (64 Bytes)
        # FLASH: 0x0200 - 0x027F (128 Bytes)
        self.base_address = 0x0000
        self.memory_buffer = bytearray(640)  # Total buffer covering up to 0x0280
        
        self.refresh_memory_display()

    def _create_lcd(self, color_hex, digits):
        lcd = QLCDNumber()
        lcd.setDigitCount(digits)
        lcd.setFixedSize(80, 40)
        lcd.setStyleSheet(f"""
            QLCDNumber {{
                background-color: #1E1E1E; 
                color: {color_hex};
                border: 2px inset #555555; 
                border-radius: 4px;
            }}
        """)
        return lcd

    def sync_data(self, state_dict):
        """Refreshes memory grid on every clock pulse from simulation engine."""
        # 1. Direct bytearray / dict mapping
        if 'ram' in state_dict:
            ram_data = state_dict['ram']
            if isinstance(ram_data, (bytes, bytearray)):
                self.memory_buffer[:min(len(ram_data), 64)] = ram_data[:64]
            elif isinstance(ram_data, dict):
                for addr, val in ram_data.items():
                    if int(addr) < 64:
                        self.memory_buffer[int(addr)] = int(val) & 0xFF

        if 'scratchpad' in state_dict:
            sp_data = state_dict['scratchpad']
            sp_offset = 0x0200
            if isinstance(sp_data, (bytes, bytearray)):
                end_idx = min(sp_offset + len(sp_data), 640)
                self.memory_buffer[sp_offset:end_idx] = sp_data[:end_idx - sp_offset]
            elif isinstance(sp_data, dict):
                for addr, val in sp_data.items():
                    real_addr = sp_offset + int(addr)
                    if real_addr < 640:
                        self.memory_buffer[real_addr] = int(val) & 0xFF

        # 2. Direct current_addr / current_data signals
        if 'current_addr' in state_dict and 'current_data' in state_dict:
            try:
                addr = int(state_dict['current_addr'])
                val = int(state_dict['current_data'])
                if addr < len(self.memory_buffer):
                    self.memory_buffer[addr] = val & 0xFF
            except (ValueError, TypeError):
                pass

        # 3. Robust check for array signals (handles top.ram[0], ram[0], top.scratchpad[0], etc.)
        for key, val in state_dict.items():
            try:
                val_int = int(val) & 0xFF
                if 'ram[' in key:
                    idx = int(key.split('ram[')[1].split(']')[0])
                    if idx < 64:
                        self.memory_buffer[idx] = val_int
                elif 'scratchpad[' in key:
                    idx = int(key.split('scratchpad[')[1].split(']')[0])
                    if idx < 128:
                        self.memory_buffer[0x0200 + idx] = val_int
            except (ValueError, IndexError, TypeError):
                pass

        self.refresh_memory_display()

    def set_auto_clock(self, active: bool):
        """Kept for interface compatibility across views."""
        pass

    def on_preset_changed(self, idx):
        presets = [0x0000, 0x0200]
        self.base_address = presets[idx]
        self.refresh_memory_display()

    def refresh_memory_display(self):
        self.grid.blockSignals(True)
        
        rows_needed = 16 if self.base_address == 0x0000 else 32

        self.grid.setRowCount(rows_needed)

        for r in range(rows_needed):
            row_addr = self.base_address + (r * 4)
            
            # 4-Digit Address Column
            addr_item = QTableWidgetItem(f"0x{row_addr:04X}")
            addr_item.setForeground(QBrush(QColor("#00E5FF")))
            addr_item.setTextAlignment(Qt.AlignCenter)
            self.grid.setItem(r, 0, addr_item)

            ascii_str = ""
            # 4 Hex Data Bytes (0, 1, 2, 3)
            for c in range(4):
                curr_addr = row_addr + c
                val = self.memory_buffer[curr_addr] if curr_addr < len(self.memory_buffer) else 0
                
                hex_item = QTableWidgetItem(f"{val:02X}")
                hex_item.setTextAlignment(Qt.AlignCenter)
                
                if val != 0:
                    hex_item.setForeground(QBrush(QColor("#00FF00")))
                else:
                    hex_item.setForeground(QBrush(QColor("#555555")))

                self.grid.setItem(r, c + 1, hex_item)
                ascii_str += chr(val) if 32 <= val <= 126 else "."

            # ASCII Column at Index 5
            ascii_item = QTableWidgetItem(ascii_str)
            ascii_item.setForeground(QBrush(QColor("#FFB74D")))
            ascii_item.setTextAlignment(Qt.AlignCenter)
            self.grid.setItem(r, 5, ascii_item)

        self.grid.blockSignals(False)

        # Dynamic Update: Re-evaluate currently selected cell
        self.update_inspector()

    def update_inspector(self):
        """Reads the currently selected cell and updates the bottom inspector readouts."""
        items = self.grid.selectedItems()
        if not items:
            return

        row = items[0].row()
        col = items[0].column()

        # Ignore click on Address (0) or ASCII (5) columns
        if col < 1 or col > 4:
            return

        selected_addr = self.base_address + (row * 4) + (col - 1)
        val = self.memory_buffer[selected_addr] if selected_addr < len(self.memory_buffer) else 0

        self.lbl_sel_addr.setText(f"0x{selected_addr:04X}")
        self.lcd_hex.display(f"{val:02X}")
        self.lcd_dec.display(val)
        self.lbl_bin_val.setText(f"{val:08b}")

    def on_cell_selected(self):
        items = self.grid.selectedItems()
        if not items:
            return

        row = items[0].row()
        col = items[0].column()

        if col < 1 or col > 4:
            return

        selected_addr = self.base_address + (row * 4) + (col - 1)
        val = self.memory_buffer[selected_addr] if selected_addr < len(self.memory_buffer) else 0

        self.update_inspector()
        self.memory_updated.emit(selected_addr, val)

    def show_help(self):
        msg = QMessageBox(self)
        msg.setWindowTitle("Learner Guide: Memory Region Inspector")
        msg.setText(
            "<b>How to Use the Memory Region Inspector</b><br><br>"
            "This pane monitors dynamic hardware memory maps in real time.<br><br>"
            "<b>1. Selectable Memory Maps:</b><br>"
            "• <b>RAM (0x0000):</b> 64-Byte primary working memory.<br>"
            "• <b>SCRATCHPAD (0x0200):</b> 128-Byte secondary buffer for intermediate operations.<br><br>"
            "<b>2. How to Write from Verilog:</b><br>"
            "Declare 8-bit memory arrays in your Verilog code and assign values on a clock edge:<br>"
            "&nbsp;&nbsp;• <code>reg [7:0] ram [0:63];</code><br>"
            "&nbsp;&nbsp;• <code>reg [7:0] scratchpad [0:127];</code><br>"
            "&nbsp;&nbsp;• Write operation: <code>ram[addr] <= data_in;</code> or <code>scratchpad[addr] <= data_in;</code><br><br>"
            "<b>3. How to Retrieve & Inspect Data:</b><br>"
            "• Select either map region using the top dropdown menu.<br>"
            "• Step the simulation clock (<b>PULSE</b> or <b>AUTO</b>) — updated cells light up green.<br>"
            "• Click any cell in the 4-column grid to retrieve its <b>Hex</b>, <b>Decimal</b>, <b>Binary</b>, and <b>ASCII</b> representation in the bottom readout panel."
        )
        msg.exec_()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    test_window = QWidget()
    test_window.setStyleSheet("background-color: #FAFAFA;")
    layout = QVBoxLayout(test_window)
    
    module = MemoryRegionView()
    layout.addWidget(module)
    test_window.setWindowTitle("Test: Hardware Memory Region")
    test_window.resize(680, 750)
    test_window.show()
    sys.exit(app.exec_())