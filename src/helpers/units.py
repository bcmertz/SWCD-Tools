# -----------------------------------------------------------------------------------------
# Name:        Units
# Purpose:     This package provides various convenience functions for working arcpy units
#
# License:     Contextual Copyleft AI (CCAI) License v1.0.
#              Full license in LICENSE file.
# -----------------------------------------------------------------------------------------

import arcpy
from copy import copy
from typing import Self
from functools import singledispatchmethod
from enum import StrEnum

# inferred from https://developers.arcgis.com/rest/services-reference/enterprise/gp-data-types/#gplinearunit
# but accuracy is unclear since they only give "esriFeet" and other placeholders
# to test accuracy every GPLinearUnit was logged in a script
#
# map arcpy GPLinearUnit to parameter display representation
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
LINEAR_UNITS = StrEnum("LINEAR_UNITS", {i: i for i in LINEAR_UNITS_MAP.values()})


# https://developers.arcgis.com/rest/services-reference/enterprise/gp-data-types/#gparealunit
#
# map arcpy GPArealUnit to parameter display representation
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
AREAL_UNITS = StrEnum("AREAL_UNITS", {i: i for i in AREAL_UNITS_MAP.values()})


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
    "Foot": "FeetInt",
    "Unknown": "Unknown",
}

# z-units available to rasters for VCS
Z_UNITS = list(set(SPATIAL_TO_LINEAR.keys()) - LINEAR_UNITS.Unkown)


def get_z_unit(fc) -> LINEAR_UNITS:
    """Get z unit from spatial reference."""
    # find z unit of spatial reference vertical coordinate system
    desc = arcpy.Describe(fc)
    if desc.spatialReference.VCS:
        return LINEAR_UNITS[SPATIAL_TO_LINEAR[desc.spatialReference.VCS.linearUnitName]]

    return LINEAR_UNITS.Unknown


def get_linear_unit(fc) -> LINEAR_UNITS:
    """Find linear unit from spatial reference."""
    # find linear unit from spatial reference
    try:
        desc = arcpy.Describe(fc)
        return LINEAR_UNITS[desc.spatialReference.linearUnitName]
    except Exception:
        return LINEAR_UNITS[fc.spatialReference.linearUnitName]

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
        out = copy(self)
        out.amount *= scalar
        return out
    def __truediv__(self: Self, divisor: int | float) -> Self:
        # Divide
        out = copy(self)
        out.amount /= divisor
        return out
    def __mod__(self: Self, divisor: int | float) -> Self:
        # Modulo
        out = copy(self)
        out.amount %= divisor
        return out
    def __floordiv__(self: Self, divisor: int | float) -> Self:
        # Integer division
        out = copy(self)
        out.amount = out.amount // divisor
        return out

class LinearUnit(BaseUnit):
    # this project's type checker ty doesn't support singledispatchmethod yet :/
    # (https://github.com/astral-sh/ty/issues/2805)
    @singledispatchmethod
    def __init__(self, input):
        """Accepts distance and unit either:
        1) Separately:
           - LinearUnit(4, "Feet")
           - LinearUnit(5, "International Feet")
           - LinearUnit(4, LINEAR_UNITS.FeetInt)
        2) Together:
           - LinearUnit("4 Feet")
           - LinearUnit("5 International Feet")
        """
        raise TypeError("Parameters must either be one of 1) input: str, unit: None 2) input: float | int, unit: LINEAR_UNITS. Received {}".format(input))
    @__init__.register
    def _(self, quantity: str):
        length, unit, *rest = quantity.split(" ")
        if rest:
            unit += " " + " ".join(rest)
            unit = LINEAR_UNITS_MAP[unit]
        super().__init__(amount=float(length), unit=LINEAR_UNITS[unit])
    @__init__.register
    def _(self, length: int | float, unit: str | LINEAR_UNITS):
        unit, *rest = unit.split(" ")
        if rest:
            unit += " " + " ".join(rest)
            unit = LINEAR_UNITS_MAP[unit]
        super().__init__(amount=length, unit=LINEAR_UNITS[unit])
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
        """Return full string description of LINEAR_UNIT stored in LINEAR_UNITS_MAP."""
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
        out = copy(self)
        out.length += other_length
        return out
    def __sub__(self: Self, other: Self) -> Self:
        other_length = other.length * arcpy.LinearUnitConversionFactor(other.unit, self.unit)
        out = copy(self)
        out.length -= other_length
        return out

class ArealUnit(BaseUnit):
    # this project's type checker ty doesn't support singledispatchmethod yet :/
    # (https://github.com/astral-sh/ty/issues/2805)
    @singledispatchmethod
    def __init__(self, input):
        """Accepts area and unit either:
        1) Separately:
           - ArealUnit(4, "Acres")
           - ArealUnit(5, "International Acres")
           - ArealUnit(4, LINEAR_UNITS.Acres)
        2) Together:
           - ArealUnit("4 Acres")
           - ArealUnit("5 International Acres")
        """
        raise TypeError("Parameters must either be one of 1) input: str, unit: None 2) input: float | int, unit: AREAL_UNITS. Received {}".format(input))
    @__init__.register
    def _(self, quantity: str):
        area, unit, *rest = quantity.split(" ")
        if rest:
            unit += " " + " ".join(rest)
            unit = AREAL_UNITS_MAP[unit]
        super().__init__(amount=float(area), unit=AREAL_UNITS[unit])
    @__init__.register
    def _(self, area: int | float, unit: str | AREAL_UNITS):
        unit, *rest = unit.split(" ")
        if rest:
            unit += " " + " ".join(rest)
            unit = AREAL_UNITS_MAP[unit]
        super().__init__(amount=area, unit=AREAL_UNITS[unit])
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
        """Return full string description of AREAL_UNIT stored in AREAL_UNITS_MAP."""
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
        out = copy(self)
        out.area += other_area
        return out
    def __sub__(self: Self, other: Self) -> Self:
        other_area = other.area * arcpy.ArealUnitConversionFactor(other.unit, self.unit)
        out = copy(self)
        out.area -= other_area
        return out
