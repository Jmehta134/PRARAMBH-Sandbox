import sys
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QComboBox, QLCDNumber, QLabel, QFrame, QMessageBox, QApplication
from PyQt5.QtCore import Qt

class RegisterRow(QFrame):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("RegisterRow { background-color: #E6E6E6; border: 1px solid #C0C0C0; border-radius: 6px; }")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(20)
        
        self.combo = QComboBox()
        self.combo.addItem("-- Empty --")
        self.combo.setMinimumWidth(200)
        self.combo.setFixedHeight(35)
        self.combo.setStyleSheet("""
            QComboBox { font-size: 13px; font-weight: bold; color: #333333; background-color: #FFFFFF; border: 1px solid #AAAAAA; border-radius: 4px; padding-left: 10px; }
        """)
        
        self.lcd = QLCDNumber(4)
        self.lcd.setHexMode()
        self.lcd.setFixedHeight(45)
        self.lcd.setStyleSheet("QLCDNumber { background-color: #1E1E1E; color: #00FF00; border: 2px inset #555555; border-radius: 4px; }")
        self.lcd.display("0000")
        
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
        layout.setContentsMargins(15, 20, 15, 15)
        
        title = QLabel("DYNAMIC REGISTER PROBE")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-weight: 900; color: #333333; font-size: 18px; letter-spacing: 2px; margin-bottom: 10px;")
        layout.addWidget(title)
        
        self.rows = [RegisterRow() for _ in range(6)]
        for row in self.rows:
            layout.addWidget(row)
        layout.addStretch()

    def set_available_signals(self, internals):
        """Populates all dropdowns with the internal signals found in the Verilog code."""
        # FIXED: Removed the ugly 'dut.' prefix!
        for row in self.rows:
            row.update_options(internals)

    def sync_data(self, state_dict):
        """Reads the currently selected signal in the dropdown and looks it up in the live data."""
        for row in self.rows:
            selected_sig = row.combo.currentText()
            if selected_sig in state_dict:
                row.lcd.display(f"{state_dict[selected_sig]:04X}")
            else:
                row.lcd.display("0000")

    def show_help(self):
        msg = QMessageBox(self)
        msg.setWindowTitle("Learner Guide: Dynamic Register Probe")
        msg.setText(
            "<b>Dynamic Register Probe Mapping</b><br><br>"
            "Unlike fixed I/O ports, this tool uses AST introspection to scan your entire Verilog module for internal registers.<br><br>"
            "<b>Monitored Signals:</b><br>"
            "• Any internal <code>reg</code>, <code>wire</code>, or <code>integer</code> declared in your active file.<br><br>"
            "<b>How it works:</b><br>"
            "Select any signal from the dropdown menu (e.g., <code>dut.counter</code> or <code>dut.state</code>) "
            "to read its raw Hex value from the simulation engine on every clock pulse."
        )
        msg.exec_()