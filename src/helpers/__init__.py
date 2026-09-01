# --------------------------------------------------------------------------------
# Name:        Helpers Package
# Purpose:     Collect helper tools into a package, import functions specifically
#
# License:     Contextual Copyleft AI (CCAI) License v1.0.
#              Full license in LICENSE file.
# --------------------------------------------------------------------------------

from .features import (
    fc_to_geometry,
    geometry_to_fc,
    is_empty,
)
from .geometry import (
    bbox,
    delaunay_fc,
    fc_to_numpy_array,
    triangle_csc,
    voronoi,
    voronoi_fc,
)
from .layers import add_layer_to_group, get_oid
from .logging import error, log, warn
from .parameter import (
    raster_and_layer,
    sanitize,
    set_required_parameter,
    validate_spatial_reference,
)
from .rasters import (
    cell_area,
    cell_length,
    cells_per_area,
    cells_per_length,
    min_cell_path,
    pixel_type,
)
from .tool import EXTENSIONS, empty_workspace, license, reload_module, setup_environment
from .units import (
    AREAL_UNITS,
    LINEAR_UNITS,
    SPATIAL_UNITS,
    Area,
    Distance,
    get_linear_unit,
    get_z_unit,
)

__all__ = [
    "AREAL_UNITS",
    "EXTENSIONS",
    "LINEAR_UNITS",
    "SPATIAL_UNITS",
    "Area",
    "Distance",
    "Length",
    "add_layer_to_group",
    "bbox",
    "cell_area",
    "cell_length",
    "cells_per_area",
    "cells_per_length",
    "delaunay_fc",
    "empty_workspace",
    "error",
    "fc_to_geometry",
    "fc_to_numpy_array",
    "geometry_to_fc",
    "get_linear_unit",
    "get_oid",
    "get_z_unit",
    "is_empty",
    "license",
    "log",
    "min_cell_path",
    "pixel_type",
    "raster_and_layer",
    "reload_module",
    "sanitize",
    "set_required_parameter",
    "setup_environment",
    "triangle_csc",
    "validate_spatial_reference",
    "voronoi",
    "voronoi_fc",
    "warn",
]
