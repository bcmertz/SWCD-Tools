# -----------------------------------------------------------------------------------------
# Name:        Raster Info
# Purpose:     This package provides various convenience functions for working with rasters
#
# License:     GNU Affero General Public License v3.
#              Full license in LICENSE file, or at <https://www.gnu.org/licenses/>
# -----------------------------------------------------------------------------------------

import arcpy
from typing import Literal

def z_unit(raster) -> str | None:
    """Find z-unit of raster"""
    # find z unit of raster based on vertical coordinate system
    desc = arcpy.Describe(raster)
    if desc.spatialReference.VCS:
        if desc.spatialReference.VCS.linearUnitName == "Meter":
            return "METER"
        elif desc.spatialReference.VCS.linearUnitName == "Foot" or desc.spatialReference.VCS.linearUnitName == "Foot_US":
            return "FOOT"

    return None


UNITS = {
    "METER": 1.0,
    "FOOT": 3.2808,
    "INCH": 39.3696,
    "CENTIMETER": 100 
}

def z_factor(in_unit: Literal[UNITS.keys()], out_unit: Literal[UNITS.keys()], num: float) -> float:
    """Find z-factor of raster"""
    return num * UNITS[out_unit] / UNITS[in_unit]


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

def pixel_type(id):
    """return the the string representation of the raster pixel type"""
    return PIXEL_TYPES[id]
