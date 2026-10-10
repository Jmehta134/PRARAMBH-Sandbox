import sys
import os
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QSplitter, QComboBox, QPushButton, QLabel, QFileDialog, QStackedWidget,
    QFrame, QMessageBox
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont

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
from console_log import ConsoleLogView

# Import the Dynamic Simulation Backend Engine
from sim_engine import SimulationEngine

# =============================================================================
# GLOBAL STYLING (Neutral/Grey System Theme)
# =============================================================================
STYLE_SHEET = """
QMainWindow {
    background-color: #F0F0F0;
}
QWidget {
    color: #333333;
    font-family: 'Segoe UI', Arial, sans-serif;
}
QFrame#HeaderFrame {
    background-color: #E5E5E5;
    border-bottom: 1px solid #CCCCCC;
    border-radius: 0px;
}
QFrame#PaneFrame {
    background-color: #FAFAFA;
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
}
QPushButton:pressed {
    background-color: #CCE4F7;
    border: 1px solid #005499;
}
/* Kakooii Circular Help Button */
QPushButton#HelpBtn {
    background-color: #EFEFEF;
    border: 2px solid #ADADAD;
    border-bottom: 3px solid #888888;
    border-radius: 13px; /* Perfectly circular */
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
QPushButton#ResetBtn {
    background-color: #D13438;
    color: white;
    border: 1px solid #A80000;
}
QPushButton#ResetBtn:hover {
    background-color: #E81123;
}
QPushButton#LeverBtn {
    background-color: #E1E1E1;
    border: 2px solid #ADADAD;
    color: #555555;
}
QPushButton#LeverBtn:checked {
    background-color: #0078D7;
    border: 2px solid #005A9E;
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
QSplitter::handle {
    background-color: #CCCCCC;
    width: 4px;
}
QSplitter::handle:hover {
    background-color: #0078D7;
}
"""

# =============================================================================
# DYNAMIC PANE WIDGET (Left & Right Split)
# =============================================================================
class SandboxPane(QFrame):
    def __init__(self):
        super().__init__()
        self.setObjectName("PaneFrame")
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.layout.setSpacing(10)

        # Pane Header (Help Button on Left, Selector on Right)
        header_layout = QHBoxLayout()
        
        self.btn_help = QPushButton("?")
        self.btn_help.setObjectName("HelpBtn")
        self.btn_help.setFixedSize(26, 26)
        self.btn_help.setCursor(Qt.PointingHandCursor)
        self.btn_help.setToolTip("How to use this tool")
        self.btn_help.clicked.connect(self.show_module_help)
        
        self.tool_selector = QComboBox()
        self.tool_selector.addItems([
            "Empty Workspace",       # 0
            "Pixel Matrix",          # 1
            "Character Display",     # 2
            "Register Monitor",      # 3
            "DIP & Hex I/O",         # 4
            "Programmable Keypad",   # 5
            "Slider ADC In",         # 6
            "Gauge ADC Out",         # 7
            "Mouse dir In",          # 8
            "String In",          # 8
            "Console Log"            # 9
        ])
        self.tool_selector.currentIndexChanged.connect(self.switch_tool)
        
        header_layout.addWidget(self.btn_help)
        header_layout.addStretch()
        header_layout.addWidget(self.tool_selector)
        self.layout.addLayout(header_layout)

        # Tool Stack
        self.stack = QStackedWidget()
        self.layout.addWidget(self.stack)

        self.setup_placeholders()

    def setup_placeholders(self):
        # 0: Empty Workspace
        empty = QLabel("Select a tool from the dropdown above.", alignment=Qt.AlignCenter)
        empty.setStyleSheet("color: #888888; font-style: italic;")
        self.stack.addWidget(empty)
        
        # 1: Pixel Matrix View
        self.pixel_matrix = PixelMatrixView()
        self.stack.addWidget(self.pixel_matrix)
        
        # 2: 16x3 Display
        self.char_display = CharDisplayView()
        self.stack.addWidget(self.char_display)
        
        # 3: Register Monitor
        self.register_monitor = RegisterMonitorView()
        self.stack.addWidget(self.register_monitor)
        
        # 4: DIP & Hex I/O
        self.dip_io = DipHexIOView()
        self.stack.addWidget(self.dip_io)
        
        # 5: Programmable Keypad
        self.keypad = ProgrammableKeypadView()
        self.stack.addWidget(self.keypad)

        # Slider pane
        self.slider_adc = SliderADCView()
        self.stack.addWidget(self.slider_adc)

        # Gauge pane
        self.gauge_adc = GaugeADCView()
        self.stack.addWidget(self.gauge_adc)

        # Mouse dir pane
        self.mouse_sensor = MouseDirectionView()
        self.stack.addWidget(self.mouse_sensor)

        # String Input
        self.string_input = StringInputView()
        self.stack.addWidget(self.string_input)

        # Console Log
        self.console_log = ConsoleLogView()
        self.stack.addWidget(self.console_log)

    def switch_tool(self, index):
        self.stack.setCurrentIndex(index)

    def show_module_help(self):
        """Fetches and displays the learner instructions from the active tool."""
        current_widget = self.stack.currentWidget()
        if hasattr(current_widget, 'show_help'):
            current_widget.show_help()
        else:
            msg = QMessageBox(self)
            msg.setWindowTitle("Sandbox Help")
            msg.setText("Please select a tool from the dropdown menu first to view its specific guide.")
            msg.exec_()


