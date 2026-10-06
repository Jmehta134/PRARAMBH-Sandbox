import sys
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, 
    QPushButton, QLabel, QLCDNumber, QApplication, QFrame, QMessageBox
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont

# =============================================================================
# COMPONENT: Custom Industrial DIP Switch
# =============================================================================
class DipSwitch(QPushButton):
    """A custom toggle button styled to look like a physical hardware DIP switch."""
    state_changed = pyqtSignal(int, int)  # (bit_index, state)

    def __init__(self, bit_index):
        super().__init__()
        self.bit_index = bit_index
        self.setCheckable(True)
        self.setFixedSize(38, 75)  # Slightly proportioned for better ergonomics
        self.setCursor(Qt.PointingHandCursor)
        self.setText("0")
        
        # Upgraded font size (15px bold) for clear 0/1 readability
        self.style_unchecked = """
            QPushButton {
                background-color: #E5E5E5;
                border: 2px solid #B0B0B0;
                border-radius: 4px;
                color: #666666;
                font-weight: bold;
                font-size: 15px;
                padding-top: 32px; 
            }
            QPushButton:hover { border: 2px solid #888888; }
        """
        
        self.style_checked = """
            QPushButton {
                background-color: #0078D7;
                border: 2px solid #005A9E;
                border-radius: 4px;
                color: white;
                font-weight: bold;
                font-size: 15px;
                padding-bottom: 32px; 
            }
            QPushButton:hover { background-color: #1084D0; }
        """
        
        self.setStyleSheet(self.style_unchecked)
        self.toggled.connect(self.on_toggle)

    def on_toggle(self, checked):
        if checked:
            self.setText("1")
            self.setStyleSheet(self.style_checked)
        else:
            self.setText("0")
            self.setStyleSheet(self.style_unchecked)
        self.state_changed.emit(self.bit_index, 1 if checked else 0)

# =============================================================================
# COMPONENT: Virtual LED Indicator
# =============================================================================
class VirtualLED(QFrame):
    """A custom styled widget representing a hardware status LED."""
    def __init__(self):
        super().__init__()
        self.setFixedSize(22, 22)
        self.set_state(False)

    def set_state(self, is_on):
        if is_on:
            self.setStyleSheet("""
                QFrame {
                    background-color: #00E5FF;
                    border: 1px solid #00B3CC;
                    border-radius: 11px;
                }
            """)
        else:
            self.setStyleSheet("""
                QFrame {
                    background-color: #D0D0D0;
                    border: 1px solid #A0A0A0;
                    border-radius: 11px;
                }
            """)

# =============================================================================
# MODULE: 8-Bit Byte Control Group
# =============================================================================
class ByteControl(QGroupBox):
    """Groups 8 DIP switches and a Hex LCD display for a single 8-bit bus."""
    value_changed = pyqtSignal(int)

    def __init__(self, title):
        super().__init__(title)
        # Harmonized group box header typography with letter spacing
        self.setStyleSheet("""
            QGroupBox {
                font-weight: 900;
                color: #333333;
                border: 2px solid #CCCCCC;
                border-radius: 8px;
                margin-top: 14px;
                padding-top: 20px;
                font-size: 13px;
                letter-spacing: 1px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 14px;
                padding: 0 6px;
            }
        """)
        
        self.current_val = 0
        self.switches = []
        
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # Switch Row (MSB to LSB: 7 to 0)
        switch_layout = QHBoxLayout()
        switch_layout.setAlignment(Qt.AlignCenter)
        
        for i in range(7, -1, -1):
            sw = DipSwitch(i)
            sw.state_changed.connect(self.update_value)
            
            bit_layout = QVBoxLayout()
            bit_layout.setSpacing(4)
            bit_label = QLabel(f"b{i}")
            bit_label.setAlignment(Qt.AlignCenter)
            # Upgraded bit label typography for high contrast & clarity
            bit_label.setStyleSheet("color: #333333; font-size: 12px; font-weight: bold;")
            
            bit_layout.addWidget(bit_label)
            bit_layout.addWidget(sw)
            switch_layout.addLayout(bit_layout)
            self.switches.append(sw)
            
        layout.addLayout(switch_layout)
        
        # Hex LCD Display
        self.lcd = QLCDNumber()
        self.lcd.setDigitCount(2)
        self.lcd.setHexMode()
        self.lcd.setFixedHeight(50)
        self.lcd.setStyleSheet("""
            QLCDNumber {
                background-color: #1E1E1E;
                color: #00FF00;
                border: 2px inset #555555;
                border-radius: 4px;
            }
        """)
        self.lcd.display("00")
        
        layout.addWidget(self.lcd)

    def update_value(self, bit_index, state):
        if state == 1:
            self.current_val |= (1 << bit_index)
        else:
            self.current_val &= ~(1 << bit_index)
            
        self.lcd.display(f"{self.current_val:02X}")
        self.value_changed.emit(self.current_val)

