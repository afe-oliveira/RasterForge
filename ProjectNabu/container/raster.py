from typing import TypedDict, Union, Literal, Dict, Optional, Tuple

import numpy as np
import rasterio


class RasterImportConfig(TypedDict):
    id: int
    name: str
    type: Literal['relative', 'absolute']


class LayerFormat(TypedDict):
    data: np.ndarray[Union[np.uint8, np.int32]]
    type: Literal['relative', 'absolute']


class Raster:

    layers: Dict[str, np.ndarray[Union[np.uint8, np.int32]]] = {}

    _scale: int = None
    _transform: Optional[Tuple[float, float, float, float, float, float]] = None
    _projection = Optional[str] = None
    _metadata = Optional[Dict[str, str]] = None

    def __init__(self, scale: int):
        self._scale = scale

    # ****************

    @property
    def scale(self):
        return self._scale

    @property
    def transform(self) -> Optional[Tuple[float, float, float, float, float, float]]:
        return self._transform

    @transform.setter
    def transform(self, value: Optional[Tuple[float, float, float, float, float, float]]):
        self._transform = value

    @property
    def projection(self) -> Optional[str]:
        return self._projection

    @projection.setter
    def projection(self, value: Optional[str]):
        self._projection = value

    @property
    def metadata(self) -> Optional[Dict[str, str]]:
        return self._metadata

    @metadata.setter
    def metadata(self, value: Optional[Dict[str, str]]):
        self._metadata = value

    # ****************

    def import_layers(self, path: str, config: list[RasterImportConfig]):
        with rasterio.open(path) as dataset:
            for item in config:
                band = dataset.read(item["id"])

                if item['type'] == 'relative':
                    band = np.interp(band, (band.min(), band.max()), (0, 255))
                    self.layers[item["name"]] = band.astype(np.uint8)
                elif item['type'] == 'absolute':
                    pass

                band = np.interp(band, (band.min(), band.max()), (item['min'], item['max']))
                self.layers[item["name"]] = band.astype(np.uint8)

    def add_layer(self, data: np.ndarray, name: str):
        if name not in self.layers.keys():
            self.layers[name] = data

    def remove_layer(self, name: str):
        if name in self.layers.keys():
            self.layers.pop(name)

    def edit_layer(self, current_name: str, new_name: str):
        if current_name in self.layers.keys():
            self.layers[new_name] = self.layers.pop(current_name)