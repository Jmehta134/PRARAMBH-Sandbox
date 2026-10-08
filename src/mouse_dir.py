import sys
import math
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, 
    QLCDNumber, QApplication, QMessageBox, QGridLayout
)
from PyQt5.QtGui import QFont, QPainter, QPen, QColor, QBrush, QPolygonF
from PyQt5.QtCore import Qt, pyqtSignal, QPointF, QTimer

# =============================================================================
# COMPONENT: Custom Painted Mouse Sensor Canvas
# =============================================================================
class MouseSensorCanvas(QWidget):
    def __init__(self):
        super().__init__()
        self.setFixedSize(340, 340)
        self.active_dir = -1  

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        rect = self.rect()
        center = QPointF(rect.width() / 2, rect.height() / 2)
        
        color_lit_fill = QColor("#00E5FF")
        color_lit_line = QColor("#008899")
        color_dim_fill = QColor("#222222")
        color_dim_line = QColor("#111111")

        # --- Draw 8 Directional Arrows ---
        for i in range(8):
            painter.save()
            painter.translate(center)
            painter.rotate(-90 + i * 45)

            is_corner = (i % 2 != 0)
            length = 210 if is_corner else 150
            
            # UPGRADED ARROW GEOMETRY: Bolder shaft and broader head
            base_offset = 35
            shaft_half_width = 14  # Increased from 8 (Shaft is now 28px wide)
            head_half_width = 28   # Increased from 18 (Head is now 56px wide)
            head_length = 35       # Increased from 25 to match the wider proportions
            
            arrow_poly = QPolygonF([
                QPointF(base_offset, -shaft_half_width),
                QPointF(length - head_length, -shaft_half_width),
                QPointF(length - head_length, -head_half_width),
                QPointF(length, 0),
                QPointF(length - head_length, head_half_width),
                QPointF(length - head_length, shaft_half_width),
                QPointF(base_offset, shaft_half_width)
            ])

            if self.active_dir == i:
                painter.setBrush(QBrush(color_lit_fill))
                painter.setPen(QPen(color_lit_line, 2))
            else:
                painter.setBrush(QBrush(color_dim_fill))
                painter.setPen(QPen(color_dim_line, 2))

            painter.drawPolygon(arrow_poly)
            painter.restore()

        # --- Draw Center Resting Circle ---
        if self.active_dir == -1:
            painter.setBrush(QBrush(color_lit_fill))
            painter.setPen(QPen(color_lit_line, 3))
        else:
            painter.setBrush(QBrush(color_dim_fill))
            painter.setPen(QPen(color_dim_line, 3))

        painter.drawEllipse(center, 22, 22)


