import inspect
from typing import Type

import numpy as np
from PySide6.QtGui import Qt
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QPushButton,
    QScrollArea,
    QProgressBar,
    QComboBox,
    QLineEdit,
    QLabel,
    QGroupBox,
    QGridLayout,
    QFrame,
    QDoubleSpinBox, QSpinBox,
)

from RasterForge.containers.layer import Layer

from RasterForge.gui.data import data
from RasterForge.gui.processes.adaptative_elements import adaptative_input

from RasterForge.processes.composite import PRESET_COMPOSITES, composite
from RasterForge.processes.topographic import slope, aspect


class FuelPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        # Create a Scroll Area
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)

        self.scroll_content = QWidget(self)
        self.scroll_area.setWidget(self.scroll_content)

        # Create a Vertical Layout for the Scroll Content (Aligned Top)
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_layout.setAlignment(Qt.AlignTop)

        # Add the Combo Box and Scroll Area to the main layout
        layout = QVBoxLayout(self)
        layout.addWidget(self.scroll_area)

        # Create a Grid Layout for the General UI
        buttons_layout = QGridLayout()

        # Add Back Button
        back_button = QPushButton("Back", self)
        back_button.clicked.connect(self.back_clicked)
        buttons_layout.addWidget(back_button, 0, 0, 1, 1)

        # Add Progress Bar
        progress_bar = QProgressBar(self)
        buttons_layout.addWidget(progress_bar, 0, 1, 1, 23)

        # Add Build Button
        build_button = QPushButton("Build", self)
        build_button.clicked.connect(self.build_clicked)
        buttons_layout.addWidget(build_button, 0, 24, 1, 1)

        # Add the Buttons Layout to the Main Layout
        layout.addLayout(buttons_layout)

        # Set Layout
        self.setLayout(layout)

        # When Raster Data Changes, Update Inner Scroll Content
        data.raster_changed.connect(self.update_scroll_content)

        # Start Scroll at First Position
        self.update_scroll_content()

    def update_scroll_content(self):
        # Clear Existing Widgets
        for i in reversed(range(self.scroll_layout.count())):
            widget = self.scroll_layout.takeAt(i).widget()
            if widget:
                widget.deleteLater()

        array_type: Type[np.ndarray] = np.ndarray
        self.inputs = {}

        for component in ["Vegetation Density", "Canopy Height", "Distance", "Water Feature", "Artificial Structures"]:
            label = QLabel(f"{component}", self)
            widget = adaptative_input(component, array_type)

            self.scroll_layout.addWidget(label)
            self.scroll_layout.addWidget(widget)

            self.inputs[component] = widget

        # Add Separator
        separator_line = QFrame(self)
        separator_line.setFrameShape(QFrame.HLine)
        separator_line.setFrameShadow(QFrame.Sunken)
        self.scroll_layout.addWidget(separator_line)

        # Add Alpha Selection
        label = QLabel(f"Alpha", self)
        widget = adaptative_input("Alpha", array_type)
        self.scroll_layout.addWidget(label)
        self.scroll_layout.addWidget(widget)
        self.inputs["Alpha"] = widget

        # Add Fuel Model Selection
        label = QLabel(f"Fuel Models", self)
        self.scroll_layout.addWidget(label)

        # Add Spinbox for Trees
        trees_label = QLabel("Trees", self)
        trees_spinbox = QSpinBox(self)
        self.scroll_layout.addWidget(trees_label)
        self.scroll_layout.addWidget(trees_spinbox)
        self.inputs["Trees"] = trees_spinbox

        # Add Spinbox for Trees Vegetation
        trees_vegetation_label = QLabel("Trees + Vegetation", self)
        trees_vegetation_spinbox = QSpinBox(self)
        self.scroll_layout.addWidget(trees_vegetation_label)
        self.scroll_layout.addWidget(trees_vegetation_spinbox)
        self.inputs["Trees + Vegetation"] = trees_vegetation_spinbox

        # Add Spinbox for Vegetation
        vegetation_label = QLabel("Vegetation", self)
        vegetation_spinbox = QSpinBox(self)
        self.scroll_layout.addWidget(vegetation_label)
        self.scroll_layout.addWidget(vegetation_spinbox)
        self.inputs["Vegetation"] = vegetation_spinbox

    def back_clicked(self):
        data.process_main.emit()

    def build_clicked(self):
        layer = Layer()
        data.viewer = layer
        data.viewer_changed.emit()