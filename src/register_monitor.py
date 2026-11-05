import sys
import re

from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QComboBox,
    QLabel,
    QFrame,
    QMessageBox,
    QApplication,
    QSizePolicy
)

from PyQt5.QtCore import Qt


# ============================================================
# REGISTER BLOCK
# ============================================================

class RegisterRow(QFrame):

    def __init__(self, parent_view=None):
        super().__init__()

        self.parent_view = parent_view
        self.setObjectName("RegisterBlock")
        self.signal_width = 1

        self.setMinimumHeight(230)
        self.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Fixed
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(12)

        # ----------------------------------------------------
        # 1. SIGNAL SELECTION ROW
        # ----------------------------------------------------
        sig_layout = QHBoxLayout()
        sig_layout.setSpacing(14)

        lbl_sig_tag = QLabel("SIGNAL:")
        lbl_sig_tag.setObjectName("TagLabel")
        lbl_sig_tag.setFixedWidth(100)

        self.combo = QComboBox()
        self.combo.addItem("-- Select Signal --")
        self.combo.setObjectName("RegisterCombo")
        self.combo.setMinimumHeight(50)
        self.combo.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Fixed
        )
        self.combo.setMaxVisibleItems(15)
        self.combo.currentIndexChanged.connect(self._on_selection_changed)

        sig_layout.addWidget(lbl_sig_tag)
        sig_layout.addWidget(self.combo, 1)
        layout.addLayout(sig_layout)

        # ----------------------------------------------------
        # 2. WIDTH DISPLAY ROW
        # ----------------------------------------------------
        width_layout = QHBoxLayout()
        width_layout.setSpacing(14)

        lbl_width_tag = QLabel("WIDTH:")
        lbl_width_tag.setObjectName("TagLabel")
        lbl_width_tag.setFixedWidth(100)

        self.lbl_width_info = QLabel("--")
        self.lbl_width_info.setObjectName("WidthInfoLabel")

        width_layout.addWidget(lbl_width_tag)
        width_layout.addWidget(self.lbl_width_info)
        width_layout.addStretch()
        layout.addLayout(width_layout)

        # ----------------------------------------------------
        # 3. HEXADECIMAL DISPLAY ROW
        # ----------------------------------------------------
        hex_layout = QHBoxLayout()
        hex_layout.setSpacing(14)

        lbl_hex_tag = QLabel("HEX:")
        lbl_hex_tag.setObjectName("TagLabel")
        lbl_hex_tag.setFixedWidth(100)

        self.lbl_hex = QLabel("")
        self.lbl_hex.setObjectName("DigitalDisplayHex")
        self.lbl_hex.setMinimumHeight(50)
        self.lbl_hex.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        hex_layout.addWidget(lbl_hex_tag)
        hex_layout.addWidget(self.lbl_hex, 1)
        layout.addLayout(hex_layout)

        # ----------------------------------------------------
        # 4. BINARY DISPLAY ROW
        # ----------------------------------------------------
        bin_layout = QHBoxLayout()
        bin_layout.setSpacing(14)

        lbl_bin_tag = QLabel("BIN:")
        lbl_bin_tag.setObjectName("TagLabel")
        lbl_bin_tag.setFixedWidth(100)

        self.lbl_bin = QLabel("")
        self.lbl_bin.setObjectName("DigitalDisplayBin")
        self.lbl_bin.setMinimumHeight(48)
        self.lbl_bin.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        bin_layout.addWidget(lbl_bin_tag)
        bin_layout.addWidget(self.lbl_bin, 1)
        layout.addLayout(bin_layout)

        self._apply_style()

    # --------------------------------------------------------
    # STYLING (Matched to String Input Theme)
    # --------------------------------------------------------

    def _apply_style(self):

        self.setStyleSheet("""
            QFrame#RegisterBlock {
                background-color: #171E29;
                border: 1px solid #2B394B;
                border-radius: 11px;
            }

            QLabel#TagLabel {
                color: #8193AA;
                font-family: 'Consolas', monospace;
                font-size: 16px;
                font-weight: bold;
                letter-spacing: 1.5px;
            }

            QLabel#WidthInfoLabel {
                color: #45F5A5;
                font-family: 'Consolas', monospace;
                font-size: 18px;
                font-weight: bold;
            }

            QComboBox#RegisterCombo {
                background-color: #0A1018;
                color: #45F5A5;
                border: 1px solid #29384A;
                border-radius: 6px;
                padding-left: 12px;
                padding-right: 8px;
                font-family: 'Consolas', monospace;
                font-size: 18px;
                font-weight: bold;
            }

            QComboBox#RegisterCombo:hover {
                border: 1px solid #39DFA1;
            }

            QComboBox#RegisterCombo QAbstractItemView {
                background-color: #0A1018;
                color: #D6E0EE;
                selection-background-color: #176B56;
                selection-color: #FFFFFF;
                border: 1px solid #29384A;
                outline: none;
                padding: 6px;
                font-family: 'Consolas', monospace;
                font-size: 16px;
            }

            QLabel#DigitalDisplayHex {
                background-color: #0A1018;
                color: #43C5F2;
                border: 1px solid #29384A;
                border-radius: 8px;
                padding-left: 16px;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 28px;
                font-weight: bold;
                letter-spacing: 2px;
            }

            QLabel#DigitalDisplayBin {
                background-color: #0A1018;
                color: #45F5A5;
                border: 1px solid #29384A;
                border-radius: 8px;
                padding-left: 16px;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 22px;
                font-weight: bold;
                letter-spacing: 1px;
            }
        """)

    # --------------------------------------------------------
    # SELECTION & OPTIONS HANDLING
    # --------------------------------------------------------

    def _on_selection_changed(self, index):

        sig_name = self.combo.currentText()

        if sig_name == "-- Select Signal --" or not sig_name:
            self.lbl_width_info.setText("--")
            self.lbl_hex.setText("")
            self.lbl_bin.setText("")
            return

        if self.parent_view:
            width = self.parent_view.get_signal_width(sig_name)
            self.signal_width = width
            unit_str = "bit" if width == 1 else "bits"
            self.lbl_width_info.setText(f"{width} {unit_str}")

    def update_options(self, display_names):

        current_selection = self.combo.currentText()

        self.combo.blockSignals(True)
        self.combo.clear()
        self.combo.addItem("-- Select Signal --")
        self.combo.addItems(display_names)

        if current_selection in display_names:
            idx = self.combo.findText(current_selection)
            if idx >= 0:
                self.combo.setCurrentIndex(idx)
        else:
            self.combo.setCurrentIndex(0)

        self.combo.blockSignals(False)
        self._on_selection_changed(self.combo.currentIndex())