# =============================================================================
# MAIN PANE: Mouse Direction Sensor View
# =============================================================================
class MouseDirectionView(QWidget):
    mouse_updated = pyqtSignal(str, int)

    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(15, 15, 15, 15)

        title = QLabel("HARDWARE MOUSE SENSOR PANEL")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("""
            font-weight: 900; 
            color: #333333; 
            font-size: 18px; 
            letter-spacing: 1.5px;
            margin-bottom: 5px;
        """)
        self.layout.addWidget(title)
        
        self.layout.addStretch(1)

        # --- Top Section: Sensor Bezel ---
        bezel = QFrame()
        bezel.setStyleSheet("""
            QFrame {
                background-color: #151515;
                border: 3px inset #333333;
                border-radius: 8px;
            }
        """)
        bezel_layout = QVBoxLayout(bezel)
        bezel_layout.setContentsMargins(15, 15, 15, 15)
        
        self.canvas = MouseSensorCanvas()
        bezel_layout.addWidget(self.canvas, alignment=Qt.AlignCenter)
        
        bezel_wrapper = QHBoxLayout()
        bezel_wrapper.addStretch()
        bezel_wrapper.addWidget(bezel)
        bezel_wrapper.addStretch()
        
        self.layout.addLayout(bezel_wrapper)
        self.layout.addSpacing(25)

        # --- Bottom Section: Control Box ---
        control_box = QFrame()
        control_box.setStyleSheet("""
            QFrame {
                border: 2px solid #CCCCCC;
                border-radius: 8px;
                background-color: #E5E5E5;
            }
        """)
        
        control_lay = QGridLayout(control_box)
        control_lay.setContentsMargins(30, 20, 30, 20)
        control_lay.setHorizontalSpacing(50)
        control_lay.setVerticalSpacing(10)

        lbl_style = "font-weight: 900; color: #555555; font-size: 13px; letter-spacing: 1px; border: none; background: transparent;"
        
        target_lbl = QLabel("DRIVING HARDWARE REGISTER:")
        target_lbl.setStyleSheet(lbl_style)
        target_lbl.setAlignment(Qt.AlignCenter | Qt.AlignBottom)
        
        readout_lbl = QLabel("CURRENT HEX VALUE:")
        readout_lbl.setStyleSheet(lbl_style)
        readout_lbl.setAlignment(Qt.AlignCenter | Qt.AlignBottom)

        reg_name_lbl = QLabel("mouse_dir [7:0]")
        reg_name_lbl.setStyleSheet("""
            background-color: #FFFFFF; border: 2px solid #ADADAD;
            padding: 8px 12px; border-radius: 6px; font-weight: bold;
            font-size: 15px; color: #005A9E; font-family: monospace;
        """)
        reg_name_lbl.setAlignment(Qt.AlignCenter)
        
        self.lcd_val = QLCDNumber()
        self.lcd_val.setDigitCount(2)
        self.lcd_val.setHexMode()
        self.lcd_val.setFixedSize(100, 50)
        self.lcd_val.setStyleSheet("""
            QLCDNumber {
                background-color: #1E1E1E; 
                color: #00FF00;
                border: 3px inset #555555; 
                border-radius: 6px;
            }
        """)
        self.lcd_val.display("00")

        control_lay.addWidget(target_lbl, 0, 0)
        control_lay.addWidget(readout_lbl, 0, 1)
        control_lay.addWidget(reg_name_lbl, 1, 0, alignment=Qt.AlignTop | Qt.AlignHCenter)
        control_lay.addWidget(self.lcd_val, 1, 1, alignment=Qt.AlignTop | Qt.AlignHCenter)
        
        wrapper_bottom = QHBoxLayout()
        wrapper_bottom.addStretch()
        wrapper_bottom.addWidget(control_box)
        wrapper_bottom.addStretch()
        
        self.layout.addLayout(wrapper_bottom)
        self.layout.addStretch(2)

        # --- Mouse Tracking Engine ---
        self.current_val = 0
        from PyQt5.QtGui import QCursor
        self.last_pos = QCursor.pos()
        
        self.tracker_timer = QTimer(self)
        self.tracker_timer.timeout.connect(self.poll_mouse)
        self.tracker_timer.start(50)

    def poll_mouse(self):
        from PyQt5.QtGui import QCursor
        pos = QCursor.pos()
        
        dx = pos.x() - self.last_pos.x()
        dy = pos.y() - self.last_pos.y()
        
        distance_sq = dx**2 + dy**2
        
        dir_index = -1
        val = 0
        
        if distance_sq > 16:  
            angle = math.degrees(math.atan2(dy, dx))
            sector = round(angle / 45.0) % 8
            dir_index = (sector + 2) % 8
            val = 1 << dir_index

        self.last_pos = pos

        if val != self.current_val:
            self.current_val = val
            self.canvas.active_dir = dir_index
            self.canvas.update()
            
            self.lcd_val.display(f"{self.current_val:02X}")
            self.mouse_updated.emit("mouse_dir", self.current_val)

    def show_help(self):
        msg = QMessageBox(self)
        msg.setWindowTitle("Learner Guide: Mouse Sensor")
        msg.setText(
            "<b>Hardware Mouse Direction Sensor</b><br><br>"
            "This input module tracks your physical computer mouse and maps its movement vector directly into your Verilog design.<br><br>"
            "<b>Input Port Driven:</b><br>"
            "• <code>mouse_dir</code> : 8-bit input bus ([7:0])<br><br>"
            "<b>Direction Mapping (Clockwise):</b><br>"
            "• Bit 0 (0x01) : North (Up)<br>"
            "• Bit 1 (0x02) : North-East<br>"
            "• Bit 2 (0x04) : East (Right)<br>"
            "• Bit 3 (0x08) : South-East<br>"
            "• Bit 4 (0x10) : South (Down)<br>"
            "• Bit 5 (0x20) : South-West<br>"
            "• Bit 6 (0x40) : West (Left)<br>"
            "• Bit 7 (0x80) : North-West<br><br>"
            "<i>Note: If the mouse rests completely, the register zeroes out (0x00) and the center ring illuminates.</i>"
        )
        msg.exec_()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    test_window = QWidget()
    test_window.setStyleSheet("background-color: #FAFAFA;")
    layout = QVBoxLayout(test_window)
    module = MouseDirectionView()
    layout.addWidget(module)
    test_window.setWindowTitle("Test: Mouse Direction Sensor")
    test_window.resize(600, 750)
    test_window.show()
    sys.exit(app.exec_())