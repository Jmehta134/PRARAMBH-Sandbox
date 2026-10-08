import sys
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QGridLayout, 
    QMessageBox, QLCDNumber, QApplication
)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt

# =============================================================================
# COMPONENT: Virtual LED Indicator (For RS & EN Bits)
# =============================================================================
class VirtualLED(QFrame):
    """A custom styled widget representing a hardware status LED."""
    def __init__(self):
        super().__init__()
        self.setFixedSize(24, 24)
        self.set_state(False)

    def set_state(self, is_on):
        if is_on:
            self.setStyleSheet("""
                QFrame {
                    background-color: #00E5FF;
                    border: 1px solid #00B3CC;
                    border-radius: 12px;
                }
            """)
        else:
            self.setStyleSheet("""
                QFrame {
                    background-color: #D0D0D0;
                    border: 1px solid #A0A0A0;
                    border-radius: 12px;
                }
            """)

# =============================================================================
# MAIN PANE: HD44780 Emulated LCD Module
# =============================================================================
class CharDisplayView(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(15, 15, 15, 15)
        
        # Internal LCD Emulator State
        self.memory = [' '] * 64
        self.cursor = 0
        self.prev_en = False

        # --- Standardized Centered Pane Header ---
        title = QLabel("CHARACTER DISPLAY (LCD)")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("""
            font-weight: 900; 
            color: #333333; 
            font-size: 18px; 
            letter-spacing: 1.5px;
            margin-bottom: 5px;
        """)
        self.layout.addWidget(title)

        self.layout.addSpacing(5)

        # --- TOP SECTION: The Character Grid Container ---
        self.grid_container = QFrame()
        self.grid_container.setStyleSheet("""
            QFrame {
                background-color: #FAFAFA;
                border: 4px solid #A0A0A0;
                border-radius: 6px;
            }
        """)
        
        self.grid_layout = QGridLayout(self.grid_container)
        self.grid_layout.setSpacing(2)
        self.grid_layout.setContentsMargins(4, 4, 4, 4)

        self.cells = []
        tech_font = QFont("Consolas", 16, QFont.Bold)
        tech_font.setStyleHint(QFont.Monospace)

        # Build the 16x4 distinct character boxes
        for row in range(4):
            for col in range(16):
                cell = QLabel()
                cell.setFixedSize(30, 42)
                cell.setAlignment(Qt.AlignCenter)
                cell.setFont(tech_font)
                self.grid_layout.addWidget(cell, row, col)
                self.cells.append(cell)

        # Center the LCD grid horizontally
        grid_wrapper = QHBoxLayout()
        grid_wrapper.addStretch()
        grid_wrapper.addWidget(self.grid_container)
        grid_wrapper.addStretch()
        self.layout.addLayout(grid_wrapper)

        self.layout.addSpacing(30)

        # --- BOTTOM SECTION: 4 Distinct Control Boxes ---
        regs_layout = QVBoxLayout()
        regs_layout.setSpacing(12)

        box_style = """
            QFrame {
                border: 2px solid #CCCCCC;
                border-radius: 8px;
                background-color: #E5E5E5;
            }
        """
        lbl_style = "font-weight: 900; color: #555555; font-size: 12px; letter-spacing: 1px; border: none; background: transparent;"
        badge_style = """
            QLabel {
                background-color: #FFFFFF; border: 2px solid #ADADAD;
                padding: 6px 12px; border-radius: 6px; font-weight: bold;
                font-size: 14px; color: #005A9E; font-family: monospace;
            }
        """
        lcd_style = """
            QLCDNumber {
                background-color: #1E1E1E; color: #00FF00;
                border: 3px inset #555555; border-radius: 6px;
            }
        """

        box_height = 70

        # 1. Instruction Register Box (Full Width Horizontal)
        box_ir = QFrame()
        box_ir.setStyleSheet(box_style)
        box_ir.setFixedHeight(box_height)
        ir_lay = QHBoxLayout(box_ir)
        ir_lay.setContentsMargins(20, 10, 20, 10)
        
        lbl_ir = QLabel("INSTRUCTION REGISTER (IR):")
        lbl_ir.setStyleSheet(lbl_style)
        badge_ir = QLabel("lcd_ir [7:0]")
        badge_ir.setStyleSheet(badge_style)
        self.lcd_ir = QLCDNumber()
        self.lcd_ir.setDigitCount(2)
        self.lcd_ir.setHexMode()
        self.lcd_ir.setFixedSize(90, 45)
        self.lcd_ir.setStyleSheet(lcd_style)
        self.lcd_ir.display("00")
        
        ir_lay.addWidget(lbl_ir)
        ir_lay.addStretch()
        ir_lay.addWidget(badge_ir)
        ir_lay.addSpacing(15)
        ir_lay.addWidget(self.lcd_ir)

        # 2. Data Register Box (Full Width Horizontal)
        box_dr = QFrame()
        box_dr.setStyleSheet(box_style)
        box_dr.setFixedHeight(box_height)
        dr_lay = QHBoxLayout(box_dr)
        dr_lay.setContentsMargins(20, 10, 20, 10)
        
        lbl_dr = QLabel("DATA REGISTER (DR):")
        lbl_dr.setStyleSheet(lbl_style)
        badge_dr = QLabel("lcd_dr [7:0]")
        badge_dr.setStyleSheet(badge_style)
        self.lcd_dr = QLCDNumber()
        self.lcd_dr.setDigitCount(2)
        self.lcd_dr.setHexMode()
        self.lcd_dr.setFixedSize(90, 45)
        self.lcd_dr.setStyleSheet(lcd_style)
        self.lcd_dr.display("00")
        
        dr_lay.addWidget(lbl_dr)
        dr_lay.addStretch()
        dr_lay.addWidget(badge_dr)
        dr_lay.addSpacing(15)
        dr_lay.addWidget(self.lcd_dr)

        # 3 & 4. Control Pins Layout (Two Half-Width Boxes)
        pins_lay = QHBoxLayout()
        pins_lay.setSpacing(12)

        # Box 3: RS Pin
        box_rs = QFrame()
        box_rs.setStyleSheet(box_style)
        box_rs.setFixedHeight(box_height)
        rs_lay = QHBoxLayout(box_rs)
        rs_lay.setContentsMargins(15, 10, 20, 10)
        
        lbl_rs = QLabel("RS PIN:")
        lbl_rs.setStyleSheet(lbl_style)
        badge_rs = QLabel("lcd_rs")
        badge_rs.setStyleSheet(badge_style)
        self.led_rs = VirtualLED()
        
        rs_lay.addWidget(lbl_rs)
        rs_lay.addStretch()
        rs_lay.addWidget(badge_rs)
        rs_lay.addSpacing(15)
        rs_lay.addWidget(self.led_rs)

        # Box 4: EN Pin
        box_en = QFrame()
        box_en.setStyleSheet(box_style)
        box_en.setFixedHeight(box_height)
        en_lay = QHBoxLayout(box_en)
        en_lay.setContentsMargins(15, 10, 20, 10)
        
        lbl_en = QLabel("EN PIN:")
        lbl_en.setStyleSheet(lbl_style)
        badge_en = QLabel("lcd_en")
        badge_en.setStyleSheet(badge_style)
        self.led_en = VirtualLED()
        
        en_lay.addWidget(lbl_en)
        en_lay.addStretch()
        en_lay.addWidget(badge_en)
        en_lay.addSpacing(15)
        en_lay.addWidget(self.led_en)

        pins_lay.addWidget(box_rs)
        pins_lay.addWidget(box_en)

        # Add all boxes to the main register layout
        regs_layout.addWidget(box_ir)
        regs_layout.addWidget(box_dr)
        regs_layout.addLayout(pins_lay)

        # Center the entire stack horizontally
        boxes_wrapper = QHBoxLayout()
        boxes_wrapper.addStretch()
        boxes_wrapper.addLayout(regs_layout)
        boxes_wrapper.addStretch()

        self.layout.addLayout(boxes_wrapper)
        self.layout.addStretch(2)

        # Startup Display Initialization
        boot_text = "   uP PRARAMBH      SYSTEM IDLE                                 "
        self.memory = list(boot_text.ljust(64, ' '))
        self.refresh_display()

    def update_values(self, state_dict):
        """Hardware Emulation Engine - Triggered on Clock Pulse"""
        ir_val = state_dict.get('lcd_ir', state_dict.get('dut.lcd_ir', None))
        dr_val = state_dict.get('lcd_dr', state_dict.get('dut.lcd_dr', None))
        rs_val = state_dict.get('lcd_rs', state_dict.get('dut.lcd_rs', None))
        en_val = state_dict.get('lcd_en', state_dict.get('dut.lcd_en', None))

        # Update Visuals
        if ir_val is not None and ir_val != 0xEEEE:
            self.lcd_ir.display(f"{ir_val & 0xFF:02X}")
        if dr_val is not None and dr_val != 0xEEEE:
            self.lcd_dr.display(f"{dr_val & 0xFF:02X}")
        
        rs_bit = False
        if rs_val is not None and rs_val != 0xEEEE:
            rs_bit = bool(rs_val & 1)
            self.led_rs.set_state(rs_bit)

        en_bit = False
        if en_val is not None and en_val != 0xEEEE:
            en_bit = bool(en_val & 1)
            self.led_en.set_state(en_bit)

            # === HD44780 SYNCHRONOUS LOGIC ===
            # The LCD only executes a command when the Enable (EN) pin pulses HIGH!
            if en_bit and not self.prev_en:
                if not rs_bit: 
                    # --- Instruction Mode (RS = 0) ---
                    cmd = ir_val & 0xFF
                    if cmd == 0x01: # 0x01: Clear Display
                        self.memory = [' '] * 64
                        self.cursor = 0
                    elif (cmd & 0x80) == 0x80: # 0x80 to 0xBF: Set Cursor Address
                        self.cursor = cmd & 0x3F
                else: 
                    # --- Data Mode (RS = 1) ---
                    data = dr_val & 0xFF
                    char = chr(data) if 32 <= data <= 126 else '?'
                    if self.cursor < 64:
                        self.memory[self.cursor] = char
                        self.cursor += 1
                
                self.refresh_display()

            self.prev_en = en_bit

    def refresh_display(self):
        """Draws the memory array to the grid and visually highlights the cursor."""
        for i in range(64):
            self.cells[i].setText(self.memory[i])
            if i == self.cursor:
                # Invert colors to show where the hardware cursor is currently pointing!
                self.cells[i].setStyleSheet("""
                    QLabel { background-color: #00FFCC; color: #1A1E24; border-radius: 2px; }
                """)
            else:
                self.cells[i].setStyleSheet("""
                    QLabel { background-color: #1A1E24; color: #00FFCC; border-radius: 2px; }
                """)

    def show_help(self):
        msg = QMessageBox(self)
        msg.setWindowTitle("Learner Guide: HD44780 LCD Emulator")
        msg.setText(
            "<b>HD44780 Character LCD Emulator</b><br><br>"
            "This widget fully emulates a standard hardware LCD controller! It uses internal memory and a moving cursor. It <b>only</b> updates when the Enable (EN) pin is pulsed high.<br><br>"
            "<b>Required Verilog Outputs:</b><br>"
            "• <code>lcd_ir [7:0]</code> : Instruction Register<br>"
            "• <code>lcd_dr [7:0]</code> : Data Register<br>"
            "• <code>lcd_rs</code> : Register Select (0 = Instruction, 1 = Data)<br>"
            "• <code>lcd_en</code> : Enable Pin (Must pulse 0 → 1 to execute!)<br><br>"
            "<b>Basic Instructions (RS=0, Pulse EN):</b><br>"
            "• <code>0x01</code> : Clear Display & Reset Cursor<br>"
            "• <code>0x80 + [0 to 63]</code> : Move Cursor to a specific position<br><br>"
            "<b>Writing Text (RS=1, Pulse EN):</b><br>"
            "Set DR to an ASCII value, set RS=1, and pulse EN. The character will print and the cursor will auto-increment!"
        )
        msg.exec_()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    test_window = QWidget()
    test_window.setStyleSheet("background-color: #FFFFFF;")
    layout = QVBoxLayout(test_window)
    module = CharDisplayView()
    layout.addWidget(module)
    test_window.setWindowTitle("Test: HD44780 Emulation")
    test_window.resize(650, 750)
    test_window.show()
    sys.exit(app.exec_())