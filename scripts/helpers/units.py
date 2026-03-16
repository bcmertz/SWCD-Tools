# -----------------------------------------------------------------------------------------
# Name:        Units
# Purpose:     This package provides various convenience functions for working arcpy units
#
# License:     Contextual Copyleft AI (CCAI) License v1.0.
#              Full license in LICENSE file.
# -----------------------------------------------------------------------------------------

import arcpy

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
    try:
        desc = arcpy.Describe(fc)
        return desc.spatialReference.linearUnitName
    except:
        return fc.spatialReference.linearUnitName

# mapping of linear to areal (square) units
LINEAR_TO_AREAL = {
    "Kilometers": "SquareKilometers",
    "Meters": "SquareMeters",
    "Decimeters": "SquareDecimeters",
    "Centimeters": "SquareCentimeters",
    "Millimeters": "SquareMillimeters",
    "YardsInt": "SquareYards",
    "FeetInt": "SquareFeet",
    "InchesInt": "SquareInches",
    "MilesInt": "SquareMiles",
    "MilesUS": "SquareMilesUS",
    "YardsUS": "SquareYardsUS",
    "FeetUS": "SquareFeetUS",
    "InchesUS": "SquareInchesUS ",
    "NauticalMilesUS": "Unknown",
    "NauticalMilesInt": "Unknown",
}

LINEAR_UNITS = list(UNITS.keys())
AREAL_UNITS =list(UNITS.values())

def area_to_num_cells(raster, area: str) -> int | None:
    """Convert GPArealUnit AREA to the number of cells in the RASTER it is equivalent to."""
    threshold, threshold_unit = area.split(" ")
    try:
        desc = arcpy.Describe(raster)
        linear_unit = desc.spatialReference.linearUnitName
        cellsize_y = desc.meanCellHeight * arcpy.LinearUnitConversionFactor(linear_unit, "FeetUS")  # Cell size in the Y axis
        cellsize_x = desc.meanCellWidth * arcpy.LinearUnitConversionFactor(linear_unit, "FeetUS")   # Cell size in the X axis
        if linear_unit is None:
            return None
        cell_area_ft2 = cellsize_x * cellsize_y
        threshold = int(int(threshold) * arcpy.ArealUnitConversionFactor(threshold_unit, "SquareFeetUS") / cell_area_ft2) # number of cells
        return threshold
    except:
        return None
