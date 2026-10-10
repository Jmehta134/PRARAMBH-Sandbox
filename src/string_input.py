import sys
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, 
    QLineEdit, QPushButton, QComboBox, QMessageBox, QApplication
)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt, pyqtSignal

# =============================================================================
# MAIN PANE: Dynamic ASCII String Input Interface (Expanded Workspace)
# =============================================================================
class StringInputView(QWidget):
    """
    Industrial ASCII String Injector Interface.
    Packs up to 16 ASCII characters into a wide Verilog input bus or string register.
    Designed to fill the full width and height of the split workspace pane.
    """
    # Emits (target_port_name, integer_packed_value)
    string_updated = pyqtSignal(str, object)

    def __init__(self):
        super().__init__()
        self.available_inputs = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # --- Pane Header ---
        title = QLabel("STRING & ASCII INPUT INJECTOR")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("""
            font-weight: 900; 
            color: #333333; 
            font-size: 18px; 
            letter-spacing: 1.5px;
            margin-bottom: 2px;
        """)
        
        subtitle = QLabel("Inject raw ASCII strings directly into Verilog input buses")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("color: #666666; font-size: 12px; font-style: italic; margin-bottom: 4px;")
        
        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.setSpacing(30)

        # --- Expanded Kakkoii Frame Panel ---
        panel_frame = QFrame()
        panel_frame.setStyleSheet("""
            QFrame {
                background-color: #1E1E1E;
                border: 2px solid #CCCCCC;
                border-radius: 10px;
            }
        """)
        panel_layout = QVBoxLayout(panel_frame)
        panel_layout.setContentsMargins(25, 25, 25, 25)
        panel_layout.setSpacing(20)

        # --- Target Input Port Selector ---
        port_layout = QHBoxLayout()
        lbl_port = QLabel("TARGET INPUT PORT:")
        lbl_port.setStyleSheet("""
            font-weight: 900; 
            color: #00E5FF; 
            font-size: 13px; 
            letter-spacing: 1px; 
            border: none; 
            background: transparent;
        """)
        
        self.combo_target = QComboBox()
        self.combo_target.setMinimumWidth(220)
        self.combo_target.setFixedHeight(38)
        self.combo_target.setStyleSheet("""
            QComboBox {
                background-color: #2D2D30;
                color: #00FFCC;
                border: 1px solid #555555;
                padding: 6px 12px;
                border-radius: 4px;
                font-weight: bold;
                font-size: 13px;
                font-family: monospace;
            }
            QComboBox::drop-down { border: none; }
        """)
        
        port_layout.addWidget(lbl_port)
        port_layout.addStretch()
        port_layout.addWidget(self.combo_target)
        panel_layout.addLayout(port_layout)

        # --- ASCII String Input Field ---
        lbl_input = QLabel("ASCII PAYLOAD INPUT (UP TO 16 CHARACTERS):")
        lbl_input.setStyleSheet("""
            font-weight: 900; 
            color: #AAAAAA; 
            font-size: 12px; 
            letter-spacing: 1px; 
            border: none; 
            background: transparent;
        """)
        panel_layout.addWidget(lbl_input)

        self.txt_input = QLineEdit()
        self.txt_input.setPlaceholderText("Type string here (e.g. HELLO)...")
        self.txt_input.setMaxLength(16)
        self.txt_input.setFixedHeight(55)
        self.txt_input.setFont(QFont("Consolas", 18, QFont.Bold))
        self.txt_input.setStyleSheet("""
            QLineEdit {
                background-color: #101010;
                color: #00FFCC;
                border: 2px solid #333333;
                border-radius: 6px;
                padding: 10px 15px;
                selection-background-color: #0078D7;
            }
            QLineEdit:focus {
                border: 2px solid #00E5FF;
            }
        """)
        self.txt_input.textChanged.connect(self.update_status)
        panel_layout.addWidget(self.txt_input)

        # --- Live Byte & Bit Width Indicator ---
        self.lbl_status = QLabel("0 / 16 Characters  |  0 Bits (Packed Hex: 0x00)")
        self.lbl_status.setAlignment(Qt.AlignCenter)
        self.lbl_status.setStyleSheet("""
            color: #888888; 
            font-family: monospace; 
            font-size: 12px; 
            font-weight: bold;
            border: none; 
            background: transparent;
        """)
        panel_layout.addWidget(self.lbl_status)

        panel_layout.addSpacing(10)

        # --- Expanded Kakkoii UPDATE / BLAST BUTTON ---
        self.btn_update = QPushButton("UPDATE STRING REGISTER")
        self.btn_update.setFixedHeight(55)
        self.btn_update.setCursor(Qt.PointingHandCursor)
        self.btn_update.setStyleSheet("""
            QPushButton {
                background-color: #0078D7;
                color: #FFFFFF;
                border: 2px solid #005A9E;
                border-bottom: 5px solid #003B66;
                border-radius: 6px;
                font-weight: 900;
                font-size: 14px;
                letter-spacing: 1.5px;
            }
            QPushButton:hover {
                background-color: #1084D0;
                border-color: #0078D7;
                border-bottom: 5px solid #005A9E;
            }
            QPushButton:pressed {
                background-color: #005A9E;
                border-bottom: 2px solid #003B66;
                padding-top: 3px;
            }
        """)
        self.btn_update.clicked.connect(self.emit_string_data)
        panel_layout.addWidget(self.btn_update)

        # Allow panel to consume full pane width
        layout.addWidget(panel_frame)
        layout.addStretch()

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
        msg = QMessageBox(self)
        msg.setWindowTitle("Learner Guide: ASCII String Input Injector")
        msg.setText(
            "<b>ASCII String Input Injector</b><br><br>"
            "This interface converts plain text typed on your keyboard into packed ASCII bitvectors for Verilog simulation.<br><br>"
            "<b>How It Works:</b><br>"
            "• Type any combination of standard keyboard ASCII characters into the input box.<br>"
            "• Each character is converted to an 8-bit ASCII byte.<br>"
            "• Clicking <b>UPDATE STRING REGISTER</b> packs all characters into a wide bitvector bus and blasts it to your target input pin.<br><br>"
            "<b>Example Verilog Port:</b><br>"
            "<code>input wire [127:0] string_in</code> (Can hold up to 16 ASCII characters!)"
        )
        msg.exec_()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    test_window = QWidget()
    test_window.setStyleSheet("background-color: #F0F0F0;")
    layout = QVBoxLayout(test_window)
    module = StringInputView()
    layout.addWidget(module)
    test_window.setWindowTitle("Test: String Input Interface")
    test_window.resize(700, 500)
    test_window.show()
    sys.exit(app.exec_())