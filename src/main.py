import sys
import os
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QSplitter, QComboBox, QPushButton, QLabel, QFileDialog, QStackedWidget,
    QFrame, QMessageBox, QDialog, QListWidget
)
from PyQt5.QtCore import Qt, QTimer, QUrl, QEvent, QRect
from PyQt5.QtGui import QFont, QIcon, QDesktopServices, QPainter, QColor, QPen

# Import all module views
from dip_hex_io import DipHexIOView
from pixel_matrix import PixelMatrixView
from char_display import CharDisplayView
from register_monitor import RegisterMonitorView
from programmable_keypad import ProgrammableKeypadView
from slider import SliderADCView
from gauge import GaugeADCView
from mouse_dir import MouseDirectionView
from string_input import StringInputView
from memory_region import MemoryRegionView
from block_builder import VisualBlockBuilder
from console_log import ConsoleLogView

# Import the Dynamic Simulation Backend Engine
from sim_engine import SimulationEngine

# 1. Resolve local iverilog binary path based on platform
base_dir = os.path.dirname(os.path.abspath(__file__))
if sys.platform.startswith('win'):
    local_bin = os.path.join(base_dir, "bin", "windows", "bin")
    iverilog_path = os.path.join(local_bin, "iverilog.exe")
else:
    local_bin = os.path.join(base_dir, "bin", "linux", "bin")
    iverilog_path = os.path.join(local_bin, "iverilog")

# 2. Add to PATH and set specific environment variables PyVerilog uses
if os.path.exists(local_bin) and local_bin not in os.environ["PATH"]:
    os.environ["PATH"] = local_bin + os.pathsep + os.environ["PATH"]

# Some versions of PyVerilog/iverilog look for explicit compiler flags or environment variables
os.environ["IVERILOG_PATH"] = iverilog_path

