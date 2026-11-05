from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QLineEdit, QPushButton, QMessageBox, QSizePolicy
)
from PyQt5.QtGui import (
    QRegExpValidator, QPainter, QPainterPath, QPen, QColor
)
from PyQt5.QtCore import Qt, pyqtSignal, QRegExp, QTimer


class SignalWire(QWidget):
    """Single continuous U-shaped signal wire."""

    def __init__(self, parent=None, input_widget=None, label_widget=None):
        super().__init__(parent)

        self.input_widget = input_widget
        self.label_widget = label_widget
        self.active = False

        self.setFixedWidth(48)
        self.setSizePolicy(
            QSizePolicy.Fixed,
            QSizePolicy.Expanding
        )
        self.setAttribute(Qt.WA_TransparentForMouseEvents)

    def set_active(self, active):
        self.active = active
        self.update()

    def paintEvent(self, event):
        if not self.input_widget or not self.label_widget:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        parent = self.parentWidget()

        # Find the exact left-edge centre of each connected object.
        input_origin = self.input_widget.mapTo(
            parent, self.input_widget.rect().topLeft()
        )

        label_origin = self.label_widget.mapTo(
            parent, self.label_widget.rect().topLeft()
        )

        start = self.mapFrom(
            parent,
            input_origin + self.input_widget.rect().center()
            - self.input_widget.rect().topLeft()
        )

        end = self.mapFrom(
            parent,
            label_origin + self.label_widget.rect().center()
            - self.label_widget.rect().topLeft()
        )

        # Align both endpoints with the left edges.
        start.setX(
            self.mapFrom(parent, input_origin).x()
        )
        end.setX(
            self.mapFrom(parent, label_origin).x()
        )

        left_x = 7
        radius = min(
            17,
            max(8, (end.y() - start.y()) / 4)
        )

        path = QPainterPath()
        path.moveTo(start)
        path.lineTo(left_x + radius, start.y())

        path.quadTo(
            left_x, start.y(),
            left_x, start.y() + radius
        )

        path.lineTo(
            left_x, end.y() - radius
        )

        path.quadTo(
            left_x, end.y(),
            left_x + radius, end.y()
        )

        path.lineTo(end)

        color = (
            QColor("#45F5A5")
            if self.active
            else QColor("#344357")
        )

        pen = QPen(color)
        pen.setWidth(11)
        pen.setCapStyle(Qt.RoundCap)
        pen.setJoinStyle(Qt.RoundJoin)

        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawPath(path)