# =============================================================================
# MAIN APPLICATION WINDOW
# =============================================================================
class UnifiedSandboxIDE(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("µP PRARAMBH - Dynamic Verilog Sandbox")
        self.resize(1280, 800)
        self.setStyleSheet(STYLE_SHEET)
        
        self.target_verilog_file = None
        self.setup_ui()
        
        # --- INITIALIZE SIMULATION ENGINE ---
        self.engine = SimulationEngine()
        self.engine.log_message.connect(self.broadcast_log)
        self.engine.parsed_design.connect(self.distribute_parsed_data)
        self.engine.hardware_updated.connect(self.sync_hardware_to_ui)
        
        # Auto-Clock Timer setup
        self.clock_timer = QTimer()
        self.clock_timer.timeout.connect(lambda: self.engine.send_command('clk', 1))
        
        # --- UI TO ENGINE SIGNAL BINDINGS ---
        # Fixed port bindings (trigged when DIP switch values change)
        self.left_pane.dip_io.byte_a.value_changed.connect(lambda v: self.engine.send_command('port_a', v))
        self.left_pane.dip_io.byte_b.value_changed.connect(lambda v: self.engine.send_command('port_b', v))
        self.right_pane.dip_io.byte_a.value_changed.connect(lambda v: self.engine.send_command('port_a', v))
        self.right_pane.dip_io.byte_b.value_changed.connect(lambda v: self.engine.send_command('port_b', v))

        self.left_pane.slider_adc.adc_updated.connect(self.engine.send_command)
        self.right_pane.slider_adc.adc_updated.connect(self.engine.send_command)

        self.left_pane.string_input.string_updated.connect(self.engine.send_command)
        self.right_pane.string_input.string_updated.connect(self.engine.send_command)
        
        # Generic bindings (The keypad dynamically targets specific ports)
        self.left_pane.keypad.keypad_triggered.connect(self.engine.send_command)
        self.right_pane.keypad.keypad_triggered.connect(self.engine.send_command)

        self.left_pane.mouse_sensor.mouse_updated.connect(self.engine.send_command)
        self.right_pane.mouse_sensor.mouse_updated.connect(self.engine.send_command)

        # Global Control Controls
        self.btn_pulse.clicked.connect(lambda: self.engine.send_command('clk', 1))
        self.btn_reset.pressed.connect(lambda: self.engine.send_command('rst', 1))
        self.btn_reset.released.connect(lambda: self.engine.send_command('rst', 0))

    def broadcast_log(self, message, level="INFO"):
        """Broadcasts simulation logs to both left and right console panes."""
        self.left_pane.console_log.log_message(message, level)
        self.right_pane.console_log.log_message(message, level)

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 1. GLOBAL HEADER
        header = QFrame()
        header.setObjectName("HeaderFrame")
        header.setFixedHeight(70)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(15, 10, 15, 10)
        
        # -- File Selection (160px width for clean visibility)
        self.btn_select_file = QPushButton("Load Target .v")
        self.btn_select_file.setObjectName("FileBtn")
        self.btn_select_file.setFixedSize(160, 35)
        self.btn_select_file.clicked.connect(self.select_file)
        
        self.lbl_file = QLabel("No File Selected")
        self.lbl_file.setStyleSheet("color: #666666; font-family: monospace;")
        
        header_layout.addWidget(self.btn_select_file)
        header_layout.addWidget(self.lbl_file)
        
        # Spacer to push clock controls to the right
        header_layout.addStretch(1)
        
        # -- Clocking Engine
        clk_label = QLabel("CLOCK ENGINE:")
        clk_label.setStyleSheet("font-weight: bold; color: #555555;")
        header_layout.addWidget(clk_label)
        header_layout.addSpacing(8)

        self.btn_pulse = QPushButton("PULSE")
        self.btn_pulse.setFixedSize(85, 35)
        header_layout.addWidget(self.btn_pulse)

        # 110px width so MANUAL is never cropped
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
        self.combo_freq.setStyleSheet("color: #AAAAAA; border-color: #CCCCCC; background-color: #F0F0F0;")
        header_layout.addWidget(self.combo_freq)

        header_layout.addSpacing(20)

        # -- Global Reset (135px width for clean visibility)
        self.btn_reset = QPushButton("GLOBAL RST")
        self.btn_reset.setObjectName("ResetBtn")
        self.btn_reset.setFixedSize(135, 35)
        header_layout.addWidget(self.btn_reset)

        main_layout.addWidget(header)

        # 2. SPLIT WORKSPACE
        workspace_container = QWidget()
        workspace_layout = QVBoxLayout(workspace_container)
        workspace_layout.setContentsMargins(15, 15, 15, 15)
        
        self.splitter = QSplitter(Qt.Horizontal)
        
        self.left_pane = SandboxPane()
        self.right_pane = SandboxPane()
        
        # --- INITIAL CONFIGURATION ON STARTUP ---
        self.left_pane.tool_selector.setCurrentIndex(9)  # Console Log
        self.right_pane.tool_selector.setCurrentIndex(0) # Empty Workspace
        
        self.splitter.addWidget(self.left_pane)
        self.splitter.addWidget(self.right_pane)
        self.splitter.setSizes([640, 640])
        
        workspace_layout.addWidget(self.splitter)
        main_layout.addWidget(workspace_container)

    def select_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Verilog Target File", "", "Verilog Files (*.v)")
        if file_path:
            self.target_verilog_file = file_path
            filename = os.path.basename(file_path)
            self.lbl_file.setText(f"Target: {filename}")
            self.lbl_file.setStyleSheet("color: #005A9E; font-family: monospace; font-weight: bold;")
            
            # Start dynamic AST introspection & compile process
            self.engine.compile_and_run(file_path)

    def distribute_parsed_data(self, parsed):
        """Passes extracted inputs and internal registers to user modules."""
        # Supply inputs to Macro Keypads
        self.left_pane.keypad.set_available_inputs(parsed['inputs'])
        self.right_pane.keypad.set_available_inputs(parsed['inputs'])
        
        # Supply internal registers to Register Monitors
        self.left_pane.register_monitor.set_available_signals(parsed['internals'])
        self.right_pane.register_monitor.set_available_signals(parsed['internals'])
        
        # Supply data to Displays

        self.left_pane.slider_adc.set_available_inputs(parsed['inputs'])
        self.right_pane.slider_adc.set_available_inputs(parsed['inputs'])

        self.left_pane.gauge_adc.set_available_signals(parsed['outputs'] + parsed['internals'])
        self.right_pane.gauge_adc.set_available_signals(parsed['outputs'] + parsed['internals'])

        self.left_pane.string_input.set_available_inputs(parsed['inputs'])
        self.right_pane.string_input.set_available_inputs(parsed['inputs'])

    def sync_hardware_to_ui(self, state_dict):
        """Routes live simulation dictionary to active UI widgets."""
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

        # Update dynamic dropdown register rows
        self.left_pane.register_monitor.sync_data(state_dict)
        self.right_pane.register_monitor.sync_data(state_dict)
        
        # Update OLED Displays <-- Added routing here
        self.left_pane.char_display.update_values(state_dict)
        self.right_pane.char_display.update_values(state_dict)

        self.left_pane.gauge_adc.update_values(state_dict)

    def toggle_clock_mode(self, is_auto):
        if is_auto:
            self.btn_lever.setText("AUTO")
            self.btn_pulse.setEnabled(False)
            self.btn_pulse.setStyleSheet("color: #AAAAAA; border-color: #CCCCCC; background-color: #F0F0F0;")
            self.combo_freq.setEnabled(True)
            self.combo_freq.setStyleSheet("")
            
            freq_map = {0: 1000, 1: 250, 2: 62, 3: 4, 4: 1, 5: 1}
            interval = freq_map.get(self.combo_freq.currentIndex(), 1000)
            self.clock_timer.start(interval)
            
            self.left_pane.console_log.log_message("Clock Engine switched to AUTO mode.", "INFO")
            self.right_pane.console_log.log_message("Clock Engine switched to AUTO mode.", "INFO")
        else:
            self.btn_lever.setText("MANUAL")
            self.btn_pulse.setEnabled(True)
            self.btn_pulse.setStyleSheet("")
            self.combo_freq.setEnabled(False)
            self.combo_freq.setStyleSheet("color: #AAAAAA; border-color: #CCCCCC; background-color: #F0F0F0;")
            self.clock_timer.stop()
            
            self.left_pane.console_log.log_message("Clock Engine switched to MANUAL mode.", "INFO")
            self.right_pane.console_log.log_message("Clock Engine switched to MANUAL mode.", "INFO")

    def update_clock_frequency(self):
        """Dynamically updates the clock speed if AUTO mode is currently active."""
        if self.clock_timer.isActive():
            freq_map = {0: 1000, 1: 250, 2: 62, 3: 4, 4: 1, 5: 1}
            interval = freq_map.get(self.combo_freq.currentIndex(), 1000)
            self.clock_timer.start(interval) # Calling start() again safely restarts it with the new interval
            
if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    font = QFont("Segoe UI", 10)
    app.setFont(font)
    
    window = UnifiedSandboxIDE()
    window.show()
    sys.exit(app.exec_())