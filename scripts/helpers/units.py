# -----------------------------------------------------------------------------------------
# Name:        Units
# Purpose:     This package provides various convenience functions for working arcpy units
#
# License:     GNU Affero General Public License v3.
#              Full license in LICENSE file, or at <https://www.gnu.org/licenses/>
# -----------------------------------------------------------------------------------------

import arcpy
from typing import Literal

def get_z_unit(fc) -> str | None:
    """Get z unit from spatial reference."""
    # find z unit of spatial reference vertical coordinate system
    desc = arcpy.Describe(fc)
    if desc.spatialReference.VCS:
        return desc.spatialReference.VCS.linearUnitName

    return None


def get_linear_unit(fc) -> str | None:
    """Find linear unit from spatial reference."""
    # find linear unit from spatial reference
    desc = arcpy.Describe(fc)
    return desc.spatialReference.linearUnitName


# mapping of z unit to linear unit names
UNITS = {
    "KILOMETER": "Kilometers",
    "METER": "Meters",
    "DECIMETER": "Decimeters",
    "MILLIMETER": "Millimeters",
    "CENTIMETER": "Centimeters",
    "NAUTICAL_MILE": "NauticalMilesInt",
    "MILE_US": "MilesInt",
    "YARD": "YardsInt",
    "FOOT": "FeetInt",
    "INCH": "InchesInt",
    "NAUTICAL_MILE": "NauticalMilesUS",
    "MILES_US": "MilesUS",
    "YARD": "YardsUS",
    "FOOT": "FeetUS",
    "INCH": "InchesUS",
}

##UNITS = {
##    "Kilometers": "KILOMETER",
##    "Meters": "METER",
##    "Decimeters": "DECIMETER",
##    "Millimeters": "MILLIMETER",
##    "Centimeters": "CENTIMETER",
##    "NauticalMilesInt": "NAUTICAL_MILE",
##    "MilesInt": "MILE_US",
##    "YardsInt": "YARD",
##    "FeetInt": "FOOT",
##    "InchesInt": "INCH",
##    "NauticalMilesUS": "NAUTICAL_MILE",
##    "MilesUS": "MILES_US",
##    "YardsUS": "YARD",
##    "FeetUS": "FOOT",
##    "InchesUS": "INCH",
##}

z_units = list(UNITS.keys())
linear_units = list(UNITS.values())

def z_unit_to_linear_unit(in_unit: Literal[UNITS.keys()]) -> Literal[UNITS.values()] | None:
    """Convert z unit to linear unit format."""
    return UNITS.get(in_unit, None)

def area_to_num_cells(raster, area: str) -> int | None:
    """Convert GPLinearUnit AREA to the number of cells in the RASTER it is equivalent to."""
    threshold, threshold_unit = area.split(" ")
    try:
        desc = arcpy.Describe(raster)
        linear_unit = desc.spatialReference.linearUnitName
        cellsize_y = desc.meanCellHeight * arcpy.LinearUnitConversionFactor(linear_unit, "FeetUS")  # Cell size in the Y axis
        cellsize_x = desc.meanCellWidth * arcpy.LinearUnitConversionFactor(linear_unit, "FeetUS")   # Cell size in the X axis
        if linear_unit == None:
            return None
        cell_area_ft2 = cellsize_x * cellsize_y
        threshold = int(int(threshold) * arcpy.ArealUnitConversionFactor(threshold_unit, "SquareFeetUS") / cell_area_ft2) # number of cells
        return threshold
    except:
        return None