# =============================================================================
# MAIN PANE: DIP & Hex I/O View
# =============================================================================
class DipHexIOView(QWidget):
    """The main modular pane to be injected into the Unified Sandbox."""
    def __init__(self):
        super().__init__()
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(15)
        
        # --- TOP SECTION: Inputs ---
        self.byte_a = ByteControl("INPUT PORT A [7:0]")
        self.byte_b = ByteControl("INPUT PORT B [7:0]")
        
        self.byte_a.value_changed.connect(lambda val: print(f"Port A updated: 0x{val:02X}"))
        self.byte_b.value_changed.connect(lambda val: print(f"Port B updated: 0x{val:02X}"))
        
        main_layout.addWidget(self.byte_a)
        main_layout.addWidget(self.byte_b)
        
        # --- BOTTOM SECTION: 16-Bit Output ---
        output_group = QGroupBox("OUTPUT MONITOR [15:0]")
        output_group.setStyleSheet(self.byte_a.styleSheet())
        
        output_layout = QVBoxLayout(output_group)
        
        # Two rows of 8 LEDs for clean 16-bit visualization
        led_layout_high = QHBoxLayout()
        led_layout_low = QHBoxLayout()
        led_layout_high.setAlignment(Qt.AlignCenter)
        led_layout_low.setAlignment(Qt.AlignCenter)
        
        self.leds = []
        for i in range(15, -1, -1):
            bit_layout = QVBoxLayout()
            bit_layout.setSpacing(4)
            lbl = QLabel(f"O{i}")
            lbl.setAlignment(Qt.AlignCenter)
            # Matching prominent typography for output bit labels
            lbl.setStyleSheet("color: #333333; font-size: 12px; font-weight: bold;")
            
            led = VirtualLED()
            self.leds.append(led)
            
            bit_layout.addWidget(lbl)
            bit_layout.addWidget(led)
            
            if i > 7:
                led_layout_high.addLayout(bit_layout)
            else:
                led_layout_low.addLayout(bit_layout)
            
        output_layout.addLayout(led_layout_high)
        output_layout.addLayout(led_layout_low)
        
        self.lcd_out = QLCDNumber()
        self.lcd_out.setDigitCount(4)
        self.lcd_out.setHexMode()
        self.lcd_out.setFixedHeight(50)
        self.lcd_out.setStyleSheet(self.byte_a.lcd.styleSheet())
        self.lcd_out.display("0000")
        
        output_layout.addWidget(self.lcd_out)
        main_layout.addWidget(output_group)
        
        main_layout.addStretch()

    def set_output_value(self, hex_val):
        """Updates the output LEDs and Hex display based on hardware simulation."""
        self.lcd_out.display(f"{hex_val:04X}")
        for i in range(16):
            is_on = bool((hex_val >> (15 - i)) & 1)
            self.leds[i].set_state(is_on)

    def show_help(self):
        msg = QMessageBox(self)
        msg.setWindowTitle("Learner Guide: DIP & Hex I/O")
        msg.setText(
            "<b>DIP & Hex I/O Interface Mapping</b><br><br>"
            "This module acts as an 8-bit input driver and 16-bit output monitor. "
            "It automatically maps to the following exact port name strings in your Verilog file:<br><br>"
            "<b>Input Ports Driven:</b><br>"
            "• <code>port_a</code> : 8-bit input bus (Input Port A [7:0])<br>"
            "• <code>port_b</code> : 8-bit input bus (Input Port B [7:0])<br><br>"
            "<b>Output Port Monitored:</b><br>"
            "• <code>out_monitor</code> : 16-bit output bus (Output Monitor [15:0])<br><br>"
            "<b>How to use in Verilog:</b><br>"
            "Declare these exact names in your top module header:<br>"
            "<code>module top(input [7:0] port_a, input [7:0] port_b, output [15:0] out_monitor);</code><br><br>"
            "Toggling the DIP switches live-updates <code>port_a</code> and <code>port_b</code> in the simulator, "
            "and any logic driving <code>out_monitor</code> lights up the LEDs and Hex display instantly!"
        )
        msg.exec_()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    test_window = QWidget()
    test_window.setStyleSheet("background-color: #FAFAFA;")
    layout = QVBoxLayout(test_window)
    module = DipHexIOView()
    layout.addWidget(module)
    test_window.setWindowTitle("Module Test: 8-Bit DIP & 16-Bit Output")
    test_window.resize(650, 850)
    test_window.show()
    sys.exit(app.exec_())