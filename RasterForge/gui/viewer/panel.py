import os
import shutil
import tempfile

import rasterio
from rasterio.transform import from_origin

import numpy as np
from PySide6.QtWidgets import (
    QGraphicsView,
    QGraphicsScene,
    QLabel,
    QGraphicsPixmapItem,
    QWidget,
    QPushButton,
    QGridLayout,
    QSlider,
    QFrame,
    QComboBox,
    QFileDialog,
)
from PySide6.QtGui import QPixmap, QTransform, QImage
from PySide6.QtCore import Qt, QRectF, QPointF
from matplotlib import pyplot as plt
from matplotlib.backends.backend_template import FigureCanvas

from RasterForge.gui.common.layer_information import LayerInfoWindow
from RasterForge.gui.data import _data

COLORMAPS = {
    "Viridis": "viridis",
    "Viridis (Reversed)": "viridis_r",
    "Plasma": "plasma",
    "Plasma (Reversed)": "plasma_r",
    "Inferno": "inferno",
    "Inferno (Reversed)": "inferno_r",
    "Magma": "magma",
    "Magma (Reversed)": "magma_r",
    "Cividis": "cividis",
    "Cividis (Reversed)": "cividis_r",
    "Twilight": "twilight",
    "Twilight (Reversed)": "twilight_r",
    "Gray": "gray",
    "Gray (Reversed)": "gray_r",
    "Autumn": "autumn",
    "Autumn (Reversed)": "autumn_r",
    "Cool-Warm": "coolwarm",
    "Red-Blue": "RdBu",
    "Spectral": "Spectral",
    "Jet": "jet",
    "Ocean": "ocean",
    "Terrain": "terrain",
}


