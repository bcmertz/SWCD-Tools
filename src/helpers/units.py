# -----------------------------------------------------------------------------------------
# Name:        Units
# Purpose:     This package provides various convenience functions for working arcpy units
#
# License:     Contextual Copyleft AI (CCAI) License v1.0.
#              Full license in LICENSE file.
# -----------------------------------------------------------------------------------------

import arcpy
from typing import Self
from enum import StrEnum

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
    except Exception:
        return fc.spatialReference.linearUnitName


# inferred from https://developers.arcgis.com/rest/services-reference/enterprise/gp-data-types/#gplinearunit
# but accuracy is unclear since they only give "esriFeet" and other placeholders
# to test accuracy every GPLinearUnit was logged in a script
#
# map arcpy GPLinearUnit to parameter display representation
LINEAR_UNITS_MAP = {
    "Unknown" : "Unknown",
    "International Inches" : "InchesInt",
    "US Survey Inches" : "Inches",
    "International Feet" : "FeetInt",
    "US Survey Feet" : "Feet",
    "International Yards" : "YardsInt",
    "US Survey Yards" : "Yards",
    "Statute Miles" : "MilesInt",
    "US Survey Miles" : "Miles",
    "Millimeters" : "Millimeters",
    "Centimeters" : "Centimeters",
    "Decimeters" : "Decimeters",
    "Meters" : "Meters",
    "Kilometers" : "Kilometers",
    "US Survey Nautical Miles" : "NauticalMiles",
    "International Nautical Miles" : "NauticalMilesInt",
    "Points" : "Points",
    "Decimal Degrees" : "DecimalDegrees",
}
LINEAR_UNITS = StrEnum("LINEAR_UNITS", {
    i: i for i in LINEAR_UNITS_MAP.values()
})


# https://developers.arcgis.com/rest/services-reference/enterprise/gp-data-types/#gparealunit
#
# map arcpy GPArealUnit to parameter display representation
AREAL_UNITS_MAP = {
    "Unknown" : "Unknown",
    "Square International Inches" : "SquareInches",
    "Square US Inches" : "SquareInchesUS",
    "Square International Feet" : "SquareFeet",
    "Square US Feet" : "SquareFeetUS",
    "Square International Yards" : "SquareYards",
    "Square US Yards" : "SquareYardsUS",
    "International Acres" : "Acres",
    "US Survey Acres" : "AcresUS",
    "Square Statute Miles" : "SquareMiles",
    "Square US Survey Miles" : "SquareMilesUS",
    "Square Millimeters" : "SquareMillimeters",
    "Square Centimeters" : "SquareCentimeters",
    "Square Decimeters" : "SquareDecimeters",
    "Square Meters" : "SquareMeters",
    "Square Kilometers" : "SquareKilometers",
    "Ares" : "Ares",
    "Hectares" : "Hectares",
}
AREAL_UNITS = StrEnum("AREAL_UNITS", {
    i: i for i in AREAL_UNITS_MAP.values()
})


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

# mapping of spatial reference linear unit to GPLinearUnit
SPATIAL_TO_LINEAR = {
    "Meter": "Meters",
    "Foot_US": "Feet",
    "Foot": "FeetInt"
}

# z-units available to rasters for VCS
Z_UNITS = list(SPATIAL_TO_LINEAR.keys())


class BaseUnit:
    def __init__(self: Self, amount: float | int, unit: LINEAR_UNITS | AREAL_UNITS):
        self.amount = amount
        self.base_unit = unit
    def __str__(self) -> str:
        return "{} {}".format(self.amount, self.base_unit)
    def __repr__(self) -> str:
        return "{} {}".format(self.amount, self.base_unit)
    def __mul__(self: Self, scalar: int | float) -> Self:
        # Multiply
        self.amount *= scalar
        return self
    def __truediv__(self: Self, divisor: int | float) -> Self:
        # Divide
        self.amount *= divisor
        return self
    def __mod__(self: Self, divisor: int | float) -> Self:
        # Modulo
        self.amount %= divisor
        return self
    def __floordiv__(self: Self, divisor: int | float) -> Self:
        # Integer division
        self.amount  = self.amount // divisor
        return self