# =============================================================================
# GLOBAL STYLING (Professional Dark Grey Theme)
# =============================================================================
STYLE_SHEET = """
QMainWindow {
    background-color: #E8E8E8;
}
QWidget {
    color: #222222;
    font-family: 'Segoe UI', Arial, sans-serif;
}
QFrame#HeaderFrame {
    background-color: #F5F5F5;
    border-bottom: 1px solid #D0D0D0;
    border-radius: 0px;
}
QFrame#PaneFrame {
    background-color: #FFFFFF;
    border: 1px solid #D0D0D0;
    border-radius: 6px;
}
QPushButton {
    background-color: #E1E1E1;
    border: 1px solid #ADADAD;
    padding: 6px 12px;
    border-radius: 4px;
    font-weight: bold;
    color: #333333;
}
QPushButton:hover {
    background-color: #E5F1FB;
    border: 1px solid #0078D7;
    color: #0078D7;
}
QPushButton:pressed {
    background-color: #CCE4F7;
    border: 1px solid #005499;
}
/* Pane's help button */
QPushButton#HelpBtn {
    background-color: #EFEFEF;
    border: 2px solid #ADADAD;
    border-bottom: 3px solid #888888;
    border-radius: 13px;
    font-weight: 900;
    color: #555555;
    font-size: 14px;
    padding: 0px;
}
QPushButton#HelpBtn:hover {
    background-color: #E1F0FA;
    border: 2px solid #0078D7;
    border-bottom: 3px solid #005A9E;
    color: #0078D7;
}
QPushButton#HelpBtn:pressed {
    background-color: #CCE4F7;
    border-bottom: 1px solid #005A9E;
    margin-top: 2px;
}
QPushButton#FileBtn {
    background-color: #0078D7;
    color: white;
    border: 1px solid #005A9E;
}
QPushButton#FileBtn:hover {
    background-color: #1084D0;
}
/* Top help button*/
QPushButton#GlobalHelpBtn {
    background-color: #FADBD8;
    border: 3px solid #D98880;
    border-radius: 4px;
    font-weight: bold;
    font-size: 13px;
    color: #333333;
    padding: 4px 8px;
}
QPushButton#GlobalHelpBtn:hover {
    background-color: #F5B7B1;
    border: 3px solid #C0392B;
}
QPushButton#LeverBtn {
    background-color: #E1E1E1;
    border: 1px solid #ADADAD;
    color: #555555;
}
QPushButton#LeverBtn:checked {
    background-color: #0078D7;
    border: 1px solid #005A9E;
    color: white;
}
QComboBox {
    background-color: #FFFFFF;
    border: 1px solid #ADADAD;
    padding: 4px 8px;
    border-radius: 4px;
    color: #333333;
}
QComboBox:drop-down {
    border: none;
    border-left: 1px solid #ADADAD;
    width: 20px;
}
QComboBox:down-arrow {
    image: none;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 5px solid #333333;
    margin-top: 1px;
}
QComboBox QAbstractItemView {
    background-color: #FFFFFF;
    color: #333333;
    selection-background-color: #0078D7;
    selection-color: #FFFFFF;
    border: 1px solid #ADADAD;
}
QSplitter::handle {
    background-color: #CCCCCC;
    width: 4px;
}
QSplitter::handle:hover {
    background-color: #0078D7;
}
QPushButton#ExampleBtn {
    background-color: #E1E1E1;
    border: 1px solid #ADADAD;
    border-radius: 4px;
    font-weight: bold;
    color: #333333;
    padding: 4px 8px;
}
QPushButton#ExampleBtn:hover {
    background-color: #E5F1FB;
    border: 1px solid #0078D7;
    color: #0078D7;
}
/* Example Selector Dialog */
QDialog {
    background-color: #F0F0F0;
}
QLabel#DialogHeader {
    font-weight: bold;
    font-size: 15px;
    color: #333333;
}
QListWidget#ExampleList {
    background-color: #FFFFFF;
    border: 1px solid #ADADAD;
    border-radius: 6px;
    font-family: 'Consolas', 'Segoe UI', monospace;
    font-size: 15px;
    padding: 6px;
    color: #222222;
}
QListWidget#ExampleList::item {
    padding: 10px 14px;
    border-bottom: 1px solid #EAEAEA;
}
QListWidget#ExampleList::item:hover {
    background-color: #E5F1FB;
    color: #0078D7;
}
QListWidget#ExampleList::item:selected {
    background-color: #0078D7;
    color: #FFFFFF;
    font-weight: bold;
}
QPushButton#DialogCancelBtn {
    font-size: 14px;
    padding: 6px 16px;
}
QPushButton#DialogLoadBtn {
    background-color: #0078D7;
    color: white;
    border: 1px solid #005A9E;
    font-size: 14px;
    padding: 6px 18px;
}
QPushButton#DialogLoadBtn:hover {
    background-color: #1084D0;
}
/* Pane Title Header Dropdown */
QComboBox#PaneTitleDropdown {
    font-family: 'Segoe UI', sans-serif;
    font-weight: 900; 
    color: #333333; 
    font-size: 20px; 
    letter-spacing: 1.5px;
    background-color: #FFFFFF;
    border: 1px solid #CCCCCC;
    border-radius: 6px;
    padding: 6px 15px; 
}
QComboBox#PaneTitleDropdown:hover {
    border: 1px solid #0078D7;
    background-color: #E5F1FB; 
    color: #0078D7;
}
QComboBox#PaneTitleDropdown QAbstractItemView {
    background-color: #FFFFFF;
    color: #333333;
    font-size: 14px;
    font-weight: bold;
    selection-background-color: #0078D7;
    selection-color: #FFFFFF;
    border: 1px solid #ADADAD;
    border-radius: 4px;
    padding: 4px;
    outline: none;
}
"""

