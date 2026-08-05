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
}

class UNITS(StrEnum):
    """TODO."""
    # Handle the name or value of a unit being passed at creation time
    # Note: only applies to function invocation (eg - LINEAR_UNITS() not LINEAR_UNITS[])
    @classmethod
    def _missing_(cls, value):
        value = value.lower()
        for member in cls:
            if member.value == value or member.name == value:
                return member
        return None
    def __str__(self):
        return self.name
    def __repr__(self):
        return self.name
    def display(self):
        return self.value
    def __iter__(self):
        return [i.name for i in LINEAR_UNITS]

# inferred from https://developers.arcgis.com/rest/services-reference/enterprise/gp-data-types/#gplinearunit
# but accuracy is unclear since they only give "esriFeet" and other placeholders
# to test accuracy every GPLinearUnit was logged in a script
#
# map arcpy GPLinearUnit to parameter display representation
class LINEAR_UNITS(UNITS):
    Unknown = "Unknown"
    InchesInt = "International Inches"
    Inches = "US Survey Inches"
    FeetInt = "International Feet"
    Feet = "US Survey Feet"
    YardsInt = "International Yards"
    Yards = "US Survey Yards"
    MilesInt = "Statute Miles"
    Miles = "US Survey Miles"
    Millimeters = "Millimeters"
    Centimeters = "Centimeters"
    Decimeters = "Decimeters"
    Meters = "Meters"
    Kilometers = "Kilometers"
    NauticalMiles = "US Survey Nautical Miles"
    NauticalMilesInt = "International Nautical Miles"
    Points = "Points"
    DecimalDegrees = "Decimal Degrees"

    def to_areal(self) -> 'AREAL_UNITS':
        return AREAL_UNITS[LINEAR_TO_AREAL[self.name]]

    def to_spatial(self) -> 'SPATIAL_UNITS':
        return SPATIAL_UNITS[SPATIAL_TO_LINEAR[self.name]]

# https://developers.arcgis.com/rest/services-reference/enterprise/gp-data-types/#gparealunit
#
# map arcpy GPArealUnit to parameter display representation
class AREAL_UNITS(UNITS):
    Unknown = "Unknown"
    SquareInches = "Square International Inches"
    SquareInchesUS = "Square US Inches"
    SquareFeet = "Square International Feet"
    SquareFeetUS = "Square US Feet"
    SquareYards = "Square International Yards"
    SquareYardsUS = "Square US Yards"
    Acres = "International Acres"
    AcresUS = "US Survey Acres"
    SquareMiles = "Square Statute Miles"
    SquareMilesUS = "Square US Survey Miles"
    SquareMillimeters = "Square Millimeters"
    SquareCentimeters = "Square Centimeters"
    SquareDecimeters = "Square Decimeters"
    SquareMeters = "Square Meters"
    SquareKilometers = "Square Kilometers"
    Ares = "Ares"
    Hectares = "Hectares"

    def to_linear(self) -> LINEAR_UNITS:
        unit = self.name
        for key, value in LINEAR_TO_AREAL.items():
            if value == unit:
                unit = key
                break
        return LINEAR_UNITS[unit]


class SPATIAL_UNITS(UNITS):
    Meter = "Meter"
    Foot_US = "Foot_US"
    Foot = "Foot"

    def to_areal(self) -> AREAL_UNITS:
        return AREAL_UNITS[LINEAR_TO_AREAL[SPATIAL_TO_LINEAR[self.name]]]

    def to_linear(self) -> LINEAR_UNITS:
        return LINEAR_UNITS[SPATIAL_TO_LINEAR[self.name]]



def get_z_unit(fc) -> SPATIAL_UNITS | None:
    """Get z unit from spatial reference."""
    # find z unit of spatial reference vertical coordinate system
    desc = arcpy.Describe(fc)
    if desc.spatialReference.VCS:
        SPATIAL_UNITS[desc.spatialReference.VCS.linearUnitName]

    return None


def get_linear_unit(fc) -> LINEAR_UNITS:
    """Find linear unit from spatial reference."""
    # find linear unit from spatial reference
    try:
        desc = arcpy.Describe(fc)
        return LINEAR_UNITS[desc.spatialReference.linearUnitName]
    except Exception:
        return LINEAR_UNITS[fc.spatialReference.linearUnitName]

class BaseAmount:
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

class Distance(BaseAmount):
    # this project's type checker ty doesn't support singledispatchmethod yet :/
    # (https://github.com/astral-sh/ty/issues/2805)
    @singledispatchmethod
    def __init__(self, input):
        """Accepts distance and unit either:
        1) Separately:
           - Distance(4, "Feet")
           - Distance(5, "International Feet")
           - Distance(4, LINEAR_UNITS.FeetInt)
        2) Together:
           - Distance("4 Feet")
           - Distance("5 International Feet")
        """
        raise TypeError("Parameters must either be one of 1) input: str, unit: None 2) input: float | int, unit: LINEAR_UNITS. Received {}".format(input))
    @__init__.register
    def _(self, length: int | float, unit: str | LINEAR_UNITS):
        super().__init__(amount=length, unit=LINEAR_UNITS[unit])
    @__init__.register
    def _(self, quantity: str):
        length, unit, *rest = quantity.split(" ")
        if rest:
            unit += " " + " ".join(rest)
        super().__init__(amount=float(length), unit=LINEAR_UNITS[unit])
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
        """Convert Distance to output_unit factoring in length size."""
        self.length = self.length * arcpy.LinearUnitConversionFactor(self.unit, output_unit)
        self.unit = output_unit
        return self
    def __eq__(self: Self, other) -> bool:
        # Equals
        if not isinstance(other, Distance):
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

class Area(BaseAmount):
    # this project's type checker ty doesn't support singledispatchmethod yet :/
    # (https://github.com/astral-sh/ty/issues/2805)
    @singledispatchmethod
    def __init__(self, input):
        """Accepts area and unit either:
        1) Separately:
           - Area(4, "Acres")
           - Area(5, "International Acres")
           - Area(4, LINEAR_UNITS.Acres)
        2) Together:
           - Area("4 Acres")
           - Area("5 International Acres")
        """
        raise TypeError("Parameters must either be one of 1) input: str, unit: None 2) input: float | int, unit: AREAL_UNITS. Received {}".format(input))
    @__init__.register
    def _(self, area: int | float, unit: str | AREAL_UNITS):
        super().__init__(amount=area, unit=AREAL_UNITS[unit])
    @__init__.register
    def _(self, quantity: str):
        area, unit, *rest = quantity.split(" ")
        if rest:
            unit += " " + " ".join(rest)
        super().__init__(amount=float(area), unit=AREAL_UNITS[unit])
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
        """Convert Distance to output_unit factoring in area size."""
        self.area = self.area * arcpy.ArealUnitConversionFactor(self.unit, output_unit)
        self.unit = output_unit
        return self
    def __eq__(self: Self, other) -> bool:
        # Equals
        if not isinstance(other, Area):
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
