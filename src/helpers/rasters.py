# -----------------------------------------------------------------------------------
# Name:        Raster Helper
# Purpose:     This package contains various tools for working with rasters.
#
# License:     Contextual Copyleft AI (CCAI) License v1.0.
#              Full license in LICENSE file.
# -----------------------------------------------------------------------------------

import arcpy
from enum import StrEnum

from .units import LINEAR_TO_AREAL, SPATIAL_TO_LINEAR, LinearUnit, ArealUnit, LINEAR_UNITS, AREAL_UNITS

class PIXEL_TYPE(StrEnum):
    U1="1_BIT",
    U2 = "2_BIT"
    U4 = "4_BIT"
    S8 = "8_BIT_SIGNED"
    U8 = "8_BIT_UNSIGNED"
    S16 = "16_BIT_UNSIGNED"
    U16 = "16_BIT_SIGNED"
    S32 = "32_BIT_UNSIGNED"
    U32 = "32_BIT_SIGNED"
    F32 = "32_BIT_FLOAT"
    F64 = "64_BIT"

def pixel_type(raster) -> PIXEL_TYPE:
    """Return the the string representation of the raster pixel type."""
    return PIXEL_TYPE[raster.pixelType]

def cell_area(raster, to_unit: AREAL_UNITS | None = None) -> ArealUnit:
    """Return the cell size of a RASTER as a ArealUnit. User can specify unit AREA_UNITS
    for output ArealUnit to be in."""
    # Note: throws an error if not a raster, this is desirable and shouldn't be used on
    # data types other than a raster
    desc_raster = arcpy.Describe(raster)
    linear_unit = SPATIAL_TO_LINEAR[desc_raster.spatialReference.linearUnitName]
    square_unit = LINEAR_TO_AREAL[linear_unit]

    # Cell size in the X and Y axis
    cellsize_y = desc_raster.meanCellHeight
    cellsize_x = desc_raster.meanCellWidth
    area=cellsize_x * cellsize_y

    # output area
    area = ArealUnit("{} {}".format(area, square_unit))

    if to_unit is not None:
        area = area.to_unit(to_unit)

    return area

def cell_length(raster, to_unit: LINEAR_UNITS | None = None) -> LinearUnit:
    """Return the average cell length of a RASTER as a LinearUnit. User can specify
    unit LINEAR_UNITS for output LinearUnit to be in."""
    # Note: throws an error if not a raster, this is desirable and shouldn't be used on
    # data types other than a raster
    desc_raster = arcpy.Describe(raster)
    linear_unit = SPATIAL_TO_LINEAR[desc_raster.spatialReference.linearUnitName]

    # Cell size in the X and Y axis
    cellsize_y = desc_raster.meanCellHeight
    cellsize_x = desc_raster.meanCellWidth
    average_length = (cellsize_y + cellsize_x) / 2

    # output length
    length = LinearUnit("{} {}".format(average_length, linear_unit))

    if to_unit is not None:
        length = length.to_unit(to_unit)

    return length


def cells_per_area(raster, area: ArealUnit) -> int:
    """Convert ArealUnit to the number of cells in the RASTER it is equivalent to."""
    raster_cell_area = cell_area(raster)
    cell_size = raster_cell_area.area
    cell_unit = raster_cell_area.unit

    # convert area to raster cell unit
    area_size_in_cell_units = area.to_unit(cell_unit).area

    # find number of cells
    num_cells = area_size_in_cell_units / cell_size
    return int(num_cells)

def cells_per_length(raster, length: LinearUnit) -> int:
    """Convert LinearUnit to the number of cells in the RASTER it is equivalent to."""
    raster_cell_length = cell_length(raster)
    cell_size = raster_cell_length.length
    cell_unit = raster_cell_length.unit

    # convert length to raster cell unit
    area_size_in_cell_units = length.to_unit(cell_unit).length

    # find number of cells
    num_cells = area_size_in_cell_units / cell_size
    return int(num_cells)


def min_cell_path(parameters) -> str:
    """Return the parameter with the smallest cell size."""
    min_cell_size: ArealUnit | None = None
    min_cell_path = "MINOF"
    for param in parameters:
        try:
            # get cell size of param
            size = cell_area(param.value)
            if min_cell_size is None:
                min_cell_size = size
                min_cell_path = param.valueAsText
            else:
                if size < min_cell_size:
                    min_cell_size = size
                    min_cell_path = param.valueAsText
        except Exception:
            pass

    return min_cell_path
