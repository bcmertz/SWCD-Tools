# -----------------------------------------------------------------------------------
# Name:        Raster Helper
# Purpose:     This package contains various tools for working with rasters.
#
# License:     Contextual Copyleft AI (CCAI) License v1.0.
#              Full license in LICENSE file.
# -----------------------------------------------------------------------------------

import arcpy
from enum import StrEnum

from .units import (
    get_linear_unit,
    Distance,
    Area,
)


class PIXEL_TYPE(StrEnum):
    U1 = "1_BIT"
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


def cell_area(raster) -> Area:
    """Return the cell size of a RASTER as an AREA."""
    # Note: throws an error if not a raster, this is desirable and shouldn't be used on
    # data types other than a raster
    desc_raster = arcpy.Describe(raster)
    linear_unit = get_linear_unit(raster)
    square_unit = linear_unit.to_areal()

    # Cell size in the X and Y axis
    cellsize_y = desc_raster.meanCellHeight
    cellsize_x = desc_raster.meanCellWidth
    area = cellsize_x * cellsize_y

    # output area
    area = Area(area, square_unit)

    return area


def cell_length(raster) -> Distance:
    """Return the average cell length of a RASTER as a LENGTH."""
    # Note: throws an error if not a raster, this is desirable and shouldn't be used on
    # data types other than a raster
    desc_raster = arcpy.Describe(raster)
    linear_unit = get_linear_unit(raster)

    # Cell size in the X and Y axis
    cellsize_y = desc_raster.meanCellHeight
    cellsize_x = desc_raster.meanCellWidth
    average_length = (cellsize_y + cellsize_x) / 2

    # output length
    length = Distance(average_length, linear_unit)

    return length


def cells_per_area(raster, area: Area) -> int:
    """Convert Area to the number of cells in the RASTER it is equivalent to."""
    raster_cell_area = cell_area(raster)
    cell_size = raster_cell_area.area
    cell_unit = raster_cell_area.unit

    # convert area to raster cell unit
    area_size_in_cell_units = area.to_unit(cell_unit).area

    # find number of cells
    num_cells = area_size_in_cell_units / cell_size
    return int(num_cells)


def cells_per_length(raster, length: Distance) -> int:
    """Convert Distance to the number of cells in the RASTER it is equivalent to."""
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
    min_cell_size: Area | None = None
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
