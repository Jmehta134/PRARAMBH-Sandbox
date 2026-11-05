import sys
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, 
    QLineEdit, QPushButton, QComboBox, QMessageBox, QApplication
)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt, pyqtSignal

# =============================================================================
# MAIN PANE: Dynamic ASCII String Input Interface
# =============================================================================
class StringInputView(QWidget):
    """
    Industrial ASCII String Injector Interface.
    Packs up to 16 ASCII characters into a wide Verilog input bus or string register.
    """
    # Emits (target_port_name, integer_packed_value)
    string_updated = pyqtSignal(str, object)

    def __init__(self):
        super().__init__()
        self.available_inputs = []
        self.setObjectName("StringInputView")

        self.setStyleSheet("""
            QWidget#StringInputView {
                background-color: #10141B;
                color: #D6E0EE;
                font-family: 'Segoe UI', sans-serif;
            }

            QFrame#PanelFrame {
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

            QComboBox#PortCombo {
                background-color: #0A1018;
                color: #45F5A5;
                border: 1px solid #29384A;
                border-radius: 6px;
                padding: 6px 12px;
                font-family: 'Consolas', monospace;
                font-size: 16px;
                font-weight: bold;
            }
            QComboBox#PortCombo:hover {
                border: 1px solid #39DFA1;
            }
            QComboBox#PortCombo QAbstractItemView {
                background-color: #0A1018;
                color: #D6E0EE;
                selection-background-color: #176B56;
                selection-color: #FFFFFF;
                border: 1px solid #29384A;
                padding: 6px;
                font-family: 'Consolas', monospace;
                font-size: 15px;
            }

            QLineEdit#StringInput {
                background-color: #0A1018;
                color: #45F5A5;
                border: 1px solid #29384A;
                border-radius: 8px;
                padding: 8px 16px;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 22px;
                font-weight: bold;
                selection-background-color: #176B56;
                selection-color: #FFFFFF;
            }
            QLineEdit#StringInput:focus {
                border: 1px solid #39DFA1;
                background-color: #0C171B;
            }

            QLabel#StatusLabel {
                color: #8290A4;
                font-family: 'Consolas', monospace;
                font-size: 15px;
                font-weight: bold;
            }

            QPushButton#UpdateButton {
                background-color: #0078D7;
                color: #FFFFFF;
                border: 1px solid #005A9E;
                border-bottom: 4px solid #003B66;
                border-radius: 8px;
                font-family: 'Segoe UI', sans-serif;
                font-weight: 900;
                font-size: 16px;
                letter-spacing: 1.5px;
            }
            QPushButton#UpdateButton:hover {
                background-color: #1084D0;
                border-color: #0078D7;
                border-bottom: 4px solid #005A9E;
            }
            QPushButton#UpdateButton:pressed {
                background-color: #005A9E;
                border-bottom: 1px solid #003B66;
                padding-top: 3px;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 20, 22, 22)
        layout.setSpacing(22)

        # Top stretch for vertical centering
        layout.addStretch(1)

        panel_frame = QFrame()
        panel_frame.setObjectName("PanelFrame")
        panel_layout = QVBoxLayout(panel_frame)
        panel_layout.setContentsMargins(22, 22, 22, 22)
        panel_layout.setSpacing(20)

        # --- Target Input Port Selector ---
        port_layout = QHBoxLayout()
        lbl_port = QLabel("TARGET INPUT PORT:")
        lbl_port.setObjectName("TagLabel")
        
        self.combo_target = QComboBox()
        self.combo_target.setObjectName("PortCombo")
        self.combo_target.setMinimumWidth(220)
        self.combo_target.setFixedHeight(46)
        self.combo_target.setMaxVisibleItems(15)
        
        port_layout.addWidget(lbl_port)
        port_layout.addStretch()
        port_layout.addWidget(self.combo_target)
        panel_layout.addLayout(port_layout)

        # --- ASCII String Input Field ---
        lbl_input = QLabel("ASCII PAYLOAD INPUT (UP TO 16 CHARACTERS):")
        lbl_input.setObjectName("TagLabel")
        panel_layout.addWidget(lbl_input)

        self.txt_input = QLineEdit()
        self.txt_input.setObjectName("StringInput")
        self.txt_input.setPlaceholderText("Type string here (e.g. HELLO)...")
        self.txt_input.setMaxLength(16)
        self.txt_input.setFixedHeight(68)
        self.txt_input.textChanged.connect(self.update_status)
        panel_layout.addWidget(self.txt_input)

        # --- Live Byte & Bit Width Indicator ---
        self.lbl_status = QLabel("0 / 16 Characters  |  0 Bits  (Packed: 0x00)")
        self.lbl_status.setObjectName("StatusLabel")
        self.lbl_status.setAlignment(Qt.AlignCenter)
        panel_layout.addWidget(self.lbl_status)

        panel_layout.addSpacing(10)

        # --- UPDATE / BLAST BUTTON ---
        self.btn_update = QPushButton("UPDATE STRING REGISTER")
        self.btn_update.setObjectName("UpdateButton")
        self.btn_update.setFixedHeight(56)
        self.btn_update.setCursor(Qt.PointingHandCursor)
        self.btn_update.clicked.connect(self.emit_string_data)
        panel_layout.addWidget(self.btn_update)

        layout.addWidget(panel_frame)

        # Bottom stretch for vertical centering
        layout.addStretch(1)

    def set_available_inputs(self, inputs_list):
        """Populates detected input ports from main.py's Verilog parser."""
        self.available_inputs = inputs_list
        self.combo_target.clear()
        if inputs_list:
            self.combo_target.addItems(inputs_list)
            # Auto-select string_in or str_in if available
            for idx, item in enumerate(inputs_list):
                if 'str' in item.lower() or 'string' in item.lower():
                    self.combo_target.setCurrentIndex(idx)
                    break
        else:
            self.combo_target.addItem("string_in")

    def update_status(self, text):
        """Calculates live ASCII byte counts and packed bit widths."""
        char_count = len(text)
        bit_count = char_count * 8
        
        # Convert ASCII string to big-endian packed integer
        packed_val = 0
        for char in text:
            packed_val = (packed_val << 8) | ord(char)

        self.lbl_status.setText(
            f"{char_count} / 16 Characters  |  {bit_count} Bits  (Packed: 0x{packed_val:X})"
        )

    def emit_string_data(self):
        """Packs ASCII payload into a numeric integer and sends it to sim_engine."""
        target_port = self.combo_target.currentText()
        raw_text = self.txt_input.text()

        if not target_port or target_port == "None":
            QMessageBox.warning(self, "Target Warning", "Please select a valid target input port!")
            return

        packed_val = 0
        for char in raw_text:
            packed_val = (packed_val << 8) | ord(char)

        self.string_updated.emit(target_port, packed_val)

    def show_help(self):
        msg = QMessageBox()
        msg.setWindowTitle("Learner Guide: ASCII String Input Injector")
        msg.setText(
            "<b>ASCII String Input Injector</b><br><br>"
            "This interface converts plain text typed on your keyboard into packed ASCII bitvectors for Verilog simulation.<br><br>"
            "<b>How It Works:</b><br>"
            "• Select the target input port from the dropdown menu.<br>"
            "• Type any combination of standard ASCII characters (up to 16) into the payload box.<br>"
            "• Each character is converted into an 8-bit ASCII byte.<br>"
            "• Clicking <b>UPDATE STRING REGISTER</b> packs all characters into a wide bitvector bus and sends it to the target Verilog input pin.<br><br>"
            "<b>Example Verilog Bus Declaration:</b><br>"
            "<code>input wire [127:0] string_in</code> (Holds up to 16 ASCII characters)"
        )
        msg.exec_()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    test_window = QWidget()
    test_window.setStyleSheet("background-color: #10141B;")
    layout = QVBoxLayout(test_window)
    module = StringInputView()
    layout.addWidget(module)
    test_window.setWindowTitle("Test: String Input Interface")
    test_window.resize(700, 500)
    test_window.show()
    sys.exit(app.exec_())