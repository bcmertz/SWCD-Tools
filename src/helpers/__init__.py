# --------------------------------------------------------------------------------
# Name:        Helpers Package
# Purpose:     Collect helper tools into a package, import functions specifically
#
# License:     Contextual Copyleft AI (CCAI) License v1.0.
#              Full license in LICENSE file.
# --------------------------------------------------------------------------------

from .layers import get_oid, add_layer_to_group, is_empty
from .logging import log, warn, error
from .parameter import (
    validate_spatial_reference,
    set_required_parameter,
    sanitize,
    raster_and_layer,
)
from .rasters import (
    pixel_type,
    cell_area,
    cell_length,
    min_cell_path,
    cells_per_area,
    cells_per_length,
)
from .tool import license, setup_environment, reload_module, empty_workspace
from .units import (
    get_z_unit,
    get_linear_unit,
    Z_UNITS,
    LINEAR_UNITS,
    AREAL_UNITS,
    LINEAR_UNITS_MAP,
    AREAL_UNITS_MAP,
    SPATIAL_TO_LINEAR,
    LINEAR_TO_AREAL,
    convert_area,
    convert_length,
)

__all__ = [
    "get_oid",
    "add_layer_to_group",
    "is_empty",
    "log",
    "warn",
    "error",
    "validate_spatial_reference",
    "set_required_parameter",
    "sanitize",
    "raster_and_layer",
    "pixel_type",
    "cell_area",
    "cell_length",
    "min_cell_path",
    "cells_per_area",
    "cells_per_length",
    "license",
    "setup_environment",
    "reload_module",
    "empty_workspace",
    "get_z_unit",
    "get_linear_unit",
    "Z_UNITS",
    "LINEAR_UNITS",
    "AREAL_UNITS",
    "LINEAR_UNITS_MAP",
    "AREAL_UNITS_MAP",
    "SPATIAL_TO_LINEAR",
    "LINEAR_TO_AREAL",
    "convert_area",
    "convert_length",
]
