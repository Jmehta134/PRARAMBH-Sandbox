import os
import shutil
from PyQt5.QtWidgets import (
    QGraphicsView, QGraphicsScene, QGraphicsTextItem, QWidget, 
    QHBoxLayout, QPushButton, QFileDialog, QMessageBox
)
from PyQt5.QtSvg import QGraphicsSvgItem
from PyQt5.QtGui import QPainter, QColor, QFont, QImage
from PyQt5.QtCore import Qt, QTimer, QRectF

class RTLViewerPane(QGraphicsView):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        self.svg_item = None
        self.current_svg_path = None
        
        self.setBackgroundBrush(QColor("#FAFAFA"))  # Light canvas background
        self.setDragMode(QGraphicsView.ScrollHandDrag)
        self.setRenderHint(QPainter.Antialiasing)
        self.setRenderHint(QPainter.SmoothPixmapTransform)
        
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        self._show_message("No RTL Schematic Loaded.\nLoad a Verilog file or click ▶ Compile to view hardware schematic.")

        # Floating Control Toolbar Overlay
        self.setup_overlay_toolbar()

    def setup_overlay_toolbar(self):
        self.toolbar_container = QWidget(self)
        self.toolbar_container.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 230);
                border: 1px solid #CCCCCC;
                border-radius: 4px;
                font-weight: bold;
                color: #333333;
                font-size: 13px;
                padding: 4px 10px;
            }
            QPushButton#ZoomBtn {
                font-size: 18px;
                font-weight: 900;
            }
            QPushButton:hover {
                background-color: rgba(229, 241, 251, 240);
                border: 1px solid #0078D7;
                color: #0078D7;
            }
            QPushButton:pressed {
                background-color: rgba(204, 228, 247, 240);
            }
        """)
        
        tb_layout = QHBoxLayout(self.toolbar_container)
        tb_layout.setContentsMargins(6, 6, 6, 6)
        tb_layout.setSpacing(6)

        self.btn_zoom_in = QPushButton("+")
        self.btn_zoom_in.setObjectName("ZoomBtn")
        self.btn_zoom_in.setFixedSize(36, 36)
        self.btn_zoom_in.setToolTip("Zoom In")
        self.btn_zoom_in.clicked.connect(self.zoom_in)

        self.btn_zoom_out = QPushButton("-")
        self.btn_zoom_out.setObjectName("ZoomBtn")
        self.btn_zoom_out.setFixedSize(36, 36)
        self.btn_zoom_out.setToolTip("Zoom Out")
        self.btn_zoom_out.clicked.connect(self.zoom_out)

        self.btn_fit = QPushButton("1:1 / Fit")
        self.btn_fit.setFixedHeight(36)
        self.btn_fit.setToolTip("Reset to Fit View")
        self.btn_fit.clicked.connect(self.reset_zoom_fit)

        self.btn_export = QPushButton("💾 Export Schematic")
        self.btn_export.setFixedHeight(36)
        self.btn_export.setToolTip("Export Schematic as SVG, PNG, or PDF")
        self.btn_export.clicked.connect(self.export_schematic)

        tb_layout.addWidget(self.btn_zoom_in)
        tb_layout.addWidget(self.btn_zoom_out)
        tb_layout.addWidget(self.btn_fit)
        tb_layout.addWidget(self.btn_export)

        self.toolbar_container.adjustSize()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Pin toolbar to the bottom-right corner of the view viewport
        margin = 15
        tb_width = self.toolbar_container.width()
        tb_height = self.toolbar_container.height()
        self.toolbar_container.move(self.viewport().width() - tb_width - margin, self.viewport().height() - tb_height - margin)

    def load_rtl_svg(self, file_or_error_path: str):
        self.scene.clear()
        self.resetTransform()
        self.current_svg_path = None
        
        if not file_or_error_path:
            self._show_message("No RTL Schematic Loaded.\nLoad a Verilog file or click ▶ Compile.")
            return

        # Render Error Messages directly on canvas
        if file_or_error_path.startswith("RTL_ERROR:"):
            err_text = file_or_error_path.replace("RTL_ERROR:", "[RTL SCHEMATIC ERROR]").strip()
            self._show_message(err_text, is_error=True)
            return

        # Render Valid SVG File
        if os.path.exists(file_or_error_path):
            try:
                self.current_svg_path = file_or_error_path
                self.svg_item = QGraphicsSvgItem(file_or_error_path)
                self.scene.addItem(self.svg_item)
                
                rect = self.svg_item.boundingRect()
                self.setSceneRect(rect)
                
                QTimer.singleShot(50, lambda: self._fit_diagram(rect))
            except Exception as e:
                self._show_message(f"[RTL SCHEMATIC ERROR]\nFailed to display SVG schematic: {str(e)}", is_error=True)
        else:
            self._show_message(f"[RTL SCHEMATIC ERROR]\nSVG file not found: {file_or_error_path}", is_error=True)

    def _fit_diagram(self, rect):
        if rect.width() > 0 and rect.height() > 0:
            self.fitInView(rect, Qt.KeepAspectRatio)

    def _show_message(self, text: str, is_error: bool = False):
        txt_item = QGraphicsTextItem(text)
        color = QColor("#D32F2F") if is_error else QColor("#666666")
        txt_item.setDefaultTextColor(color)
        txt_item.setFont(QFont("Consolas", 11, QFont.Bold if is_error else QFont.Normal))
        self.scene.addItem(txt_item)
        self.setSceneRect(self.scene.itemsBoundingRect())

    def zoom_in(self):
        self.scale(1.15, 1.15)

    def zoom_out(self):
        self.scale(1 / 1.15, 1 / 1.15)

    def reset_zoom_fit(self):
        if self.svg_item:
            self.fitInView(self.svg_item.boundingRect(), Qt.KeepAspectRatio)

    def export_schematic(self):
        if not self.current_svg_path or not os.path.exists(self.current_svg_path):
            QMessageBox.warning(self, "Export Failed", "No valid RTL schematic is currently loaded to export.")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, 
            "Export RTL Schematic", 
            "rtl_schematic.svg", 
            "Scalable Vector Graphics (*.svg);;PNG Image (*.png);;PDF Document (*.pdf)"
        )
        
        if not file_path:
            return

        try:
            if file_path.endswith('.svg'):
                shutil.copyfile(self.current_svg_path, file_path)
            elif file_path.endswith('.png'):
                rect = self.scene.itemsBoundingRect()
                if rect.isEmpty():
                    return
                image = QImage(rect.size().toSize() * 2, QImage.Format_ARGB32)
                image.fill(Qt.white)
                painter = QPainter(image)
                painter.setRenderHint(QPainter.Antialiasing)
                painter.setRenderHint(QPainter.SmoothPixmapTransform)
                self.scene.render(painter, target=QRectF(image.rect()), source=rect)
                painter.end()
                image.save(file_path, "PNG")
            elif file_path.endswith('.pdf'):
                shutil.copyfile(self.current_svg_path, file_path)
            
            QMessageBox.information(self, "Export Successful", f"Schematic successfully exported to:\n{file_path}")
        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Failed to export schematic file:\n{str(e)}")

    def wheelEvent(self, event):
        zoom_factor = 1.15 if event.angleDelta().y() > 0 else (1 / 1.15)
        self.scale(zoom_factor, zoom_factor)