class TitleComboBox(QComboBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setEditable(True)
        self._popup_was_visible = False
        
        le = self.lineEdit()
        le.setReadOnly(True)
        le.setAlignment(Qt.AlignCenter)
        le.setCursor(Qt.PointingHandCursor)
        self.setCursor(Qt.PointingHandCursor)
        
        le.installEventFilter(self)

    def eventFilter(self, obj, event):
        if obj == self.lineEdit():
            if event.type() == QEvent.MouseButtonPress:
                self._popup_was_visible = self.view().isVisible()
                return True
            elif event.type() == QEvent.MouseButtonRelease:
                if event.button() == Qt.LeftButton:
                    if not self._popup_was_visible:
                        QTimer.singleShot(0, self.showPopup)
                    return True
        return super().eventFilter(obj, event)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._popup_was_visible = self.view().isVisible()
            return
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            if not self._popup_was_visible:
                QTimer.singleShot(0, self.showPopup)
            return
        super().mouseReleaseEvent(event)
    
class VerticalTabButton(QWidget):
    def __init__(self, text, index, parent_bar):
        super().__init__()
        self.text = text
        self.index = index
        self.parent_bar = parent_bar
        self.is_active = False
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedWidth(54) 

    def set_active(self, active):
        self.is_active = active
        self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.parent_bar.select_tab(self.index)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        if self.is_active:
            painter.fillRect(self.rect(), QColor("#FFFFFF")) # Active tab matches light panel
            text_color = QColor("#005A9E") 
        else:
            painter.fillRect(self.rect(), QColor("#D5D5D5")) # Light grey inactive tab background
            text_color = QColor("#555555") 
            painter.setPen(QPen(QColor("#B0B0B0"), 2)) # Border separator
            painter.drawLine(self.width()-1, 0, self.width()-1, self.height())

        painter.save()
        painter.translate(0, self.height())
        painter.rotate(-90)

        font = QFont("Consolas", 14, QFont.ExtraBold)
        painter.setFont(font)
        painter.setPen(text_color)
        
        text_rect = QRect(0, 0, self.height(), self.width())
        painter.drawText(text_rect, Qt.AlignCenter, self.text)
        painter.restore()

class VerticalTabBar(QWidget):
    def __init__(self, stacked_widget, parent=None):
        super().__init__(parent)
        self.stacked_widget = stacked_widget
        self.setFixedWidth(54)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Ensures the empty space below tabs matches the inactive tab color
        self.setStyleSheet("background-color: #D5D5D5;")

        self.btn_builder = VerticalTabButton("VISUAL BUILDER", 0, self)
        self.btn_sandbox = VerticalTabButton("HARDWARE SANDBOX", 1, self)

        self.btn_builder.setFixedHeight(240)
        self.btn_sandbox.setFixedHeight(240)

        layout.addWidget(self.btn_builder)
        layout.addWidget(self.btn_sandbox)
        layout.addStretch()

        self.buttons = [self.btn_builder, self.btn_sandbox]
        self.select_tab(0)

    def select_tab(self, index):
        self.stacked_widget.setCurrentIndex(index)
        for i, btn in enumerate(self.buttons):
            btn.set_active(i == index)

class ExampleSelectorDialog(QDialog):
    def __init__(self, example_dir, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select Verilog Example")
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.resize(460, 540)
        self.selected_file_path = None
        self.example_dir = example_dir

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)

        lbl = QLabel("Choose an example circuit:")
        lbl.setObjectName("DialogHeader")
        layout.addWidget(lbl)

        self.list_widget = QListWidget()
        self.list_widget.setObjectName("ExampleList")
        layout.addWidget(self.list_widget)

        btn_box = QHBoxLayout()
        
        btn_cancel = QPushButton("Cancel")
        btn_cancel.setObjectName("DialogCancelBtn")
        btn_cancel.setMinimumHeight(38)
        btn_cancel.clicked.connect(self.reject)

        self.btn_load = QPushButton("Load Example")
        self.btn_load.setObjectName("DialogLoadBtn")
        self.btn_load.setMinimumHeight(38)
        self.btn_load.clicked.connect(self.accept_selection)

        btn_box.addStretch()
        btn_box.addWidget(btn_cancel)
        btn_box.addWidget(self.btn_load)
        layout.addLayout(btn_box)

        self.file_map = {}
        self.populate_examples()
        self.list_widget.itemDoubleClicked.connect(self.accept_selection)

    def populate_examples(self):
        if os.path.exists(self.example_dir):
            files = [f for f in os.listdir(self.example_dir) if f.endswith('.v')]
            files.sort()
            for f in files:
                clean_name = f[:-2] if f.endswith('.v') else f
                self.file_map[clean_name] = os.path.join(self.example_dir, f)
                self.list_widget.addItem(clean_name)
        
        if self.list_widget.count() == 0:
            self.list_widget.addItem("No example files found")
            self.btn_load.setEnabled(False)

    def accept_selection(self):
        current_item = self.list_widget.currentItem()
        if current_item and current_item.text() in self.file_map:
            self.selected_file_path = self.file_map[current_item.text()]
            self.accept()

class SandboxPane(QFrame):
    def __init__(self):
        super().__init__()
        self.setObjectName("PaneFrame")
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.layout.setSpacing(10)

        header_layout = QHBoxLayout()
        
        self.btn_help = QPushButton("?")
        self.btn_help.setObjectName("HelpBtn")
        self.btn_help.setFixedSize(26, 26)
        self.btn_help.setCursor(Qt.PointingHandCursor)
        self.btn_help.setToolTip("How to use this tool")
        self.btn_help.clicked.connect(self.show_module_help)
        
        self.tool_selector = TitleComboBox()
        self.tool_selector.setObjectName("PaneTitleDropdown")
        self.tool_selector.setMaxVisibleItems(14)

        self.tool_selector.addItems([
            "Empty Workspace",       
            "Pixel Matrix",          
            "Character Display",     
            "Register Monitor",      
            "DIP & Hex I/O",         
            "Programmable Keypad",   
            "Slider ADC In",         
            "Gauge ADC Out",         
            "Mouse dir In",          
            "String In",             
            "Memory Region",         
            "Console Log"            
        ])
        self.tool_selector.currentIndexChanged.connect(self.switch_tool)
        
        header_layout.addWidget(self.btn_help)
        header_layout.addStretch()
        header_layout.addWidget(self.tool_selector)
        self.layout.addLayout(header_layout)

        self.stack = QStackedWidget()
        self.layout.addWidget(self.stack)

        self.setup_placeholders()

    def setup_placeholders(self):
        empty = QLabel("Select a tool from the dropdown above.", alignment=Qt.AlignCenter)
        empty.setStyleSheet("color: #888888; font-style: italic;")
        self.stack.addWidget(empty)
        
        self.pixel_matrix = PixelMatrixView()
        self.stack.addWidget(self.pixel_matrix)
        
        self.char_display = CharDisplayView()
        self.stack.addWidget(self.char_display)
        
        self.register_monitor = RegisterMonitorView()
        self.stack.addWidget(self.register_monitor)
        
        self.dip_io = DipHexIOView()
        self.stack.addWidget(self.dip_io)
        
        self.keypad = ProgrammableKeypadView()
        self.stack.addWidget(self.keypad)

        self.slider_adc = SliderADCView()
        self.stack.addWidget(self.slider_adc)

        self.gauge_adc = GaugeADCView()
        self.stack.addWidget(self.gauge_adc)

        self.mouse_sensor = MouseDirectionView()
        self.stack.addWidget(self.mouse_sensor)

        self.string_input = StringInputView()
        self.stack.addWidget(self.string_input)

        self.memory_region = MemoryRegionView()
        self.stack.addWidget(self.memory_region)

        self.console_log = ConsoleLogView()
        self.stack.addWidget(self.console_log)

    def switch_tool(self, index):
        self.stack.setCurrentIndex(index)

    def show_module_help(self):
        current_widget = self.stack.currentWidget()
        if hasattr(current_widget, 'show_help'):
            current_widget.show_help()
        else:
            msg = QMessageBox(self)
            msg.setWindowTitle("Sandbox Help")
            msg.setText("Please select a tool from the dropdown menu first to view its specific guide.")
            msg.exec_()


class UnifiedSandboxIDE(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("µP Verilog Sandbox & Visual Builder")
        self.resize(1360, 850)
        self.setStyleSheet(STYLE_SHEET)
        
        self.target_verilog_file = None
        
        self.engine = SimulationEngine()
        self.engine.log_message.connect(self.broadcast_log)
        self.engine.parsed_design.connect(self.distribute_parsed_data)
        self.engine.hardware_updated.connect(self.sync_hardware_to_ui)
        
        self.clock_timer = QTimer()
        self.clock_timer.timeout.connect(lambda: self.engine.send_command('clk', 1))
        
        self.setup_ui()

        self.left_pane.dip_io.byte_a.value_changed.connect(lambda v: self.engine.send_command('port_a', v))
        self.left_pane.dip_io.byte_b.value_changed.connect(lambda v: self.engine.send_command('port_b', v))
        self.right_pane.dip_io.byte_a.value_changed.connect(lambda v: self.engine.send_command('port_a', v))
        self.right_pane.dip_io.byte_b.value_changed.connect(lambda v: self.engine.send_command('port_b', v))
        self.left_pane.slider_adc.adc_updated.connect(self.engine.send_command)
        self.right_pane.slider_adc.adc_updated.connect(self.engine.send_command)
        self.left_pane.string_input.string_updated.connect(self.engine.send_command)
        self.right_pane.string_input.string_updated.connect(self.engine.send_command)
        self.left_pane.keypad.keypad_triggered.connect(self.engine.send_command)
        self.right_pane.keypad.keypad_triggered.connect(self.engine.send_command)
        self.left_pane.mouse_sensor.mouse_updated.connect(self.engine.send_command)
        self.right_pane.mouse_sensor.mouse_updated.connect(self.engine.send_command)
        self.btn_pulse.clicked.connect(lambda: self.engine.send_command('clk', 1))

    def broadcast_log(self, message, level="INFO"):
        self.left_pane.console_log.log_message(message, level)
        self.right_pane.console_log.log_message(message, level)

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_h_layout = QHBoxLayout(central_widget)
        main_h_layout.setContentsMargins(0, 0, 0, 0)
        main_h_layout.setSpacing(0)

        # 1. MAIN APPS STACK
        self.app_stack = QStackedWidget()

        # --- PAGE 0: Full Visual Block Builder ---
        self.full_block_builder = VisualBlockBuilder()
        self.full_block_builder.file_changed.connect(self.on_builder_file_saved)
        self.app_stack.addWidget(self.full_block_builder)

        # --- PAGE 1: Hardware Sandbox Split Workspace ---
        sandbox_container = QWidget()
        sandbox_layout = QVBoxLayout(sandbox_container)
        sandbox_layout.setContentsMargins(0, 0, 0, 0)
        sandbox_layout.setSpacing(0)
        
        # A. GLOBAL HEADER
        header = QFrame()
        header.setObjectName("HeaderFrame")
        header.setFixedHeight(70)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(15, 10, 15, 10)
        
        self.btn_select_file = QPushButton("Load Target .v")
        self.btn_select_file.setObjectName("FileBtn")
        self.btn_select_file.setFixedSize(140, 35)
        self.btn_select_file.clicked.connect(self.select_file)
        
        separator = QFrame()
        separator.setFrameShape(QFrame.VLine)
        separator.setFrameShadow(QFrame.Plain)
        separator.setLineWidth(2)
        separator.setFixedHeight(26)
        separator.setStyleSheet("background-color: #555555; border: none;")

        self.btn_get_example = QPushButton("Get Example")
        self.btn_get_example.setObjectName("ExampleBtn")
        self.btn_get_example.setFixedSize(140, 35)
        self.btn_get_example.clicked.connect(self.open_example_dialog)

        self.lbl_file = QLabel("No File Selected")
        self.lbl_file.setStyleSheet("color: #888888; font-family: monospace;")
        
        header_layout.addWidget(self.btn_select_file)
        header_layout.addSpacing(6)
        header_layout.addWidget(separator)
        header_layout.addSpacing(6)
        header_layout.addWidget(self.btn_get_example)
        header_layout.addSpacing(12)
        header_layout.addWidget(self.lbl_file)
        
        header_layout.addStretch(1)
        
        clk_label = QLabel("CLOCK ENGINE:")
        clk_label.setStyleSheet("font-weight: bold; color: #888888;")
        header_layout.addWidget(clk_label)
        header_layout.addSpacing(8)

        self.btn_pulse = QPushButton("PULSE")
        self.btn_pulse.setFixedSize(85, 35)
        header_layout.addWidget(self.btn_pulse)

        self.btn_lever = QPushButton("MANUAL")
        self.btn_lever.setObjectName("LeverBtn")
        self.btn_lever.setCheckable(True)
        self.btn_lever.setFixedSize(110, 35)
        self.btn_lever.toggled.connect(self.toggle_clock_mode)
        header_layout.addWidget(self.btn_lever)

        self.combo_freq = QComboBox()
        self.combo_freq.addItems(["1 Hz (Debug)", "4 Hz", "16 Hz", "256 Hz", "1 kHz (Fast)", "Max (Unlimited)"])
        self.combo_freq.currentIndexChanged.connect(self.update_clock_frequency)
        self.combo_freq.setFixedSize(135, 35)
        self.combo_freq.setEnabled(False)
        self.combo_freq.setStyleSheet("color: #888888; border-color: #555555; background-color: #1E1E1E;")
        header_layout.addWidget(self.combo_freq)

        header_layout.addSpacing(20)

        self.btn_help_link = QPushButton("?  (Help)")
        self.btn_help_link.setObjectName("GlobalHelpBtn")
        self.btn_help_link.setFixedSize(110, 35)
        self.btn_help_link.setCursor(Qt.PointingHandCursor)
        self.btn_help_link.setToolTip("Open Online Documentation & User Guide")
        self.btn_help_link.clicked.connect(self.open_help_webpage)
        header_layout.addWidget(self.btn_help_link)

        sandbox_layout.addWidget(header)

        # B. SPLIT WORKSPACE
        workspace_container = QWidget()
        workspace_layout = QVBoxLayout(workspace_container)
        workspace_layout.setContentsMargins(15, 15, 15, 15)
        
        self.splitter = QSplitter(Qt.Horizontal)
        
        self.left_pane = SandboxPane()
        self.right_pane = SandboxPane()
        
        self.left_pane.tool_selector.setCurrentIndex(11) # Default panes
        self.right_pane.tool_selector.setCurrentIndex(0)
        
        self.splitter.addWidget(self.left_pane)
        self.splitter.addWidget(self.right_pane)
        self.splitter.setSizes([640, 640])
        
        workspace_layout.addWidget(self.splitter)
        sandbox_layout.addWidget(workspace_container, 1) 
        
        self.app_stack.addWidget(sandbox_container)

        # 2. SIDEWAYS VERTICAL NAVIGATION BAR
        self.nav_bar = VerticalTabBar(self.app_stack)

        main_h_layout.addWidget(self.nav_bar)
        main_h_layout.addWidget(self.app_stack, 1)

    # --- BIDIRECTIONAL FILE SYNC HANDLERS ---
    def on_builder_file_saved(self, file_path):
        self.target_verilog_file = file_path
        filename = os.path.basename(file_path)
        self.lbl_file.setText(f"Target: {filename}")
        self.lbl_file.setStyleSheet("color: #1c1c1c; font-family: monospace; font-weight: bold;")
        self.engine.compile_and_run(file_path)

    def select_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Verilog Target File", "", "Verilog Files (*.v)")
        if file_path:
            self.target_verilog_file = file_path
            filename = os.path.basename(file_path)
            self.lbl_file.setText(f"Target: {filename}")
            self.lbl_file.setStyleSheet("color: #1c1c1c; font-family: monospace; font-weight: bold;")
            
            self.full_block_builder.load_external_file(file_path)
            self.engine.compile_and_run(file_path)

    def open_example_dialog(self):
        example_dir = self.get_examples_directory()
        dialog = ExampleSelectorDialog(example_dir, self)
        
        if dialog.exec_() == QDialog.Accepted and dialog.selected_file_path:
            self.target_verilog_file = dialog.selected_file_path
            filename = os.path.basename(dialog.selected_file_path)
            self.lbl_file.setText(f"Target: {filename}")
            self.lbl_file.setStyleSheet("color: #00E5FF; font-family: monospace; font-weight: bold;")
            
            self.full_block_builder.load_external_file(dialog.selected_file_path)
            self.engine.compile_and_run(dialog.selected_file_path)

    # --- ENGINE BINDINGS ---
    def distribute_parsed_data(self, parsed):
        self.left_pane.keypad.set_available_inputs(parsed['inputs'])
        self.right_pane.keypad.set_available_inputs(parsed['inputs'])
        all_signals = parsed['inputs'] + parsed['outputs'] + parsed['internals']
        self.left_pane.register_monitor.set_available_signals(all_signals)
        self.right_pane.register_monitor.set_available_signals(all_signals)
        self.left_pane.slider_adc.set_available_inputs(parsed['inputs'])
        self.right_pane.slider_adc.set_available_inputs(parsed['inputs'])
        self.left_pane.gauge_adc.set_available_signals(parsed['outputs'] + parsed['internals'])
        self.right_pane.gauge_adc.set_available_signals(parsed['outputs'] + parsed['internals'])
        self.left_pane.string_input.set_available_inputs(parsed['inputs'])
        self.right_pane.string_input.set_available_inputs(parsed['inputs'])

    def sync_hardware_to_ui(self, state_dict):
        if 'out_monitor' in state_dict:
            self.left_pane.dip_io.set_output_value(state_dict['out_monitor'])
            self.right_pane.dip_io.set_output_value(state_dict['out_monitor'])
            
        if 'pixel_matrix' in state_dict:
            matrix_val = state_dict['pixel_matrix']
            for y in range(16):
                for x in range(16):
                    is_on = bool((matrix_val >> ((y * 16) + x)) & 1)
                    self.left_pane.pixel_matrix.update_pixel(x, y, is_on)
                    self.right_pane.pixel_matrix.update_pixel(x, y, is_on)

        self.left_pane.register_monitor.sync_data(state_dict)
        self.right_pane.register_monitor.sync_data(state_dict)
        self.left_pane.char_display.update_values(state_dict)
        self.right_pane.char_display.update_values(state_dict)
        self.left_pane.gauge_adc.update_values(state_dict)
        self.left_pane.memory_region.sync_data(state_dict)
        self.right_pane.memory_region.sync_data(state_dict)

    def toggle_clock_mode(self, is_auto):
        if is_auto:
            self.btn_lever.setText("AUTO")
            self.btn_pulse.setEnabled(False)
            self.btn_pulse.setStyleSheet("color: #555555; border-color: #555555; background-color: #252526;")
            self.combo_freq.setEnabled(True)
            self.combo_freq.setStyleSheet("")
            
            freq_map = {0: 1000, 1: 250, 2: 62, 3: 4, 4: 1, 5: 1}
            interval = freq_map.get(self.combo_freq.currentIndex(), 1000)
            self.clock_timer.start(interval)
            
            self.left_pane.console_log.log_message("Clock Engine switched to AUTO mode.", "INFO")
            self.right_pane.console_log.log_message("Clock Engine switched to AUTO mode.", "INFO")
            self.left_pane.mouse_sensor.set_auto_clock(True)
            self.right_pane.mouse_sensor.set_auto_clock(True)
        else:
            self.btn_lever.setText("MANUAL")
            self.btn_pulse.setEnabled(True)
            self.btn_pulse.setStyleSheet("")
            self.combo_freq.setEnabled(False)
            self.combo_freq.setStyleSheet("color: #888888; border-color: #555555; background-color: #1E1E1E;")
            self.clock_timer.stop()
            
            self.left_pane.console_log.log_message("Clock Engine switched to MANUAL mode.", "INFO")
            self.right_pane.console_log.log_message("Clock Engine switched to MANUAL mode.", "INFO")
            self.left_pane.mouse_sensor.set_auto_clock(False)
            self.right_pane.mouse_sensor.set_auto_clock(False)

    def update_clock_frequency(self):
        if self.clock_timer.isActive():
            freq_map = {0: 1000, 1: 250, 2: 62, 3: 4, 4: 1, 5: 1}
            interval = freq_map.get(self.combo_freq.currentIndex(), 1000)
            self.clock_timer.start(interval)

    def open_help_webpage(self):
        url = QUrl("https://github.com") 
        QDesktopServices.openUrl(url)

    def get_examples_directory(self):
        if getattr(sys, 'frozen', False):
            base_dir = getattr(sys, '_MEIPASS', os.path.dirname(sys.executable))
            exe_dir = os.path.dirname(sys.executable)
            possible_paths = [
                os.path.join(base_dir, "_internal", "examples"),
                os.path.join(exe_dir, "_internal", "examples"),
                os.path.join(base_dir, "examples"),
                os.path.join(exe_dir, "examples")
            ]
        else:
            src_dir = os.path.dirname(os.path.abspath(__file__))          
            root_dir = os.path.dirname(src_dir)                           
            cwd = os.getcwd()

            possible_paths = [
                os.path.join(root_dir, "examples"),                       
                os.path.join(src_dir, "examples"),                        
                os.path.join(cwd, "examples"),                            
                os.path.join(root_dir, "_internal", "examples"),
                os.path.join(src_dir, "_internal", "examples")
            ]

        for path in possible_paths:
            if os.path.exists(path):
                v_files = [f for f in os.listdir(path) if f.endswith('.v')]
                if v_files:
                    return path

        fallback = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "examples")
        os.makedirs(fallback, exist_ok=True)
        return fallback

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    if getattr(sys, 'frozen', False):
        # PyInstaller bundled path resolution
        base_dir = getattr(sys, '_MEIPASS', os.path.dirname(sys.executable))
        icon_path = os.path.join(base_dir, "assets", "icon.png")
        if not os.path.exists(icon_path):
            icon_path = os.path.join(base_dir, "_internal", "assets", "icon.png")
    else:
        # Standard Python script path resolution
        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "icon.png")
        
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))
        
    font = QFont("Segoe UI", 10)
    app.setFont(font)
    
    window = UnifiedSandboxIDE()
    window.show()
    sys.exit(app.exec_())