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

# mapping of spatial reference linear unit to GPLinearUnit
SPATIAL_TO_LINEAR = {
    "Meter": "Meters",
    "Foot_US": "Feet",
    "Foot": "FeetInt"
}

# z-units available to rasters for VCS
Z_UNITS = list(SPATIAL_TO_LINEAR.keys())

# inferred from https://developers.arcgis.com/rest/services-reference/enterprise/gp-data-types/#gplinearunit
# but accuracy is unclear since they only give "esriFeet" and other placeholders
# to test accuracy every GPLinearUnit was logged in a script
#
# maps parameter display representation to arcpy GPLinearUnit
LINEAR_UNITS_MAP = {
    "Unknown": "Unknown",
    "International Inches": "InchesInt",
    "US Survey Inches": "Inches",
    "International Feet": "FeetInt",
    "US Survey Feet": "Feet",
    "International Yards": "YardsInt",
    "US Survey Yards": "Yards",
    "Statute Miles": "MilesInt",
    "US Survey Miles": "Miles",
    "Millimeters": "Millimeters",
    "Centimeters": "Centimeters",
    "Decimeters": "Decimeters",
    "Meters": "Meters",
    "Kilometers": "Kilometers",
    "US Survey Nautical Miles": "NauticalMiles",
    "International Nautical Miles": "NauticalMilesInt",
    "Points": "Points",
    "Decimal Degrees": "DecimalDegrees",
}
LINEAR_UNITS = list(LINEAR_UNITS_MAP.keys())

# https://developers.arcgis.com/rest/services-reference/enterprise/gp-data-types/#gparealunit
#
# maps parameter display representation to arcpy GPArealUnit
AREAL_UNITS_MAP = {
    "Unknown": "Unknown",
    "Square International Inches": "SquareInches",
    "Square US Inches": "SquareInchesUS",
    "Square International Feet": "SquareFeet",
    "Square US Feet": "SquareFeetUS",
    "Square International Yards": "SquareYards",
    "Square US Yards": "SquareYardsUS",
    "International Acres": "Acres",
    "US Survey Acres": "AcresUS",
    "Square Statute Miles": "SquareMiles",
    "Square US Survey Miles": "SquareMilesUS",
    "Square Millimeters": "SquareMillimeters",
    "Square Centimeters": "SquareCentimeters",
    "Square Decimeters": "SquareDecimeters",
    "Square Meters": "SquareMeters",
    "Square Kilometers": "SquareKilometers",
    "Ares": "Ares",
    "Hectares": "Hectares",
}
AREAL_UNITS = list(AREAL_UNITS_MAP.keys())

# mapping of GPLinearUnit to GPArealUnit (square units)
# not all units have a mapping
#
# kind of annoying that the naming conventions change between
# linear and areal with respect to US / Int suffix
LINEAR_TO_AREAL = {
    "Unknown": "Unknown",
    "Inches": "SquareInchesUS",
    "InchesInt": "SquareInches",
    "Feet": "SquareFeetUS",
    "FeetInt": "SquareFeet",
    "Yards": "SquareYardsUS",
    "YardsInt": "SquareYards",
    "Miles": "SquareMilesUS",
    "MilesInt": "SquareMiles",
    "Millimeters": "SquareMillimeters",
    "Centimeters": "SquareCentimeters",
    "Decimeters": "SquareDecimeters",
    "Meters": "SquareMeters",
    "Kilometers": "SquareKilometers",
    "NauticalMiles": "Unknown",
    "NauticalMilesInt": "Unknown",
    "Points": "Unknown",
    "DecimalDegrees": "Unknown",
}

def convert_area(area: str, output_unit: str) -> str:
    """Convert AREA to OUTPUT_UNIT factoring in area size."""
    size, from_unit = area.split(" ")
    output_size = float(size) * arcpy.ArealUnitConversionFactor(from_unit, output_unit)
    output_area = "{} {}".format(output_size, output_unit)
    return output_area
