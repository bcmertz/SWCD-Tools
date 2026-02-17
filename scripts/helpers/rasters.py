# -----------------------------------------------------------------------------------
# Name:        Raster Helper
# Purpose:     This package contains various tools for working with rasters.
#
# License:     GNU Affero General Public License v3.
#              Full license in LICENSE file, or at <https://www.gnu.org/licenses/>
# -----------------------------------------------------------------------------------

import arcpy
import math

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


def cell_size(raster, output_unit_source=None):
    """Return the cell size of a raster in the linear units of another data source."""
    output_unit = "FeetUS"
    if output_unit_source:
        output_unit = arcpy.Describe(output_unit_source).spatialReference.linearUnitName

    # Note: throws an error if not a raster, this is desirable and shouldn't be used on
    # data types other than a raster
    desc_raster = arcpy.Describe(raster)
    raster_linear_unit = desc_raster.spatialReference.linearUnitName

    # Cell size in the X and Y axis
    cellsize_y = desc_raster.meanCellHeight * arcpy.LinearUnitConversionFactor(raster_linear_unit, output_unit)
    cellsize_x = desc_raster.meanCellWidth * arcpy.LinearUnitConversionFactor(raster_linear_unit, output_unit)

    return math.sqrt(cellsize_x * cellsize_y)

def min_cell_path(parameters):
    """Return the parameter with the smallest cell size."""
    min_cell_size = None
    min_cell_path = None
    for param in parameters:
        try:
            size = cell_size(param.value)
            if min_cell_size is None or size < min_cell_size:
                min_cell_size = size
                min_cell_path = param.valueAsText
        except:
            pass

    return min_cell_path
