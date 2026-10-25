import sys
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QComboBox, QLCDNumber, QLabel, QFrame, QMessageBox, QApplication
from PyQt5.QtCore import Qt

class RegisterRow(QFrame):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("RegisterRow { background-color: #E6E6E6; border: 1px solid #C0C0C0; border-radius: 6px; }")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(20)
        
        self.combo = QComboBox()
        self.combo.addItem("-- Empty --")
        self.combo.setMinimumWidth(200)
        self.combo.setFixedHeight(35)
        self.combo.setStyleSheet("""
            QComboBox { font-size: 13px; font-weight: bold; color: #333333; background-color: #FFFFFF; border: 1px solid #AAAAAA; border-radius: 4px; padding-left: 10px; }
        """)
        
        self.lcd = QLCDNumber(8)
        self.lcd.setHexMode()
        self.lcd.setFixedHeight(45)
        self.lcd.setStyleSheet("QLCDNumber { background-color: #1E1E1E; color: #00FF00; border: 2px inset #555555; border-radius: 4px; }")
        self.lcd.display("")
        
        layout.addWidget(self.combo)
        layout.addWidget(self.lcd, stretch=1)

    def update_options(self, signals):
        self.combo.clear()
        self.combo.addItem("-- Select Target --")
        self.combo.addItems(signals)

class RegisterMonitorView(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(8, 8, 8, 8)
        
        self.rows = [RegisterRow() for _ in range(6)]
        for row in self.rows:
            layout.addWidget(row)
        layout.addStretch()

    def set_available_signals(self, signals_list):
        """Populates all dropdowns with the input, output, wire, and reg signals found in the Verilog code."""
        for row in self.rows:
            row.update_options(signals_list)

    def sync_data(self, state_dict):
        """Reads the currently selected signal in the dropdown and looks it up in the live data."""
        for row in self.rows:
            selected_sig = row.combo.currentText()
            if selected_sig in state_dict:
                val = int(state_dict[selected_sig]) & 0xFFFFFFFF
                row.lcd.display(f"{val:X}")
            else:
                row.lcd.display("")

    def show_help(self):
        msg = QMessageBox(self)
        msg.setWindowTitle("Learner Guide: Dynamic Signal Probe")
        msg.setText(
            "<b>Dynamic Signal Probe Mapping</b><br><br>"
            "This tool uses AST introspection to scan your entire Verilog module for signal declarations.<br><br>"
            "<b>Monitored Signals:</b><br>"
            "• Any <code>input</code>, <code>output</code>, <code>reg</code>, <code>wire</code>, or <code>integer</code> declared in your active file.<br><br>"
            "<b>How it works:</b><br>"
            "Select any signal from the dropdown menu to read its raw Hex value from the simulation engine on every clock pulse. Data automatically scales up to 32 bits."
        )
        msg.exec_()