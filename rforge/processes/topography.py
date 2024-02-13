from typing import Optional, Union

import numpy as np
from rforge.containers.layer import Layer
from rforge.tools.data_validation import check_layer
from rforge.tools.exceptions import Errors


def slope(
    dem: Union[Layer, np.ndarray],
    units: str = "degrees",
    alpha: Optional[Union[Layer, np.ndarray]] = None,
    as_array: bool = False,
) -> Union[np.ndarray, Layer]:
    """Calculate the slope of a terrain based on a Digital Elevation Model (DEM).

    Args:
      dem:
        Digital elevation model data representing the terrain.
      units:
        Units for computing the slope. Can be 'degrees' or 'radians'.
      alpha:
        Alpha layer. Defaults to None.
      as_array:
        If True, return the result as a Numpy array. Defaults to False.

    Returns:
      Slope map in the desired unit.

    Raises:
      TypeError:
        If inputs are not of the accepted type.
    """
    array = check_layer(dem)

    result = np.arctan(
        np.sqrt(
            np.power(np.gradient(array, axis=(0, 1))[0], 2)
            + np.power(np.gradient(array, axis=(0, 1))[1], 2)
        )
    )

    if units in ["degrees", "radians"]:
        if units == "degrees":
            result = np.degrees(result)
    else:
        raise TypeError(
            Errors.bad_input(name="units", expected_type="'degrees' or 'radians'")
        )

    if alpha is not None:
        alpha = check_layer(alpha)
        result = np.dstack([result, alpha])

    return result if as_array else Layer(result)


def aspect(
    dem: Union[Layer, np.ndarray],
    units: str = "degrees",
    alpha: Optional[Union[Layer, np.ndarray]] = None,
    as_array: bool = False,
) -> Union[np.ndarray, Layer]:
    """Calculate the aspect of a terrain slope based on a Digital Elevation Model (DEM).

    Args:
      dem:
        Digital elevation model data representing the terrain.
      units:
        Units for computing the slope. Can be 'degrees' or 'radians'.
      alpha:
        Alpha layer. Defaults to None.
      as_array:
        If True, return the result as a Numpy array. Defaults to False.

    Returns:
      Aspect map in the desired unit.
    """
    array = check_layer(dem)

    result = np.arctan2(-np.gradient(array, axis=0), np.gradient(array, axis=1))

    if units in ["degrees", "radians"]:
        if units == "degrees":
            result = np.degrees(result)
    else:
        raise TypeError(
            Errors.bad_input(name="units", expected_type="'degrees' or 'radians'")
        )

    if alpha is not None:
        result = np.dstack([result, alpha])

    if alpha is not None:
        alpha = check_layer(alpha)
        result = np.dstack([result, alpha])

    return result if as_array else Layer(result)