class ViewerPanel(QWidget):

    current_zoom = 0
    layer = None

    def __init__(self):
        super().__init__()

        layout = QGridLayout(self)

        _data.viewer_changed.connect(self.update_viewer)

        # Add Save Buttons
        self.save_layer_button = QPushButton("Layer")
        layout.addWidget(self.save_layer_button, 0, 0, 1, 1)
        self.save_layer_button.clicked.connect(self.save_as_layer)

        self.save_image_button = QPushButton("Image")
        layout.addWidget(self.save_image_button, 0, 1, 1, 1)
        self.save_image_button.clicked.connect(self.save_as_image)

        self.save_tif_button = QPushButton("TIFF")
        layout.addWidget(self.save_tif_button, 0, 2, 1, 1)
        self.save_tif_button.clicked.connect(self.save_as_geotiff)

        # Add Colormap ComboBox
        self.colormap_label = QLabel("Colormap:")
        self.colormap_combobox = QComboBox()
        self.colormap_combobox.addItems(list(COLORMAPS.keys()))
        self.colormap_combobox.setCurrentText("gray")
        layout.addWidget(self.colormap_label, 0, 21, 1, 1)
        layout.addWidget(self.colormap_combobox, 0, 22, 1, 1)
        self.colormap_combobox.currentIndexChanged.connect(self.update_viewer)

        # Add Pixel Value Button
        self.pixel_value_button = QPushButton("T")
        layout.addWidget(self.pixel_value_button, 0, 23, 1, 1)
        self.pixel_value_button.clicked.connect(self.toggle_pixel_value)
        self.pixel_value_show = False

        # Add Info Button
        self.info_button = QPushButton("Info")
        layout.addWidget(self.info_button, 0, 24, 1, 1)
        self.info_button.clicked.connect(self.show_info)

        # Add Graphics Scene and Graphics View
        self.scene = QGraphicsScene(self)
        self.graphics_view = QGraphicsView(self.scene)
        self.graphics_view.setMouseTracking(True)
        layout.addWidget(self.graphics_view, 1, 0, 47, 25)

        self.graphics_view.fitInView(self.scene.sceneRect(), Qt.KeepAspectRatio)

        # Add Zoom Slider
        self.zoom_slider = QSlider()
        self.zoom_slider.setOrientation(Qt.Horizontal)
        self.zoom_slider.setMinimum(0)
        self.zoom_slider.setMaximum(2000)
        self.zoom_slider.setValue(0)

        self.zoom_label = QLabel("Zoom:")
        self.zoom_value_label = QLabel("1.0")
        self.restore_zoom_button = QPushButton("Restore Zoom")

        layout.addWidget(self.zoom_label, 48, 0, 1, 1)
        layout.addWidget(self.zoom_slider, 48, 1, 1, 22)
        layout.addWidget(self.zoom_value_label, 48, 23, 1, 1)
        layout.addWidget(self.restore_zoom_button, 48, 24, 1, 1)

        self.zoom_slider.valueChanged.connect(self.update_zoom)
        self.restore_zoom_button.clicked.connect(self.restore_zoom)

        # Add a Separator
        separator_line = QFrame()
        separator_line.setFrameShape(QFrame.HLine)
        separator_line.setFrameShadow(QFrame.Sunken)
        layout.addWidget(separator_line, 49, 0, 1, 25)

        # Add Coordinate Display
        self.pixel_coordinates_label = QLabel("N/A")
        layout.addWidget(self.pixel_coordinates_label, 50, 0, 1, 5)

        self.lat_lng_coordinates_label = QLabel("N/A")
        self.lat_lng_coordinates_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        layout.addWidget(self.lat_lng_coordinates_label, 50, 20, 1, 5)

        # Initialize a QLabel for displaying band values
        self.band_values_label = QLabel("", self)
        self.band_values_label.setGeometry(0, 0, 100, 50)
        self.band_values_label.setStyleSheet(
            "background-color: rgba(255, 255, 255, 200); border: 1px solid black;"
        )
        self.band_values_label.hide()

        self.graphics_view.mouseMoveEvent = self.update_coordinates
        self.update_zoom()

        _data.viewer_changed.emit()

    def update_coordinates(self, event):
        if _data.viewer is not None and _data.viewer.array is not None:
            pos_in_scene = self.graphics_view.mapToScene(event.pos())

            if self.graphics_view.transform():
                pos_in_original = self.graphics_view.transform().inverted()[0].map(pos_in_scene)

                if 0 <= pos_in_original.x() < _data.viewer.width and 0 <= pos_in_original.y() < _data.viewer.height:
                    pixel_coordinates = f"({int(pos_in_original.x())}, {int(pos_in_original.y())})"
                    self.pixel_coordinates_label.setText(f"{pixel_coordinates}")

                    if _data.viewer.transform is not None:
                        transform = from_origin(_data.viewer.transform[0], _data.viewer.transform[3],
                                                _data.viewer.transform[1], _data.viewer.transform[5])
                        pos_transformed = transform * (pos_in_scene.x(), pos_in_scene.y())

                        lat_lng_coordinates = f"({pos_transformed[0]}, {pos_transformed[1]})"
                        self.lat_lng_coordinates_label.setText(f"{lat_lng_coordinates}")
                    else:
                        self.lat_lng_coordinates_label.setText(f"N/A")

                    band_values = self.get_band_values(int(pos_in_original.x()), int(pos_in_original.y()))
                    self.show_band_values_popup(event, band_values)
                    return

        self.pixel_coordinates_label.setText(f"N/A")
        self.lat_lng_coordinates_label.setText(f"N/A")

    def show_band_values_popup(self, event, band_values):
        if self.pixel_value_show:
            cursor_pos = self.graphics_view.mapToScene(event.pos())
            self.band_values_label.setText(f"Band Values: {band_values}")
            self.band_values_label.move(cursor_pos.x() + 10, cursor_pos.y() + 10)
            self.band_values_label.show()

    def get_band_values(self, x, y):
        band_values = ""
        if _data.viewer.array is not None:
            if _data.viewer.count > 1:
                for i in range(_data.viewer.count):
                    band_values += f"Band {i + 1}: {_data.viewer.array[y, x, i]} \n"
            else:
                band_values = f"{_data.viewer.array[y, x]}"
        return band_values

    def update_zoom(self):
        zoom_value = self.zoom_slider.value()
        self.current_zoom = 1.0 + zoom_value / 100.0
        self.graphics_view.setTransform(
            QTransform().scale(self.current_zoom, self.current_zoom)
        )
        self.zoom_value_label.setText(f"{self.current_zoom:.2f}")

    def restore_zoom(self):
        self.zoom_slider.setValue(0)
        self.update_zoom()

    def toggle_pixel_value(self):
        self.pixel_value_show = not self.pixel_value_show

    def update_viewer(self):
        self.colormap_combobox.setEnabled(False)

        if _data.viewer is not None and _data.viewer.array is not None:
            self.colormap_combobox.setEnabled(_data.viewer.count == 1 or _data.viewer.count == 2)

            temp_file_path = tempfile.mktemp(
                suffix=".png", prefix="temp_image_", dir=tempfile.gettempdir()
            )

            fig, ax = plt.subplots()
            fig.patch.set_alpha(0)

            if _data.viewer.count == 2:
                normal_data = _data.viewer.array[..., 0]
                alpha_channel = np.interp(
                    _data.viewer.array[..., 1],
                    (_data.viewer.array[..., 1].min(), _data.viewer.array[..., 1].max()),
                    (0, 1),
                )

                ax.imshow(
                    normal_data,
                    cmap=COLORMAPS[self.colormap_combobox.currentText()],
                    alpha=alpha_channel,
                )
            else:
                ax.imshow(
                    _data.viewer.array,
                    cmap=COLORMAPS[self.colormap_combobox.currentText()],
                )

            ax.axis("off")
            ax.set_frame_on(False)

            plt.savefig(temp_file_path, format="png", transparent=True)
            plt.close()

            image = QImage(temp_file_path)
            pixmap = QPixmap.fromImage(image)
            os.remove(temp_file_path)

            self.scene.clear()

            image_item = QGraphicsPixmapItem(pixmap)

            self.scene.addItem(image_item)

            self.update_zoom()


    def show_info(self):
        info_window = LayerInfoWindow("Viewer Data", _data.viewer, self)
        info_window.exec_()

    def save_as_layer(self):
        if _data.viewer is not None and _data.raster is not None:
            _data.raster.add_layer(_data.viewer, "Layer")

    def save_as_geotiff(self):
        if _data.viewer is not None and _data.raster is not None:
            file_dialog = QFileDialog()
            file_path, _ = file_dialog.getSaveFileName(
                self, "Save as TIFF", "", "TIFF Files (*.tif *.tiff)"
            )

            if file_path:
                tiff_data = _data.viewer.array.astype(np.uint8)
                import tifffile

                tifffile.imwrite(file_path, tiff_data)

    def save_as_image(self):
        if _data.viewer is not None and _data.raster is not None:
            file_dialog = QFileDialog()
            file_path, _ = file_dialog.getSaveFileName(
                self, "Save as Image", "", "Image Files (*.png *.jpg *.jpeg *.bmp)"
            )

            if file_path:
                temp_file_path = tempfile.mktemp(
                    suffix=".png", prefix="temp_image_", dir=tempfile.gettempdir()
                )

                image_data = _data.viewer.array.astype(np.uint8)
                plt.imshow(
                    image_data, cmap=COLORMAPS[self.colormap_combobox.currentText()]
                )
                plt.axis("off")
                plt.savefig(temp_file_path, format="png", transparent=True)
                plt.close()

                shutil.move(temp_file_path, file_path)
