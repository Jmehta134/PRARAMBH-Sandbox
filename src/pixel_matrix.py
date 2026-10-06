from PyQt5.QtWidgets import QWidget, QGridLayout, QFrame, QVBoxLayout, QLabel, QApplication, QMessageBox
from PyQt5.QtCore import Qt

class PixelMatrixView(QWidget):
    """An enlarged, industrial-grade 16x16 LED matrix display panel."""
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        
        # Professional Header Label (Matched size and weight)
        title = QLabel("16x16 HARDWARE LED MATRIX PANEL")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("""
            font-weight: 900; 
            color: #333333; 
            font-size: 18px; 
            letter-spacing: 1.5px;
            margin-bottom: 5px;
        """)
        layout.addWidget(title)
        
        # Recessed Bezel Frame for the Matrix Board
        bezel = QFrame()
        bezel.setStyleSheet("""
            QFrame {
                background-color: #151515;
                border: 3px inset #333333;
                border-radius: 8px;
            }
        """)
        
        grid = QGridLayout(bezel)
        grid.setSpacing(4)  # Clean gap between physical LEDs
        grid.setContentsMargins(15, 15, 15, 15)
        
        self.pixels = {}
        for y in range(16):
            for x in range(16):
                px = QFrame()
                px.setFixedSize(26, 26)  # Significantly larger pixels for high visibility
                self.set_pixel_style(px, False)
                grid.addWidget(px, y, x)
                self.pixels[(x, y)] = px
                
        layout.addWidget(bezel, alignment=Qt.AlignCenter)
        layout.addStretch()

    def set_pixel_style(self, pixel_widget, is_on):
        if is_on:
            pixel_widget.setStyleSheet("""
                QFrame {
                    background-color: #00E5FF;
                    border: 1px solid #008899;
                    border-radius: 4px;
                }
            """)
        else:
            pixel_widget.setStyleSheet("""
                QFrame {
                    background-color: #222222;
                    border: 1px solid #111111;
                    border-radius: 4px;
                }
            """)

    def update_pixel(self, x, y, is_on):
        """API for Verilog testbench to update a specific pixel coordinate."""
        if (x, y) in self.pixels:
            self.set_pixel_style(self.pixels[(x, y)], is_on)

    def show_help(self):
        msg = QMessageBox(self)
        msg.setWindowTitle("Learner Guide: Pixel Matrix View")
        msg.setText(
            "<b>16x16 LED Matrix Interface Mapping</b><br><br>"
            "This module visualizes a 256-LED grid mapped to a single 256-bit bus output from your Verilog design:<br><br>"
            "<b>Output Port Monitored:</b><br>"
            "• <code>pixel_matrix</code> : 256-bit output bus ([255:0])<br><br>"
            "<b>Grid Mapping:</b><br>"
            "Bit 0 controls coordinate (0,0) [Top-Left], and Bit 255 controls (15,15) [Bottom-Right].<br><br>"
            "<b>Example Verilog Port:</b><br>"
            "<code>output [255:0] pixel_matrix</code>"
        )
        msg.exec_()


if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    test_window = QWidget()
    test_window.setStyleSheet("background-color: #FAFAFA;")
    layout = QVBoxLayout(test_window)
    module = PixelMatrixView()
    layout.addWidget(module)
    test_window.setWindowTitle("Module Test: Pixel Matrix")
    test_window.resize(600, 600)
    test_window.show()
    sys.exit(app.exec_())