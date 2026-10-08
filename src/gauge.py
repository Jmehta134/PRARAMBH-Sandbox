import sys
import math
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, 
    QLCDNumber, QApplication, QLineEdit, QComboBox, QMessageBox, QPushButton, QGridLayout
)
from PyQt5.QtGui import QFont, QRegExpValidator, QPainter, QPen, QColor, QBrush, QPainterPath
from PyQt5.QtCore import Qt, QRegExp, QRectF, QPointF

# =============================================================================
# COMPONENT: Custom Painted Analog Gauge with Diagram Lines
# =============================================================================
class AnalogGaugeWidget(QWidget):
    def __init__(self):
        super().__init__()
        # Tuned to be prominent but not overly massive
        self.setMinimumSize(480, 380)
        self.min_val = 0
        self.max_val = 255
        self.current_val = 0

    def update_data(self, current, minimum, maximum):
        self.current_val = current
        self.min_val = minimum
        self.max_val = maximum
        self.update() # Triggers paintEvent

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        rect = self.rect()
        center = QPointF(rect.width() / 2, rect.height() / 2 - 20)
        
        # Track size calculation adjusted for the new widget bounds
        track_size = min(rect.width(), rect.height()) - 90
        
        # --- 1. Outer Grey Casing (Cropped Circle) ---
        case_padding = 24
        case_size = track_size + (case_padding * 2)
        case_rect = QRectF(center.x() - case_size/2, center.y() - case_size/2, case_size, case_size)
        
        case_path = QPainterPath()
        case_path.arcMoveTo(case_rect, -45)
        case_path.arcTo(case_rect, -45, 270)
        case_path.closeSubpath() 
        
        painter.setBrush(QBrush(QColor("#E5E5E5")))
        painter.setPen(QPen(QColor("#CCCCCC"), 3))
        painter.drawPath(case_path)

        # --- 2. Dark Inner Dial ---
        dial_padding = 10
        dial_size = track_size + (dial_padding * 2)
        dial_rect = QRectF(center.x() - dial_size/2, center.y() - dial_size/2, dial_size, dial_size)
        
        dial_path = QPainterPath()
        dial_path.arcMoveTo(dial_rect, -45)
        dial_path.arcTo(dial_rect, -45, 270)
        dial_path.closeSubpath()
        
        painter.setBrush(QBrush(QColor("#1A1E24")))
        painter.setPen(QPen(QColor("#333333"), 2))
        painter.drawPath(dial_path)

        # --- 3. Glowing Thickening Arc ---
        track_rect = QRectF(center.x() - track_size/2, center.y() - track_size/2, track_size, track_size)
        start_angle = 225
        span = 270 
        steps = span
        
        min_thick = 2
        max_thick = 18 
        
        for i in range(steps):
            current_angle = start_angle - i
            thickness = min_thick + (max_thick - min_thick) * (i / steps)
            
            pen = QPen(QColor("#00FF00"))
            pen.setWidthF(thickness)
            pen.setCapStyle(Qt.FlatCap)
            painter.setPen(pen)
            
            painter.drawArc(track_rect, int(current_angle * 16), int(-2 * 16))

        # --- 4. Schematic Diagram Leader Lines ---
        painter.setPen(QPen(QColor("#A0A0A0"), 2, Qt.DashLine))
        
        min_x = center.x() + (case_size/2) * math.cos(math.radians(225))
        min_y = center.y() - (case_size/2) * math.sin(math.radians(225))
        
        max_x = center.x() + (case_size/2) * math.cos(math.radians(-45))
        max_y = center.y() - (case_size/2) * math.sin(math.radians(-45))
        
        target_y = rect.height() - 40

        # MIN Line (Left)
        painter.drawLine(QPointF(min_x, min_y), QPointF(min_x - 35, min_y))
        painter.drawLine(QPointF(min_x - 35, min_y), QPointF(20, target_y))
        
        # MAX Line (Right)
        painter.drawLine(QPointF(max_x, max_y), QPointF(max_x + 35, max_y))
        painter.drawLine(QPointF(max_x + 35, max_y), QPointF(rect.width() - 20, target_y))

        # Glowing Anchor Dots
        painter.setBrush(QBrush(QColor("#00FF00")))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(QPointF(min_x, min_y), 5, 5)
        painter.drawEllipse(QPointF(max_x, max_y), 5, 5)

        # --- 5. Needle Logic & Drawing ---
        if self.current_val < self.min_val or self.current_val > self.max_val:
            val = self.max_val
        else:
            val = self.current_val
            
        if self.max_val <= self.min_val:
            pct = 1.0 
        else:
            pct = (val - self.min_val) / (self.max_val - self.min_val)
            
        needle_angle_deg = start_angle - (pct * span)
        needle_angle_rad = math.radians(needle_angle_deg)
        
        needle_len = track_size / 2 - 12
        end_x = center.x() + needle_len * math.cos(needle_angle_rad)
        end_y = center.y() - needle_len * math.sin(needle_angle_rad) 
        
        painter.setPen(QPen(QColor("#FF4444"), 5, Qt.SolidLine, Qt.RoundCap))
        painter.drawLine(center, QPointF(end_x, end_y))
        
        # --- 6. Center Hub ---
        painter.setBrush(QBrush(QColor("#FAFAFA")))
        painter.setPen(QPen(QColor("#A0A0A0"), 4))
        painter.drawEllipse(center, 14, 14)


