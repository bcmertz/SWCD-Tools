# -----------------------------------------------------------------------------------
# Name:        Raster Helper
# Purpose:     This package contains various tools for working with rasters.
#
# License:     Contextual Copyleft AI (CCAI) License v1.0.
#              Full license in LICENSE file.
# -----------------------------------------------------------------------------------

import os
from enum import StrEnum

import arcpy
import numpy as np
from osgeo import gdal

from .spatial import get_linear_unit
from .units import Area, Distance


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


# modified from - https://stackoverflow.com/questions/52443906/pixel-array-position-to-lat-long-gdal-python
def pixel_to_coordinate(gdal_dataset, x: int, y: int) -> tuple[float, float]:
    """Get coordinates from pixel in raster via GDAL dataset."""
    # get raster properties
    geotransform = gdal_dataset.GetGeoTransform()

    # raster properties
    originX = geotransform[0]
    pixelWidth = geotransform[1]
    xRot = geotransform[2]
    originY = geotransform[3]
    yRot = geotransform[4]
    pixelHeight = geotransform[5]

    # calculate coordinates from affine transformation
    x_coord = originX + (x + 0.5) * pixelWidth + y * xRot
    y_coord = originY + (y + 0.5) * pixelHeight + x * yRot

    return x_coord, y_coord


# modified from - https://stackoverflow.com/questions/52443906/pixel-array-position-to-lat-long-gdal-python
def coordinate_to_pixel(gdal_dataset, x: float, y: float) -> tuple[int, int]:
    """Get coordinates from pixel in raster via GDAL dataset."""
    # get raster properties
    geotransform = gdal_dataset.GetGeoTransform()

    # raster properties
    originX = geotransform[0]
    pixelWidth = geotransform[1]
    xRot = geotransform[2]
    originY = geotransform[3]
    yRot = geotransform[4]
    pixelHeight = geotransform[5]

    # calculate coordinates from affine transformation
    y_pixel = int((x - originX - y * xRot) / pixelWidth)
    x_pixel = int((y - originY - y * yRot) / pixelHeight)

    return x_pixel, y_pixel


# modified from - https://stackoverflow.com/questions/73115120/determine-coordinates-at-highest-point-of-raster
def raster_max_coordinates(input_raster: str | os.PathLike, mask=None) -> tuple[float, float, float]:
    """Find coordinates of max raster value.
    input_raster - raster path as string or path like object
    mask - masked area to ignore -
    """
    ds = gdal.Open(input_raster)

    # access size of file
    width = ds.RasterXSize
    height = ds.RasterYSize

    # access band and data as numpy arrays
    band = ds.GetRasterBand(1)
    data = band.ReadAsArray(0, 0, width, height).astype(float)

    if mask is not None:
        data = np.ma.array(data, mask=mask)

    indices = np.where(data == data.max()) # returns array([array([row]), array([col])])
    x = indices[1][0]
    y = indices[0][0]

    coords = pixel_to_coordinate(ds, x, y)
    value: float = data.max()

    return value, *coords


# modified from - https://stackoverflow.com/questions/44865023/how-can-i-create-a-circular-mask-for-a-numpy-array
def circular_mask(width: int, height: int, radius: float, center: tuple[float, float]):
    """Within raster width and height, create circle of radius at center."""
    yy, xx = np.mgrid[:height, :width]

    dist_from_center = np.sqrt((xx - center[1])**2 + (yy - center[0])**2)

    circle =  dist_from_center <= radius
    return circle
