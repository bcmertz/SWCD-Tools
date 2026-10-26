# -----------------------------------------------------------------------------------
# Name:        Features Helper
# Purpose:     This package contains various tools for working with arcpy features.
#
# License:     Contextual Copyleft AI (CCAI) License v1.0.
#              Full license in LICENSE file.
# -----------------------------------------------------------------------------------

import arcpy

from .units import LINEAR_UNITS, SPATIAL_UNITS


def get_z_unit(fc) -> SPATIAL_UNITS | None:
    """Get z unit from spatial reference."""
    # find z unit of spatial reference vertical coordinate system
    desc = arcpy.Describe(fc)
    if desc.spatialReference.VCS:
        return SPATIAL_UNITS[desc.spatialReference.VCS.linearUnitName]

    return None


def get_linear_unit(data) -> LINEAR_UNITS:
    """Find linear unit from spatial reference."""
    # find linear unit from spatial reference
    try:
        desc = arcpy.Describe(data)
        try:
            return SPATIAL_UNITS[desc.spatialReference.linearUnitName].to_linear()
        except Exception:
            return LINEAR_UNITS[desc.spatialReference.linearUnitName]
    except Exception:
        try:
            return SPATIAL_UNITS[data.spatialReference.linearUnitName].to_linear()
        except Exception:
            return LINEAR_UNITS[data.spatialReference.linearUnitName]
