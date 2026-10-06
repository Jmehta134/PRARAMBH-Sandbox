import sys
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
    QTextEdit, QLabel, QCheckBox, QFileDialog, QApplication, QFrame, QMessageBox
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QTextCursor

class ConsoleLogView(QWidget):
    """An industrial IDE terminal / system log viewer for Verilog simulation feedback."""
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(12)
        
        # Professional Header Label (Matching other modules)
        title = QLabel("SYSTEM CONSOLE & SIMULATION LOG")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("""
            font-weight: 900; 
            color: #333333; 
            font-size: 18px; 
            letter-spacing: 1.5px;
            margin-bottom: 5px;
        """)
        layout.addWidget(title)
        
        # Terminal Container Frame
        terminal_frame = QFrame()
        terminal_frame.setStyleSheet("""
            QFrame {
                background-color: #1E1E1E;
                border: 2px solid #CCCCCC;
                border-radius: 8px;
            }
        """)
        term_layout = QVBoxLayout(terminal_frame)
        term_layout.setContentsMargins(10, 10, 10, 10)
        term_layout.setSpacing(8)
        
        # Console Text Area (Monospace, read-only terminal look)
        self.console_box = QTextEdit()
        self.console_box.setReadOnly(True)
        self.console_box.setFont(QFont("Consolas", 11))
        self.console_box.setStyleSheet("""
            QTextEdit {
                background-color: #141414;
                color: #D4D4D4;
                border: 1px solid #333333;
                border-radius: 4px;
                padding: 8px;
            }
        """)
        term_layout.addWidget(self.console_box)
        
        # Toolbar Controls inside the terminal panel
        control_layout = QHBoxLayout()
        
        self.auto_scroll_cb = QCheckBox("Auto-scroll")
        self.auto_scroll_cb.setChecked(True)
        self.auto_scroll_cb.setStyleSheet("color: #AAAAAA; font-size: 12px; font-weight: bold;")
        
        self.btn_clear = QPushButton("Clear Console")
        self.btn_clear.setFixedSize(110, 30)
        self.btn_clear.setStyleSheet("""
            QPushButton {
                background-color: #2D2D30;
                color: #CCCCCC;
                border: 1px solid #555555;
                border-radius: 4px;
                font-weight: bold;
                font-size: 11px;
            }
            QPushButton:hover { background-color: #3E3E42; color: white; border-color: #0078D7; }
        """)
        self.btn_clear.clicked.connect(self.clear_console)
        
        self.btn_save = QPushButton("Save Log...")
        self.btn_save.setFixedSize(100, 30)
        self.btn_save.setStyleSheet(self.btn_clear.styleSheet())
        self.btn_save.clicked.connect(self.save_log)
        
        control_layout.addWidget(self.auto_scroll_cb)
        control_layout.addStretch()
        control_layout.addWidget(self.btn_clear)
        control_layout.addWidget(self.btn_save)
        
        term_layout.addLayout(control_layout)
        layout.addWidget(terminal_frame)
        
        # Initial boot message
        self.log_message("SYSTEM INITIALIZED", "INFO")
        self.log_message("µP PRARAMBH Unified Sandbox Environment Ready.", "SUCCESS")

    def log_message(self, message, level="INFO"):
        """Public API to push messages into the console with color-coded levels."""
        colors = {
            "INFO": "#00E5FF",      # Cyan
            "SUCCESS": "#00FF00",   # Neon Green
            "WARN": "#FFA500",      # Orange
            "ERROR": "#FF4444"      # Red
        }
        color = colors.get(level.upper(), "#D4D4D4")
        
        formatted_html = f'<span style="color: #666666;">[8:23 PM]</span> <span style="color: {color}; font-weight: bold;">[{level.upper()}]</span> <span style="color: #E0E0E0;">{message}</span>'
        self.console_box.append(formatted_html)
        
        if self.auto_scroll_cb.isChecked():
            self.console_box.moveCursor(QTextCursor.End)

    def clear_console(self):
        self.console_box.clear()
        self.log_message("Console cleared by user.", "INFO")

    def save_log(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Save Simulation Log", "", "Text Files (*.txt);;All Files (*)")
        if file_path:
            try:
                with open(file_path, 'w') as f:
                    f.write(self.console_box.toPlainText())
                self.log_message(f"Log successfully saved to {file_path}", "SUCCESS")
            except Exception as e:
                self.log_message(f"Failed to save log: {str(e)}", "ERROR")

    def show_help(self):
        msg = QMessageBox(self)
        msg.setWindowTitle("Learner Guide: System Console & Simulation Log")
        msg.setText(
            "<b>System Console & Simulation Log</b><br><br>"
            "This view acts as your Tcl/System terminal, capturing all simulation feedback, compilation messages, and custom Verilog display statements.<br><br>"
            "<b>Logged Signal Types:</b><br>"
            "• <code>[INFO]</code> : System status updates (e.g., clock mode toggles).<br>"
            "• <code>[SUCCESS]</code> : Successful Icarus Verilog compilation and testbench binding.<br>"
            "• <code>[ERROR]</code> : Syntax errors, missing files, or compilation failures.<br>"
            "• <code>[Verilog]</code> : Raw output generated by any <code>$display</code> or <code>$monitor</code> statements in your Verilog code.<br><br>"
            "<b>Interactive Features:</b><br>"
            "• <b>Auto-scroll:</b> Automatically jumps to the newest log entries.<br>"
            "• <b>Clear Console:</b> Flushes the active text buffer.<br>"
            "• <b>Save Log:</b> Exports the current session output to a <code>.txt</code> file."
        )
        msg.exec_()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    test_window = QWidget()
    test_window.setStyleSheet("background-color: #FAFAFA;")
    layout = QVBoxLayout(test_window)
    module = ConsoleLogView()
    layout.addWidget(module)
    test_window.setWindowTitle("Module Test: Console Log")
    test_window.resize(700, 500)
    test_window.show()
    sys.exit(app.exec_())