# ============================================================
# REGISTER MONITOR
# ============================================================

class RegisterMonitorView(QWidget):

    def __init__(self):

        super().__init__()

        self.setObjectName("RegisterMonitorView")
        self.signal_widths = {}

        self._build_ui()
        self._apply_style()

    # --------------------------------------------------------
    # BUILD INTERFACE
    # --------------------------------------------------------

    def _build_ui(self):

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(22, 20, 22, 22)
        main_layout.setSpacing(22)

        # Centering stretch top
        main_layout.addStretch(1)

        # Exactly TWO centered register monitor blocks
        self.rows = [
            RegisterRow(parent_view=self)
            for _ in range(2)
        ]

        for row in self.rows:
            main_layout.addWidget(row)

        # Centering stretch bottom
        main_layout.addStretch(1)

    # --------------------------------------------------------
    # MAIN STYLE
    # --------------------------------------------------------

    def _apply_style(self):

        self.setStyleSheet("""
            QWidget#RegisterMonitorView {
                background-color: #10141B;
                color: #D6E0EE;
                font-family: 'Segoe UI', sans-serif;
            }
        """)

    # --------------------------------------------------------
    # SIGNAL WIDTH QUERY
    # --------------------------------------------------------

    def get_signal_width(self, sig_name):

        return self.signal_widths.get(sig_name, 1)

    # --------------------------------------------------------
    # SIGNAL DISCOVERY
    # --------------------------------------------------------

    def set_available_signals(self, signals_input):

        """Populates dropdowns with available Verilog signals and resolves true static bit-widths."""

        self.signal_widths.clear()
        display_names = []

        if isinstance(signals_input, dict):
            for name, w in signals_input.items():
                clean_name = re.sub(r'\[.*?\]', '', str(name)).strip()
                width = min(max(1, int(w)), 32)
                self.signal_widths[clean_name] = width
                if clean_name not in display_names:
                    display_names.append(clean_name)
        elif isinstance(signals_input, (list, tuple)):
            for item in signals_input:
                if isinstance(item, dict):
                    name = item.get('name', '')
                    w = item.get('width', 32)
                    clean_name = re.sub(r'\[.*?\]', '', str(name)).strip()
                    if clean_name:
                        self.signal_widths[clean_name] = min(max(1, int(w)), 32)
                        if clean_name not in display_names:
                            display_names.append(clean_name)
                elif isinstance(item, tuple):
                    clean_name = re.sub(r'\[.*?\]', '', str(item[0])).strip()
                    w = int(item[1])
                    if clean_name:
                        self.signal_widths[clean_name] = min(max(1, w), 32)
                        if clean_name not in display_names:
                            display_names.append(clean_name)
                else:
                    s_str = str(item).strip()
                    m = re.search(r'\[\s*(\d+)\s*:\s*(\d+)\s*\]', s_str)
                    clean_name = re.sub(r'\[.*?\]', '', s_str).strip()
                    if clean_name:
                        if m:
                            msb, lsb = int(m.group(1)), int(m.group(2))
                            width = abs(msb - lsb) + 1
                            self.signal_widths[clean_name] = min(max(1, width), 32)
                        else:
                            # Scalar wires / clocks default to 1 bit, unknown buses stay 8
                            if s_str in ['clk', 'rst', 'we', 'btn_count', 'btn_checkpoint', 'serial0', 'serial1'] or s_str.startswith('btn_'):
                                self.signal_widths[clean_name] = 1
                            elif clean_name not in self.signal_widths:
                                self.signal_widths[clean_name] = 8

                        if clean_name not in display_names:
                            display_names.append(clean_name)

        for row in self.rows:
            row.update_options(display_names)

    # --------------------------------------------------------
    # LIVE DATA SYNCHRONIZATION
    # --------------------------------------------------------

    def sync_data(self, state_dict):

        """Updates Hex and Binary displays from live simulation data strictly using static declared width."""

        for row in self.rows:

            selected_sig = row.combo.currentText()

            if selected_sig in state_dict and selected_sig != "-- Select Signal --":

                raw_val = int(state_dict[selected_sig])
                width = self.signal_widths.get(selected_sig, 8)
                width = min(width, 32)

                mask = (1 << width) - 1 if width < 32 else 0xFFFFFFFF
                val = raw_val & mask

                hex_digits = max(1, (width + 3) // 4)
                row.lbl_hex.setText(f"0x{val:0{hex_digits}X}")
                row.lbl_bin.setText(f"0b{val:0{width}b}")

            else:

                if selected_sig == "-- Select Signal --":
                    row.lbl_width_info.setText("--")
                row.lbl_hex.setText("")
                row.lbl_bin.setText("")

    # --------------------------------------------------------
    # HELP
    # --------------------------------------------------------

    def show_help(self):

        msg = QMessageBox()

        msg.setWindowTitle(
            "Learner Guide: Dynamic Signal Probe"
        )

        msg.setText(
            "<b>Dynamic Signal Probe Mapping</b><br><br>"
            "This tool scans your active Verilog design for signal declarations "
            "and bit widths.<br><br>"

            "<b>Features:</b><br>"
            "• <b>Static True-Width Display:</b> Displays exact declared signal bit-widths (e.g., 1-bit clocks vs 8-bit registers).<br>"
            "• <b>Dual Hex & Binary Readouts:</b> Shows live <b>HEX</b> and <b>BIN</b> values on every clock pulse formatted strictly to the static signal width."
        )

        msg.exec_()


# ============================================================
# STANDALONE PREVIEW
# ============================================================

if __name__ == "__main__":

    app = QApplication(sys.argv)

    window = RegisterMonitorView()
    window.resize(680, 650)
    window.setWindowTitle(
        "HDL Sandbox - Register Monitor"
    )

    window.set_available_signals({
        "clk": 1,
        "btn_count": 1,
        "btn_checkpoint": 1,
        "counter[7:0]": 8,
        "checkpoint[7:0]": 8
    })

    window.show()

    sys.exit(app.exec_())