# =============================================================================
# MAIN PANE: Gauge ADC View
# =============================================================================
class GaugeADCView(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(15, 15, 15, 15)

        # --- Header ---
        title = QLabel("GAUGE ADC (ANALOG OUTPUT)")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("""
            font-weight: 900; 
            color: #333333; 
            font-size: 18px; 
            letter-spacing: 1.5px;
            margin-bottom: 5px;
        """)
        self.layout.addWidget(title)
        self.layout.addSpacing(10)

        content_vbox = QVBoxLayout()
        content_vbox.addStretch(1)

        # --- Top Section: Gauge & Min/Max Inputs ---
        gauge_hbox = QHBoxLayout()
        gauge_hbox.setSpacing(0) 
        
        input_style = """
            QLineEdit {
                background-color: #FFFFFF;
                border: 2px solid #CCCCCC;
                border-radius: 6px;
                padding: 6px;
                font-weight: 900;
                font-family: monospace;
                font-size: 16px;
                color: #005A9E;
            }
        """
        lbl_style = "font-weight: 900; color: #555555; font-size: 13px; letter-spacing: 1px;"
        hex_validator = QRegExpValidator(QRegExp("[0-9A-Fa-f]{1,8}"))

        # MIN Input (Left Side)
        min_vbox = QVBoxLayout()
        min_vbox.setAlignment(Qt.AlignBottom)
        lbl_min = QLabel("MIN (HEX)")
        lbl_min.setStyleSheet(lbl_style)
        lbl_min.setAlignment(Qt.AlignCenter)
        self.input_min = QLineEdit("00")
        self.input_min.setValidator(hex_validator)
        self.input_min.setStyleSheet(input_style)
        self.input_min.setFixedWidth(85)
        self.input_min.setAlignment(Qt.AlignCenter)
        self.input_min.textChanged.connect(self.trigger_gauge_update)
        min_vbox.addWidget(lbl_min)
        min_vbox.addWidget(self.input_min)

        # Custom Gauge Widget (Center)
        self.gauge = AnalogGaugeWidget()
        
        # MAX Input (Right Side)
        max_vbox = QVBoxLayout()
        max_vbox.setAlignment(Qt.AlignBottom)
        lbl_max = QLabel("MAX (HEX)")
        lbl_max.setStyleSheet(lbl_style)
        lbl_max.setAlignment(Qt.AlignCenter)
        self.input_max = QLineEdit("FF")
        self.input_max.setValidator(hex_validator)
        self.input_max.setStyleSheet(input_style)
        self.input_max.setFixedWidth(85)
        self.input_max.setAlignment(Qt.AlignCenter)
        self.input_max.textChanged.connect(self.trigger_gauge_update)
        max_vbox.addWidget(lbl_max)
        max_vbox.addWidget(self.input_max)

        gauge_hbox.addStretch(1)
        gauge_hbox.addLayout(min_vbox)
        gauge_hbox.addWidget(self.gauge, stretch=4) 
        gauge_hbox.addLayout(max_vbox)
        gauge_hbox.addStretch(1)

        content_vbox.addLayout(gauge_hbox)
        content_vbox.addSpacing(20)

        # --- Bottom Section: Grid Layout Control Box ---
        center_box = QFrame()
        center_box.setStyleSheet("""
            QFrame {
                border: 2px solid #CCCCCC;
                border-radius: 8px;
                background-color: #E5E5E5;
            }
        """)
        
        # QGridLayout enforces perfect baseline alignment for rows
        center_lay = QGridLayout(center_box)
        center_lay.setContentsMargins(25, 20, 25, 20)
        center_lay.setHorizontalSpacing(40)
        center_lay.setVerticalSpacing(10)

        # Labels (Row 0)
        target_lbl = QLabel("MONITOR OUTPUT PORT:")
        target_lbl.setStyleSheet(lbl_style + "border: none; background: transparent;")
        target_lbl.setAlignment(Qt.AlignCenter | Qt.AlignBottom)
        
        readout_lbl = QLabel("CURRENT DIGITAL VALUE:")
        readout_lbl.setStyleSheet(lbl_style + "border: none; background: transparent;")
        readout_lbl.setAlignment(Qt.AlignCenter | Qt.AlignBottom)

        # Widgets (Row 1)
        self.combo_target = QComboBox()
        self.combo_target.addItem("None")
        self.combo_target.setStyleSheet("""
            QComboBox {
                background-color: #FFFFFF; border: 2px solid #ADADAD;
                padding: 6px 10px; border-radius: 6px; font-weight: bold;
                font-size: 14px; color: #333333;
                min-width: 150px;
            }
        """)
        self.combo_target.currentTextChanged.connect(self.trigger_gauge_update)
        
        self.lcd_val = QLCDNumber()
        self.lcd_val.setDigitCount(4)
        self.lcd_val.setHexMode()
        self.lcd_val.setFixedSize(160, 65)
        self.lcd_val.setStyleSheet("""
            QLCDNumber {
                background-color: #1E1E1E; 
                color: #00FF00;
                border: 3px inset #555555; 
                border-radius: 6px;
            }
        """)
        self.lcd_val.display("0000")

        # Adding to grid
        center_lay.addWidget(target_lbl, 0, 0)
        center_lay.addWidget(readout_lbl, 0, 1)
        center_lay.addWidget(self.combo_target, 1, 0, alignment=Qt.AlignTop | Qt.AlignHCenter)
        center_lay.addWidget(self.lcd_val, 1, 1, alignment=Qt.AlignTop | Qt.AlignHCenter)
        
        wrapper_bottom = QHBoxLayout()
        wrapper_bottom.addStretch()
        wrapper_bottom.addWidget(center_box)
        wrapper_bottom.addStretch()
        
        content_vbox.addLayout(wrapper_bottom)
        content_vbox.addStretch(1)

        self.layout.addLayout(content_vbox)

        # State storage
        self.latest_hardware_val = 0

    def set_available_signals(self, signals):
        """Populates the dropdown with available Verilog output ports."""
        current = self.combo_target.currentText()
        self.combo_target.blockSignals(True)
        self.combo_target.clear()
        self.combo_target.addItem("None")
        
        clean_signals = [s.replace("dut.", "") for s in signals]
        self.combo_target.addItems(clean_signals)
        
        if current in clean_signals:
            self.combo_target.setCurrentText(current)
            
        self.combo_target.blockSignals(False)

    def update_values(self, state_dict):
        """Called automatically by main.py on every clock pulse."""
        target = self.combo_target.currentText()
        if target == "None":
            return
            
        val = state_dict.get(target, state_dict.get(f"dut.{target}", None))
        if val is not None and val != 0xEEEE:
            self.latest_hardware_val = val
            self.trigger_gauge_update()

    def trigger_gauge_update(self):
        """Reads user constraints and updates the gauge and LCD visuals."""
        try:
            min_val = int(self.input_min.text() or "0", 16)
            max_val = int(self.input_max.text() or "0", 16)
        except ValueError:
            return

        if self.latest_hardware_val < 0:
            self.lcd_val.display(f"{self.latest_hardware_val & 0xFFFF:04X}")
        else:
            self.lcd_val.display(f"{self.latest_hardware_val:04X}")
            
        self.gauge.update_data(self.latest_hardware_val, min_val, max_val)

    def show_help(self):
        msg = QMessageBox(self)
        msg.setWindowTitle("Learner Guide: Gauge ADC")
        msg.setText(
            "<b>Analog Output Monitor</b><br><br>"
            "This module acts like an analog dashboard gauge to visualize Verilog outputs.<br><br>"
            "<b>1. Select Output:</b> Choose the hardware register you want to monitor.<br>"
            "<b>2. Set Bounds:</b> Enter a Minimum and Maximum value in Hexadecimal to set the gauge's sweep.<br>"
            "<b>3. Out of Bounds:</b> If the hardware outputs a value lower than your Min or higher than your Max, the needle will peg to the absolute maximum position."
        )
        msg.exec_()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    test_window = QWidget()
    test_window.setStyleSheet("background-color: #FAFAFA;")
    layout = QVBoxLayout(test_window)
    module = GaugeADCView()
    layout.addWidget(module)
    test_window.setWindowTitle("Test: Gauge ADC")
    test_window.resize(650, 700) 
    test_window.show()
    sys.exit(app.exec_())