class ResetSerialInView(QWidget):

    serial_updated = pyqtSignal(str, int)
    reset_triggered = pyqtSignal(str, int)

    def __init__(self):
        super().__init__()

        self.setObjectName("ResetSerialInView")

        self.setStyleSheet("""
            QWidget#ResetSerialInView {
                background-color: #10141B;
                color: #D6E0EE;
                font-family: 'Segoe UI';
                font-size: 18px;
            }

            QLabel {
                background: transparent;
                border: none;
                color: #D6E0EE;
                font-size: 18px;
            }

            QLineEdit {
                background-color: #0A1018;
                color: #45F5A5;
                border: 1px solid #29384A;
                border-radius: 7px;
                padding: 13px 15px;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 23px;
                font-weight: bold;
                selection-background-color: #176B56;
                selection-color: #FFFFFF;
            }

            QLineEdit:focus {
                border: 1px solid #39DFA1;
                background-color: #0C171B;
            }

            QPushButton {
                background-color: #202A38;
                color: #D6E0EE;
                border: 1px solid #34475D;
                border-radius: 7px;
                padding: 11px 17px;
                font-size: 18px;
                font-weight: bold;
            }

            QPushButton:hover {
                background-color: #29384A;
                border-color: #45F5A5;
            }

            QPushButton:pressed {
                background-color: #142C29;
            }
        """)

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(22, 20, 22, 22)
        self.layout.setSpacing(22)

        # --------------------------------------------------
        # RESET button
        # --------------------------------------------------

        reset_layout = QHBoxLayout()
        reset_layout.addStretch()

        self.btn_reset = QPushButton("RESET")
        self.btn_reset.setFixedSize(120, 72)
        self.btn_reset.setCursor(Qt.PointingHandCursor)

        self.btn_reset.setStyleSheet("""
            QPushButton {
                background-color: #321C27;
                color: #FF7188;
                border: 2px solid #A33C55;
                border-radius: 13px;
                font-family: 'Consolas', monospace;
                font-size: 20px;
                font-weight: 900;
                letter-spacing: 2px;
            }

            QPushButton:hover {
                background-color: #49212F;
                color: #FF9AAA;
                border: 2px solid #FF7188;
            }

            QPushButton:pressed {
                background-color: #812F45;
                color: #FFFFFF;
                border: 2px solid #FF9AAA;
            }
        """)

        self.btn_reset.clicked.connect(
            self.on_reset_clicked
        )

        reset_layout.addWidget(self.btn_reset)
        reset_layout.addStretch()

        self.layout.addLayout(reset_layout)

        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFixedHeight(1)
        separator.setStyleSheet(
            "background-color: #273344; border: none;"
        )

        self.layout.addWidget(separator)

        bin_validator = QRegExpValidator(
            QRegExp("[0-1]*"), self
        )

        # --------------------------------------------------
        # Serial channels
        # --------------------------------------------------

        self.serial0_panel = self._create_serial_section(
            "serial0", "101101", bin_validator
        )

        self.serial1_panel = self._create_serial_section(
            "serial1", "011010", bin_validator
        )

        self.layout.addWidget(
            self.serial0_panel["panel"]
        )

        self.layout.addWidget(
            self.serial1_panel["panel"]
        )

        self.input_s0 = self.serial0_panel["input"]
        self.input_s1 = self.serial1_panel["input"]

        self.lbl_s0_wire = self.serial0_panel["wire_label"]
        self.lbl_s1_wire = self.serial1_panel["wire_label"]

        self.layout.addStretch()

    # ------------------------------------------------------
    # Create serial channel
    # ------------------------------------------------------

    def _create_serial_section(
        self, name, initial_value, validator
    ):

        panel = QFrame()
        panel.setObjectName(f"{name}_panel")

        panel.setStyleSheet("""
            QFrame {
                background-color: #171E29;
                border: 1px solid #2B394B;
                border-radius: 11px;
            }
        """)

        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(18, 18, 18, 19)
        panel_layout.setSpacing(16)

        # Header
        header_layout = QHBoxLayout()

        tag = QLabel("SERIAL CHANNEL")
        tag.setStyleSheet("""
            QLabel {
                color: #8193AA;
                font-family: 'Consolas', monospace;
                font-size: 16px;
                font-weight: bold;
                letter-spacing: 2px;
            }
        """)

        channel_name = QLabel(name)
        channel_name.setStyleSheet("""
            QLabel {
                color: #D9E5F5;
                font-family: 'Consolas', monospace;
                font-size: 19px;
                font-weight: bold;
            }
        """)

        header_layout.addWidget(tag)
        header_layout.addStretch()
        header_layout.addWidget(channel_name)

        panel_layout.addLayout(header_layout)

        # Input field
        input_field = QLineEdit(initial_value)
        input_field.setValidator(validator)
        input_field.setMinimumHeight(56)
        input_field.setPlaceholderText(
            "Enter binary bits..."
        )
        input_field.setClearButtonEnabled(True)

        # Serial status label
        wire_label = QLabel(f"{name}: LOW (0)")
        wire_label.setAlignment(
            Qt.AlignVCenter | Qt.AlignLeft
        )

        wire_label.setStyleSheet("""
            QLabel {
                color: #8290A4;
                font-family: 'Consolas', monospace;
                font-size: 18px;
                font-weight: bold;
            }
        """)

        # Content layout
        content_layout = QHBoxLayout()
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        right_layout = QVBoxLayout()
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(13)

        right_layout.addWidget(input_field)

        # Status row: no circle and no BIT OUT text.
        status_layout = QHBoxLayout()
        status_layout.setContentsMargins(0, 0, 0, 0)
        status_layout.setSpacing(0)

        status_layout.addWidget(wire_label)
        status_layout.addStretch()

        right_layout.addLayout(status_layout)

        # Create wire after the connected widgets.
        wire = SignalWire(
            panel,
            input_field,
            wire_label
        )

        content_layout.addWidget(wire)
        content_layout.addLayout(
            right_layout, stretch=1
        )

        panel_layout.addLayout(content_layout)

        return {
            "panel": panel,
            "input": input_field,
            "wire_label": wire_label,
            "wire": wire
        }

    # ------------------------------------------------------
    # Update visual signal state
    # ------------------------------------------------------

    def _set_serial_visual_state(
        self, channel, value, empty=False
    ):

        section = (
            self.serial0_panel
            if channel == "serial0"
            else self.serial1_panel
        )

        wire_label = section["wire_label"]
        wire = section["wire"]

        active = value == 1 and not empty

        if empty:
            wire_label.setText(
                f"{channel}: LOW (0) [Empty]"
            )
        else:
            wire_label.setText(
                f"{channel}: HIGH (1)"
                if active
                else f"{channel}: LOW (0)"
            )

        text_color = (
            "#45F5A5" if active else "#8290A4"
        )

        wire_label.setStyleSheet(f"""
            QLabel {{
                color: {text_color};
                font-family: 'Consolas', monospace;
                font-size: 18px;
                font-weight: bold;
            }}
        """)

        wire.set_active(active)

    # ------------------------------------------------------
    # Reset
    # ------------------------------------------------------

    def on_reset_clicked(self):

        self.reset_triggered.emit("rst", 1)

        QTimer.singleShot(
            250,
            lambda: self.reset_triggered.emit("rst", 0)
        )

    # ------------------------------------------------------
    # Clock tick / serial shifting (MSB-first from left)
    # ------------------------------------------------------

    def clock_tick(self):

        # Serial 0
        text_s0 = self.input_s0.text().strip()

        if text_s0:

            msb_char = text_s0[0]  # Take leftmost bit (MSB)
            val_s0 = int(msb_char)

            new_text_s0 = text_s0[1:]  # Shift remaining bits left
            self.input_s0.setText(new_text_s0)

            self.serial_updated.emit(
                "serial0", val_s0
            )

            self._set_serial_visual_state(
                "serial0", val_s0
            )

        else:

            self.serial_updated.emit("serial0", 0)

            self._set_serial_visual_state(
                "serial0", 0, empty=True
            )

        # Serial 1
        text_s1 = self.input_s1.text().strip()

        if text_s1:

            msb_char = text_s1[0]  # Take leftmost bit (MSB)
            val_s1 = int(msb_char)

            new_text_s1 = text_s1[1:]  # Shift remaining bits left
            self.input_s1.setText(new_text_s1)

            self.serial_updated.emit(
                "serial1", val_s1
            )

            self._set_serial_visual_state(
                "serial1", val_s1
            )

        else:

            self.serial_updated.emit("serial1", 0)

            self._set_serial_visual_state(
                "serial1", 0, empty=True
            )

    # ------------------------------------------------------
    # Synchronization
    # ------------------------------------------------------

    def sync_data(self, state_dict):
        pass

    # ------------------------------------------------------
    # Help
    # ------------------------------------------------------

    def show_help(self):
        msg = QMessageBox()
        msg.setWindowTitle("Reset & Serial Bit In Guide")
        msg.setText(
            "<b>Reset & Serial Bit In Controller</b><br><br>"
            "<b>1. System Reset (RESET)</b><br>"
            "Clicking the <b>RESET</b> button sends a temporary high reset signal to your Verilog design.<br><br>"
            "<b>2. MSB-First Serial Input Streaming</b><br>"
            "• Type binary sequences (0s and 1s) into the <b><code>serial0</code></b> and <b><code>serial1</code></b> input fields.<br>"
            "• On every positive clock edge (via <b>PULSE</b> or <b>AUTO</b> clock), the leftmost bit (MSB) is consumed and driven onto the respective wire.<br>"
            "• The remaining bits automatically shift left for the next cycle.<br><br>"
            "<b>3. Live Wire Indicators</b><br>"
            "The wire status labels update and highlight in green whenever the currently transmitted bit is <code>1</code>."
        )
        msg.exec_()