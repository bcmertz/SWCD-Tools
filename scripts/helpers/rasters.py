# -----------------------------------------------------------------------------------
# Name:        Raster Helper
# Purpose:     This package contains various tools for working with rasters.
#
# License:     Contextual Copyleft AI (CCAI) License v1.0.
#              Full license in LICENSE file.
# -----------------------------------------------------------------------------------

import arcpy

from .units import convert_area, LINEAR_TO_AREAL, SPATIAL_TO_LINEAR

PIXEL_TYPES = {
    "U1": "1_BIT",
    "U2": "2_BIT",
    "U4": "4_BIT",
    "S8": "8_BIT_SIGNED",
    "U8": "8_BIT_UNSIGNED",
    "S16": "16_BIT_UNSIGNED",
    "U16": "16_BIT_SIGNED",
    "S32": "32_BIT_UNSIGNED",
    "U32": "32_BIT_SIGNED",
    "F32": "32_BIT_FLOAT",
    "F64": "64_BIT"
}

def pixel_type(raster):
    """Return the the string representation of the raster pixel type."""
    return PIXEL_TYPES[raster.pixelType]

def cell_area(raster) -> str:
    """Return the cell size of a raster as a GPArealUnit."""
    # Note: throws an error if not a raster, this is desirable and shouldn't be used on
    # data types other than a raster
    desc_raster = arcpy.Describe(raster)
    linear_unit = SPATIAL_TO_LINEAR[desc_raster.spatialReference.linearUnitName]
    square_unit = LINEAR_TO_AREAL[linear_unit]

    # Cell size in the X and Y axis
    cellsize_y = desc_raster.meanCellHeight
    cellsize_x = desc_raster.meanCellWidth
    area=cellsize_x * cellsize_y

    # create unit
    unit = "{} {}".format(area, square_unit)

    return unit

def cells_per_area(raster, area: str) -> int:
    """Convert GPArealUnit AREA to the number of cells in the RASTER it is equivalent to."""
    cell_size, cell_unit = cell_area(raster).split(" ")

    # convert area to raster cell unit
    area_size_in_cell_units = convert_area(area, cell_unit).split(" ")[0]

    # find number of cells
    num_cells = area_size_in_cell_units / cell_size
    return num_cells

def min_cell_path(parameters):
    """Return the parameter with the smallest cell size."""
    min_cell_size = None
    min_cell_path = None
    for param in parameters:
        try:
            # get GPArealUnit of param and convert to US Acres
            raster_cell_area = cell_area(param.value)
            size_acres, unit = convert_area(raster_cell_area, "AcresUS").split(" ")

            # compare sizes
            if min_cell_size is None or size_acres < min_cell_size:
                min_cell_size = size_acres
                min_cell_path = param.valueAsText
        except:
            pass

    return min_cell_path
