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

def convert_area(area: str, output_unit: str) -> str:
    """Convert AREA to OUTPUT_UNIT factoring in area size."""
    size, from_unit = area.split(" ")
    output_size = float(size) * arcpy.ArealUnitConversionFactor(from_unit, output_unit)
    output_area = "{} {}".format(output_size, output_unit)
    return output_area
