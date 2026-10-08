import sys
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, 
    QLCDNumber, QApplication, QSlider, QLineEdit, QComboBox
)
from PyQt5.QtGui import QFont, QRegExpValidator, QPainter, QPen, QColor, QBrush
from PyQt5.QtCore import Qt, pyqtSignal, QRegExp, QPoint

class SliderADCView(QWidget):
    # Emits (target_port_name, integer_value) whenever the slider moves
    adc_updated = pyqtSignal(str, int)

    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(15, 15, 15, 15)

        # --- Standardized Pane Header (Pinned to Top) ---
        title = QLabel("SLIDER ADC (ANALOG INPUT)")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("""
            font-weight: 900; 
            color: #333333; 
            font-size: 18px; 
            letter-spacing: 1.5px;
            margin-bottom: 5px;
        """)
        self.layout.addWidget(title)
        self.layout.addSpacing(15)

        # Content Wrapper to center the UI elements vertically
        content_vbox = QVBoxLayout()

        # --- MAIN INTERFACE: Slider + Controls ---
        main_hbox = QHBoxLayout()
        main_hbox.setSpacing(50) # Increased spacing slightly to give room for diagram lines

        # 1. LEFT SIDE: The Vertical Analog Slider in a Grey Box
        self.slider_box = QFrame()
        self.slider_box.setStyleSheet("""
            QFrame {
                border: 2px solid #CCCCCC;
                border-radius: 8px;
                background-color: #E5E5E5; 
            }
        """)
        slider_box_lay = QVBoxLayout(self.slider_box)
        slider_box_lay.setContentsMargins(20, 20, 20, 20)

        self.slider = QSlider(Qt.Vertical)
        self.slider.setMinimum(0)
        self.slider.setMaximum(1000) 
        self.slider.setValue(0)
        self.slider.setTickPosition(QSlider.TicksBothSides)
        self.slider.setTickInterval(100)
        self.slider.setMinimumHeight(350)
        
        # Kakkoii Illuminated Slider Theme with Wide Industrial Handle
        self.slider.setStyleSheet("""
            QSlider {
                min-width: 80px; 
            }
            QSlider::groove:vertical {
                background: #1A1E24;
                width: 16px;
                border-radius: 8px;
                border: 2px solid #333333;
            }
            QSlider::handle:vertical {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #CCCCCC, stop:0.5 #FFFFFF, stop:1 #CCCCCC);
                height: 22px;
                margin: 0 -30px; 
                border-radius: 4px;
                border: 3px solid #00FF00; /* Hardware Green */
            }
            QSlider::handle:vertical:hover {
                background: #FFFFFF;
                border: 3px solid #00E5FF;
            }
            QSlider::add-page:vertical {
                background: #1A1E24; 
                border-radius: 8px;
            }
            QSlider::sub-page:vertical {
                background: #007A8C; 
                border-radius: 8px;
            }
        """)
        self.slider.valueChanged.connect(self.calculate_and_emit)
        
        slider_box_lay.addWidget(self.slider, alignment=Qt.AlignCenter)
        
        slider_wrap = QVBoxLayout()
        slider_wrap.addWidget(self.slider_box, alignment=Qt.AlignCenter)
        main_hbox.addLayout(slider_wrap)

        # 2. RIGHT SIDE: Settings & Readout
        right_vbox = QVBoxLayout()
        # Align left so diagram lines can neatly plug into them
        right_vbox.setAlignment(Qt.AlignLeft) 

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

        # --- Top: Max Input (Hex) --- Stacked style like the Gauge
        max_vbox = QVBoxLayout()
        max_vbox.setSpacing(5)
        lbl_max = QLabel("MAX (HEX)")
        lbl_max.setStyleSheet(lbl_style)
        self.input_max = QLineEdit("FF")
        self.input_max.setValidator(hex_validator)
        self.input_max.setStyleSheet(input_style)
        self.input_max.setFixedWidth(85)
        self.input_max.setAlignment(Qt.AlignCenter)
        self.input_max.textChanged.connect(self.calculate_and_emit)
        
        max_vbox.addWidget(lbl_max)
        max_vbox.addWidget(self.input_max)
        right_vbox.addLayout(max_vbox)

        right_vbox.addStretch(1)

        # --- Middle: Target Selector & Hex Readout Box (Grey) ---
        center_box = QFrame()
        center_box.setStyleSheet("""
            QFrame {
                border: 2px solid #CCCCCC;
                border-radius: 8px;
                background-color: #E5E5E5; 
            }
        """)
        center_lay = QVBoxLayout(center_box)
        center_lay.setContentsMargins(20, 20, 20, 20)
        center_lay.setSpacing(15)

        target_lbl = QLabel("TARGET INPUT PORT:")
        target_lbl.setStyleSheet(lbl_style + "border: none; background: transparent;")
        
        self.combo_target = QComboBox()
        self.combo_target.addItem("None")
        self.combo_target.setStyleSheet("""
            QComboBox {
                background-color: #FFFFFF; border: 2px solid #ADADAD;
                padding: 6px 10px; border-radius: 6px; font-weight: bold;
                font-size: 14px; color: #333333;
            }
        """)
        self.combo_target.currentTextChanged.connect(self.calculate_and_emit)

        readout_lbl = QLabel("CURRENT DIGITAL VALUE:")
        readout_lbl.setStyleSheet(lbl_style + "border: none; background: transparent;")
        
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

        center_lay.addWidget(target_lbl)
        center_lay.addWidget(self.combo_target)
        center_lay.addSpacing(15)
        center_lay.addWidget(readout_lbl)
        center_lay.addWidget(self.lcd_val, alignment=Qt.AlignCenter)
        
        right_vbox.addWidget(center_box)

        right_vbox.addStretch(1)

        # --- Bottom: Min Input (Hex) --- Stacked style like the Gauge
        min_vbox = QVBoxLayout()
        min_vbox.setSpacing(5)
        lbl_min = QLabel("MIN (HEX)")
        lbl_min.setStyleSheet(lbl_style)
        self.input_min = QLineEdit("00")
        self.input_min.setValidator(hex_validator)
        self.input_min.setStyleSheet(input_style)
        self.input_min.setFixedWidth(85)
        self.input_min.setAlignment(Qt.AlignCenter)
        self.input_min.textChanged.connect(self.calculate_and_emit)
        
        min_vbox.addWidget(lbl_min)
        min_vbox.addWidget(self.input_min)
        right_vbox.addLayout(min_vbox)

        wrapper_right = QHBoxLayout()
        wrapper_right.addLayout(right_vbox)
        wrapper_right.addStretch()

        main_hbox.addLayout(wrapper_right)
        main_hbox.setStretch(0, 1) 
        main_hbox.setStretch(1, 1) 

        content_vbox.addLayout(main_hbox)
        content_vbox.addStretch(1)

        self.layout.addLayout(content_vbox)

    def paintEvent(self, event):
        """Overrides paintEvent to draw orthogonal schematic lines connecting the slider to the inputs."""
        # Ensure widgets have geometry assigned before drawing
        if not hasattr(self, 'slider_box') or not hasattr(self, 'input_max'):
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        pen = QPen(QColor("#A0A0A0"), 2, Qt.DashLine)
        painter.setPen(pen)
        
        # 1. Acquire global coordinates mapped to this widget's coordinate space
        # Slider Top Right (Mapping to approx upper bound of the track)
        p_slider_top = self.slider_box.mapTo(self, QPoint(self.slider_box.width(), 40))
        # Slider Bottom Right (Mapping to approx lower bound of the track)
        p_slider_bot = self.slider_box.mapTo(self, QPoint(self.slider_box.width(), self.slider_box.height() - 40))
        
        # Input Left Centers
        p_max_in = self.input_max.mapTo(self, QPoint(0, self.input_max.height() // 2))
        p_min_in = self.input_min.mapTo(self, QPoint(0, self.input_min.height() // 2))
        
        # 2. Draw MAX Line (Orthogonal Routing: Right -> Down/Up -> Right)
        mid_x = p_slider_top.x() + 25  # Route 25px out from the slider box
        painter.drawLine(p_slider_top, QPoint(mid_x, p_slider_top.y()))
        painter.drawLine(QPoint(mid_x, p_slider_top.y()), QPoint(mid_x, p_max_in.y()))
        painter.drawLine(QPoint(mid_x, p_max_in.y()), p_max_in)
        
        # 3. Draw MIN Line (Orthogonal Routing: Right -> Down/Up -> Right)
        painter.drawLine(p_slider_bot, QPoint(mid_x, p_slider_bot.y()))
        painter.drawLine(QPoint(mid_x, p_slider_bot.y()), QPoint(mid_x, p_min_in.y()))
        painter.drawLine(QPoint(mid_x, p_min_in.y()), p_min_in)

        # 4. Draw Glowing Anchor Dots on the Slider Casing
        painter.setBrush(QBrush(QColor("#00FF00")))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(p_slider_top, 4, 4)
        painter.drawEllipse(p_slider_bot, 4, 4)

    def set_available_inputs(self, inputs):
        """Populates the dropdown with available Verilog input ports."""
        current = self.combo_target.currentText()
        self.combo_target.blockSignals(True)
        self.combo_target.clear()
        self.combo_target.addItem("None")
        
        clean_signals = [s.replace("dut.", "") for s in inputs]
        self.combo_target.addItems(clean_signals)
        
        if current in clean_signals:
            self.combo_target.setCurrentText(current)
            
        self.combo_target.blockSignals(False)

    def calculate_and_emit(self):
        """Maps the 0-1000 slider position to the Min/Max Hex range and emits the value."""
        try:
            min_val = int(self.input_min.text() or "0", 16)
            max_val = int(self.input_max.text() or "0", 16)
        except ValueError:
            return

        pct = self.slider.value() / 1000.0
        current_val = int(min_val + (max_val - min_val) * pct)
        
        if current_val < 0:
            self.lcd_val.display(f"{current_val & 0xFFFF:04X}")
        else:
            self.lcd_val.display(f"{current_val:04X}")

        target = self.combo_target.currentText()
        if target != "None":
            self.adc_updated.emit(target, current_val)

    def show_help(self):
        from PyQt5.QtWidgets import QMessageBox
        msg = QMessageBox(self)
        msg.setWindowTitle("Learner Guide: Slider ADC")
        msg.setText(
            "<b>Analog-to-Digital Converter Emulator</b><br><br>"
            "Use this slider to smoothly inject dynamic values into any hardware input port.<br><br>"
            "<b>1. Set Range:</b> Type your minimum and maximum values (in Hexadecimal) into the top and bottom boxes.<br>"
            "<b>2. Select Target:</b> Choose which Verilog <code>input</code> wire you want to inject the data into.<br>"
            "<b>3. Slide:</b> Click and drag the slider, or use the <b>Up/Down Arrow Keys</b> to increment the value smoothly.<br><br>"
            "<i>Note: The display shows the converted Hexadecimal value that is currently being injected into the Simulation Engine.</i>"
        )
        msg.exec_()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    test_window = QWidget()
    test_window.setStyleSheet("background-color: #FAFAFA;")
    layout = QVBoxLayout(test_window)
    module = SliderADCView()
    layout.addWidget(module)
    test_window.setWindowTitle("Test: Slider ADC")
    test_window.resize(600, 600)
    test_window.show()
    sys.exit(app.exec_())