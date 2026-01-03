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
    """Get z unit from spatial reference"""
    # find z unit of spatial reference vertical coordinate system
    desc = arcpy.Describe(fc)
    if desc.spatialReference.VCS:
        if desc.spatialReference.VCS.linearUnitName == "Meter":
            return "METER"
        elif desc.spatialReference.VCS.linearUnitName == "Foot" or desc.spatialReference.VCS.linearUnitName == "Foot_US":
            return "FOOT"

    return None

def get_linear_unit(fc) -> str | None:
    """Find linear unit from spatial reference"""
    # find linear unit from spatial reference
    desc = arcpy.Describe(fc)
    if desc.spatialReference.linearUnitName == "Meter":
        return "METER"
    elif desc.spatialReference.linearUnitName == "Foot" or desc.spatialReference.linearUnitName == "Foot_US":
        return "FOOT"

    return None

UNITS = {
    "METER": 1.0,
    "FOOT": 3.2808,
    "INCH": 39.3696,
    "CENTIMETER": 100 
}

def convert_units(in_unit: Literal[UNITS.keys()], out_unit: Literal[UNITS.keys()], num: float) -> float:
    """Find z-factor of raster"""
    return num * UNITS[out_unit] / UNITS[in_unit]
