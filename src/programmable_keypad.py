from PyQt5.QtWidgets import (QWidget, QGridLayout, QPushButton, QInputDialog, QMessageBox, QVBoxLayout, QLabel, QFrame, QApplication, QComboBox, QDialog, QDialogButtonBox, QFormLayout)
from PyQt5.QtCore import Qt, pyqtSignal

class KeyConfigDialog(QDialog):
    def __init__(self, current_label, current_hex, available_inputs, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configure Macro Key")
        layout = QFormLayout(self)
        
        import PyQt5.QtWidgets as qtw
        self.label_edit = qtw.QLineEdit(current_label)
        self.hex_edit = qtw.QLineEdit(f"{current_hex:02X}")
        self.target_combo = QComboBox()
        self.target_combo.addItems(available_inputs if available_inputs else ["None"])
        
        layout.addRow("Macro Label:", self.label_edit)
        layout.addRow("Inject Hex Value:", self.hex_edit)
        layout.addRow("Target Input Port:", self.target_combo)
        
        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        layout.addRow(btns)

class MechanicalKey(QPushButton):
    key_pressed = pyqtSignal(str, int) # Now emits (Target_Port, Value)

    def __init__(self, idx, parent_view):
        super().__init__()
        self.parent_view = parent_view
        self.label_text = f"CMD_{idx:X}"
        # Set default value dynamically based on 1-based index (0x01 to 0x10)
        self.hex_val = idx + 1
        self.target_port = "None"
        
        self.setFixedSize(105, 105)
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet("""
            QPushButton { background-color: #EFEFEF; border: 2px solid #ADADAD; border-bottom: 5px solid #777777; border-radius: 8px; font-weight: bold; color: #222222; font-size: 13px; }
            QPushButton:hover { background-color: #E1F0FA; border: 2px solid #0078D7; border-bottom: 5px solid #005A9E; }
            QPushButton:pressed { background-color: #CCE4F7; border: 2px solid #005A9E; border-bottom: 2px solid #005A9E; padding-top: 5px; }
        """)
        self.update_display()
        self.clicked.connect(self.on_click)

    def update_display(self):
        self.setText(f"{self.label_text}\n[{self.target_port}]\n[0x{self.hex_val:02X}]")

    def on_click(self):
        if self.target_port != "None":
            self.key_pressed.emit(self.target_port, self.hex_val)

    def mousePressEvent(self, event):
        if event.button() == Qt.RightButton:
            self.open_config_dialog()
        else:
            super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.open_config_dialog()
        else:
            super().mouseDoubleClickEvent(event)

    def open_config_dialog(self):
        """Helper method to launch the key configuration dialog."""
        dlg = KeyConfigDialog(self.label_text, self.hex_val, self.parent_view.available_inputs, self)
        if dlg.exec_():
            try:
                self.hex_val = int(dlg.hex_edit.text(), 16)
                self.label_text = dlg.label_edit.text()
                self.target_port = dlg.target_combo.currentText()
                self.update_display()
            except ValueError:
                QMessageBox.warning(self, "Error", "Invalid Hexadecimal!")

class ProgrammableKeypadView(QWidget):
    keypad_triggered = pyqtSignal(str, int) # Relays up to main

    def __init__(self):
        super().__init__()
        self.available_inputs = []
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        
        title = QLabel("PROGRAMMABLE MACRO KEYPAD")
        subtitle = QLabel("Right-click any key to map it to a specific Verilog input port")
        title.setAlignment(Qt.AlignCenter)
        subtitle.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-weight: 900; color: #333333; font-size: 18px; letter-spacing: 1.5px;")
        subtitle.setStyleSheet("color: #666666; font-size: 12px; font-style: italic; margin-bottom: 10px;")
        layout.addWidget(title)
        layout.addWidget(subtitle)
        
        frame = QFrame()
        frame.setStyleSheet("QFrame { background-color: #E5E5E5; border: 2px solid #CCCCCC; border-radius: 10px; }")
        grid = QGridLayout(frame)
        grid.setSpacing(14)
        
        self.keys = []
        for i in range(16):
            btn = MechanicalKey(i, self)
            btn.key_pressed.connect(self.keypad_triggered.emit)
            grid.addWidget(btn, i//4, i%4)
            self.keys.append(btn)
            
        layout.addWidget(frame, alignment=Qt.AlignCenter)
        layout.addStretch()

    def set_available_inputs(self, inputs_list):
        self.available_inputs = inputs_list

    def show_help(self):
        msg = QMessageBox(self)
        msg.setWindowTitle("Learner Guide: Programmable Keypad")
        msg.setText(
            "<b>Programmable Macro Keypad Mapping</b><br><br>"
            "This keypad dynamically detects all <code>input</code> ports declared in your Verilog top module.<br><br>"
            "<b>How to Map a Keycap:</b><br>"
            "1. Right-click any keycap.<br>"
            "2. Select any detected input port string (e.g., <code>opcode</code>, <code>enable</code>, or <code>port_a</code>).<br>"
            "3. Enter the Hex value you want to blast to that input port.<br>"
            "4. Left-click the key to transmit the value live to the simulation!"
        )
        msg.exec_()