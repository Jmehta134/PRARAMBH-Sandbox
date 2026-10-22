import os
import sys
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QFileDialog, QMessageBox, 
    QShortcut, QFrame, QLabel
)
from PyQt5.QtCore import Qt, QUrl, pyqtSignal
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtGui import QKeySequence, QDesktopServices

from verilog_parser import verilog_to_blockly_xml

def get_absolute_path(relative_path):
    """Safely resolve paths whether running from Python or compiled PyInstaller."""
    if hasattr(sys, '_MEIPASS'):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    return os.path.normpath(os.path.join(base_path, relative_path))

class VisualBlockBuilder(QWidget):
    file_changed = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)

        self.current_file_path = None

        # --- DARK GREY TOP ACTION BAR ---
        top_bar = QFrame()
        top_bar.setObjectName("HeaderFrame")
        top_bar.setFixedHeight(70) 
        
        bar_layout = QHBoxLayout(top_bar)
        bar_layout.setContentsMargins(15, 10, 15, 10)
        bar_layout.setSpacing(10)

        # Standardized Dark Grey Button Theme
        btn_style = """
            QPushButton {
                background-color: #3E3E42;
                color: #E0E0E0;
                border: 1px solid #555555;
                border-radius: 4px;
                font-family: 'Segoe UI', Arial, sans-serif;
                font-weight: bold;
                font-size: 16px;
                padding: 0px 15px;
            }
            QPushButton:hover {
                background-color: #4E4E52;
                border: 1px solid #00E5FF;
                color: #00E5FF;
            }
            QPushButton:pressed {
                background-color: #1E1E1E;
            }
        """

        btn_new = QPushButton("New")
        btn_new.setFixedSize(85, 35)
        btn_new.setCursor(Qt.PointingHandCursor)
        btn_new.setStyleSheet(btn_style)
        btn_new.clicked.connect(self.new_file)

        btn_open = QPushButton("Open")
        btn_open.setFixedSize(85, 35)
        btn_open.setCursor(Qt.PointingHandCursor)
        btn_open.setStyleSheet(btn_style)
        btn_open.clicked.connect(self.open_file)

        btn_import = QPushButton("Import")
        btn_import.setFixedSize(140, 35)
        btn_import.setCursor(Qt.PointingHandCursor)
        btn_import.setStyleSheet(btn_style)
        btn_import.clicked.connect(self.import_file)

        separator = QFrame()
        separator.setFrameShape(QFrame.VLine)
        separator.setFrameShadow(QFrame.Plain)
        separator.setLineWidth(2)
        separator.setFixedHeight(26)
        separator.setStyleSheet("background-color: #555555; border: none;")

        # Primary action gets a slight blue tint in dark mode
        btn_save = QPushButton("Save")
        btn_save.setFixedSize(110, 35)
        btn_save.setCursor(Qt.PointingHandCursor)
        btn_save.setStyleSheet(btn_style.replace("#3E3E42", "#005A9E").replace("#E0E0E0", "#FFFFFF"))
        btn_save.clicked.connect(self.save_file)

        btn_save_as = QPushButton("Save As")
        btn_save_as.setFixedSize(110, 35)
        btn_save_as.setCursor(Qt.PointingHandCursor)
        btn_save_as.setStyleSheet(btn_style)
        btn_save_as.clicked.connect(self.save_file_as)

        self.lbl_filename = QLabel("[ Unsaved Workspace ]")
        self.lbl_filename.setStyleSheet("color: #888888; font-family: monospace; font-weight: bold;")

        btn_help = QPushButton("?  (Help)")
        btn_help.setFixedSize(110, 35)
        btn_help.setCursor(Qt.PointingHandCursor)
        btn_help.setToolTip("Open Online Documentation & User Guide")
        btn_help.setStyleSheet(btn_style)
        btn_help.clicked.connect(self.open_help_webpage)

        bar_layout.addWidget(btn_new)
        bar_layout.addWidget(btn_open)
        bar_layout.addWidget(btn_import)
        bar_layout.addSpacing(6)
        bar_layout.addWidget(separator)
        bar_layout.addSpacing(6)
        bar_layout.addWidget(btn_save)
        bar_layout.addWidget(btn_save_as)
        bar_layout.addSpacing(15)
        bar_layout.addWidget(self.lbl_filename)
        
        bar_layout.addStretch(1)
        bar_layout.addWidget(btn_help)

        self.layout.addWidget(top_bar)

        self.web_view = QWebEngineView()
        html_path = get_absolute_path(os.path.join("assets", "blockly", "index.html"))
        self.web_view.load(QUrl.fromLocalFile(html_path))
        self.web_view.page().setBackgroundColor(Qt.transparent)

        self.layout.addWidget(self.web_view, 1)

        QShortcut(QKeySequence("Ctrl+N"), self).activated.connect(self.new_file)
        QShortcut(QKeySequence("Ctrl+O"), self).activated.connect(self.open_file)
        QShortcut(QKeySequence("Ctrl+I"), self).activated.connect(self.import_file)
        QShortcut(QKeySequence("Ctrl+S"), self).activated.connect(self.save_file)
        QShortcut(QKeySequence("Ctrl+Shift+S"), self).activated.connect(self.save_file_as)

    def set_current_file(self, path, emit_signal=True):
        self.current_file_path = path
        if path:
            filename = os.path.basename(path)
            self.lbl_filename.setText(f"Editing: {filename}")
            self.lbl_filename.setStyleSheet("color: #1c1c1c; font-family: monospace; font-weight: bold;")
            if emit_signal:
                self.file_changed.emit(path)
        else:
            self.lbl_filename.setText("[ Unsaved Workspace ]")
            self.lbl_filename.setStyleSheet("color: #888888; font-family: monospace; font-weight: bold;")

    def load_external_file(self, path):
        if not path or not os.path.exists(path): return
        if path == self.current_file_path: return

        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()

        xml_data = verilog_to_blockly_xml(content) if path.endswith('.v') else content
        escaped_xml = xml_data.replace('\\', '\\\\').replace('`', '\\`')
        self.web_view.page().runJavaScript(f"window.importWorkspace(`{escaped_xml}`);")
        self.set_current_file(path, emit_signal=False)

    def new_file(self):
        self.set_current_file(None)
        self.web_view.page().runJavaScript("window.importWorkspace('');")

    def open_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Open Hardware Description", "", "Supported Files (*.xml *.v);;Blockly XML (*.xml);;Verilog Source (*.v)"
        )
        if path and os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()

            xml_data = verilog_to_blockly_xml(content) if path.endswith('.v') else content
            escaped_xml = xml_data.replace('\\', '\\\\').replace('`', '\\`')
            self.web_view.page().runJavaScript(f"window.importWorkspace(`{escaped_xml}`);")
            
            # Only set as current file if it didn't fail parsing
            if not xml_data.startswith("PARSE_ERROR:"):
                self.set_current_file(path)
            else:
                print(f"[Backend] {xml_data}")

    def import_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Import Hardware Description", "", "Supported Files (*.xml *.v);;Blockly XML (*.xml);;Verilog Source (*.v)"
        )
        if path and os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()

            xml_data = verilog_to_blockly_xml(content) if path.endswith('.v') else content
            escaped_xml = xml_data.replace('\\', '\\\\').replace('`', '\\`')
            self.web_view.page().runJavaScript(f"window.appendWorkspace(`{escaped_xml}`);")
            
            if xml_data.startswith("PARSE_ERROR:"):
                print(f"[Backend] {xml_data}")

    def save_file(self):
        if self.current_file_path:
            self._execute_save(self.current_file_path)
            self.set_current_file(self.current_file_path)
        else:
            self.save_file_as()

    def save_file_as(self):
        path, selected_filter = QFileDialog.getSaveFileName(
            self, "Save Hardware Description As", "", "Verilog Source (*.v);;Blockly XML (*.xml)"
        )
        if not path:
            return

        if "Verilog" in selected_filter and not path.endswith('.v'): path += '.v'
        elif "Blockly" in selected_filter and not path.endswith('.xml'): path += '.xml'

        self._execute_save(path)
        self.set_current_file(path)

    def _execute_save(self, path):
        if path.endswith('.v'):
            self.web_view.page().runJavaScript("window.generatedVerilog || '';", lambda content: self._write_to_file(path, content))
        else:
            self.web_view.page().runJavaScript("window.exportWorkspace();", lambda content: self._write_to_file(path, content))

    def _write_to_file(self, file_path, content):
        if not content:
            if file_path.endswith('.xml'):
                content = '<xml xmlns="https://developers.google.com/blockly/xml"></xml>'
            else:
                QMessageBox.warning(self, "Empty Canvas", "No hardware logic generated to save.")
                return
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
        except Exception as e:
            QMessageBox.critical(self, "Save Error", f"Failed to save file:\n{str(e)}")

    def open_help_webpage(self):
        url = QUrl("https://github.com")
        QDesktopServices.openUrl(url)