class LinearUnit(BaseUnit):
    def __init__(self: Self, input: str):
        length, unit_str, *rest = input.split(" ")
        if rest is not None:
            unit_str += " " + " ".join(rest)
            unit_str = LINEAR_UNITS_MAP[unit_str]
        super().__init__(amount=float(length), unit=LINEAR_UNITS[unit_str])
    @property
    def length(self) -> int | float:
        return self.amount
    @length.setter
    def length(self: Self, value: int | float) -> None:
        self.amount = value
        return
    @property
    def unit(self) -> LINEAR_UNITS:
        return LINEAR_UNITS[self.base_unit]
    @unit.setter
    def unit(self: Self, unit: LINEAR_UNITS) -> None:
        self.base_unit = unit
        return
    def to_unit(self: Self, output_unit: LINEAR_UNITS) -> Self:
        """Convert LinearUnit to output_unit factoring in length size."""
        self.length = self.length * arcpy.LinearUnitConversionFactor(self.unit, output_unit)
        self.unit = output_unit
        return self
    def full_unit(self: Self) -> str:
        unit = self.unit
        for key, value in LINEAR_UNITS_MAP.items():
            if value == unit:
                unit = key
                break
        return unit
    def __eq__(self: Self, other) -> bool:
        # Equals
        if not isinstance(other, LinearUnit):
            return False
        else:
            other_length = other.length * arcpy.LinearUnitConversionFactor(other.unit, self.unit)
            return self.length == other_length
    def __ne__(self: Self, other) -> bool:
        # Not equals
        return not self.__eq__(other)
    def __lt__(self: Self, other: Self) -> bool:
        # Less than
        other_length = other.length * arcpy.LinearUnitConversionFactor(other.unit, self.unit)
        return self.length < other_length
    def __gt__(self: Self, other: Self) -> bool:
        # Greater than
        other_length = other.length * arcpy.LinearUnitConversionFactor(other.unit, self.unit)
        return self.length > other_length
    def __le__(self: Self, other: Self) -> bool:
        # Less or equal
        other_length = other.length * arcpy.LinearUnitConversionFactor(other.unit, self.unit)
        return self.length <= other_length
    def __ge__(self: Self, other: Self) -> bool:
        # Greater or equal
        other_length = other.length * arcpy.LinearUnitConversionFactor(other.unit, self.unit)
        return self.length >= other_length
    def __add__(self: Self, other: Self) -> Self:
        other_length = other.length * arcpy.LinearUnitConversionFactor(other.unit, self.unit)
        self.length += other_length
        return self
    def __sub__(self: Self, other: Self) -> Self:
        other_length = other.length * arcpy.LinearUnitConversionFactor(other.unit, self.unit)
        self.length -= other_length
        return self

class ArealUnit(BaseUnit):
    def __init__(self: Self, input: str):
        area, unit_str, *rest = input.split(" ")
        if rest is not None:
            unit_str += " " + " ".join(rest)
            unit_str = AREAL_UNITS_MAP[unit_str]
        super().__init__(amount=float(area), unit=AREAL_UNITS[unit_str])
    @property
    def area(self) -> int | float:
        return self.amount
    @area.setter
    def area(self: Self, value: int | float) -> None:
        self.amount = value
        return
    @property
    def unit(self) -> AREAL_UNITS:
        return AREAL_UNITS[self.base_unit]
    @unit.setter
    def unit(self: Self, unit: AREAL_UNITS) -> None:
        self.base_unit = unit
        return
    def to_unit(self: Self, output_unit: AREAL_UNITS) -> Self:
        """Convert LinearUnit to output_unit factoring in area size."""
        self.area = self.area * arcpy.ArealUnitConversionFactor(self.unit, output_unit)
        self.unit = output_unit
        return self
    def full_unit(self: Self) -> str:
        unit = self.unit
        for key, value in AREAL_UNITS_MAP.items():
            if value == unit:
                unit = key
                break
        return unit
    def __eq__(self: Self, other) -> bool:
        # Equals
        if not isinstance(other, ArealUnit):
            return False
        else:
            other_area = other.area * arcpy.ArealUnitConversionFactor(other.unit, self.unit)
            return self.area == other_area
    def __ne__(self: Self, other) -> bool:
        # Not equals
        return not self.__eq__(other)
    def __lt__(self: Self, other: Self) -> bool:
        # Less than
        other_area = other.length * arcpy.ArealUnitConversionFactor(other.unit, self.unit)
        return self.length < other_area
    def __gt__(self: Self, other: Self) -> bool:
        # Greater than
        other_area = other.area * arcpy.ArealUnitConversionFactor(other.unit, self.unit)
        return self.area > other_area
    def __le__(self: Self, other: Self) -> bool:
        # Less or equal
        other_area = other.area * arcpy.ArealUnitConversionFactor(other.unit, self.unit)
        return self.area <= other_area
    def __ge__(self: Self, other: Self) -> bool:
        # Greater or equal
        other_area = other.area * arcpy.ArealUnitConversionFactor(other.unit, self.unit)
        return self.area >= other_area
    def __add__(self: Self, other: Self) -> Self:
        other_area = other.area * arcpy.ArealUnitConversionFactor(other.unit, self.unit)
        self.area += other_area
        return self
    def __sub__(self: Self, other: Self) -> Self:
        other_area = other.area * arcpy.ArealUnitConversionFactor(other.unit, self.unit)
        self.area -= other_area
        return self
