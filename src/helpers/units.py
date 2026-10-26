# -----------------------------------------------------------------------------------------
# Name:        Units
#
# Purpose:     The missing ArcGIS Pro units package. This package provides various convenience functions for working arcpy units
#              Much of this is motivated by the strange behavior and conventions of arcpy.LinearUnitConversionFactor
#              and arcpy.ArealUnitConversionFactor. These built-ins provide the standard interface for converting between
#              linear and areal units in ArcGIS Pro but have poorly defined behavior in terms of what units are all allowed
#              and how they are structured.
#
#              For example: arcpy.LinearUnitConversionFactor takes US feet as [Foot US, FootUS, Foot, Feet]
#              but not [US Survey Feet, Foot_US]. The documentation only specifies FeetUS as valid.
#              To make matters worse, the documentation for spatial units on raster vertical coordinate systems
#              and some geoprocessing tools like arcpy.sa.Slope specifies Foot_US as the proper format but takes many other
#              formats which aren't specified, including "US Survey Feet". Finally, GPLinearUnit parameters takes US Survey Feet
#              but returns Feet.
#
#              This package handles this complexity by rigidly defining LINEAR_UNITS, AREAL_UNITS, and SPATIAL_UNITS classes
#              and provides methods for converting between them. This is ingested by Distance and Area classes which provide
#              unit and amount of linear and areal measurements, as well as methods to convert and do math with these measurements.
#
# License:     Contextual Copyleft AI (CCAI) License v1.0.
#              Full license in LICENSE file.
# -----------------------------------------------------------------------------------------

import math
from copy import copy
from enum import StrEnum
from functools import singledispatchmethod
from typing import Self

import arcpy

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
    # Handle the name or value of a unit being passed at creation time
    # Note: only applies to function invocation (eg - LINEAR_UNITS() not LINEAR_UNITS[])
    #       so you can do LINEAR_UNITS(value | name | LINEAR_UNITS) but only names in LINEAR_UNITS[name]
    #
    ## yes
    # LINEAR_UNITS("FeetInt")
    # LINEAR_UNITS("International Feet")
    # LINEAR_UNITS(LINEAR_UNITS.FeetInt)
    # LINEAR_UNITS["FeetInt"]
    # LINEAR_UNITS.FeetInt
    #
    ## no
    # LINEAR_UNITS["International Feet"]
    # LINEAR_UNITS[LINEAR_UNITS.FeetInt]
    @classmethod
    def _missing_(cls, value):
        for member in cls:
            if (member.value == value) | (member.name == value):
                return member
        return None

    def __eq__(self, other):
        return (self.name == other) | (self.value == other)

    def __ne__(self, other):
        return not self.__eq__(other)

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name

    def __iter__(self):
        return [i.name for i in LINEAR_UNITS]

    def display(self):
        return self.value


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

    def to_areal(self) -> "AREAL_UNITS":
        return AREAL_UNITS[LINEAR_TO_AREAL[self.name]]

    def to_spatial(self) -> "SPATIAL_UNITS":
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


class SLOPE_UNITS(UNITS):
    Ratio = "Ratio"
    Percent = "Percent"
    Degrees = "Degrees"
    Radians = "Radians"


class FLOW_UNITS(UNITS):
    CFS = "ft^3/s"
    CMS = "m^3/s"


class SPATIAL_UNITS(UNITS):
    Meter = "Meter"
    Foot_US = "Foot_US"
    Foot = "Foot"

    def to_areal(self) -> AREAL_UNITS:
        return AREAL_UNITS[LINEAR_TO_AREAL[SPATIAL_TO_LINEAR[self.name]]]

    def to_linear(self) -> LINEAR_UNITS:
        return LINEAR_UNITS[SPATIAL_TO_LINEAR[self.name]]


class BaseAmount:
    def __init__(self: Self, amount: float | int, unit: LINEAR_UNITS | AREAL_UNITS | SLOPE_UNITS | FLOW_UNITS):
        self.amount = amount
        self.base_unit = unit

    def __str__(self) -> str:
        return f"{self.amount} {self.base_unit}"

    def __repr__(self) -> str:
        return f"{self.amount} {self.base_unit}"

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
        raise TypeError(
            f"Parameters must either be one of 1) input: str, unit: None 2) input: float | int, unit: str | LINEAR_UNITS. Received {input}"
        )

    @__init__.register
    def _(self, length: int | float, unit: str | LINEAR_UNITS):
        unit, *rest = unit.split(" ")
        if rest:
            unit += " " + " ".join(rest)
            super().__init__(amount=length, unit=LINEAR_UNITS(unit))
        else:
            super().__init__(amount=length, unit=LINEAR_UNITS[unit])

    @__init__.register
    def _(self, quantity: str):
        length, unit, *rest = quantity.split(" ")
        if rest:
            unit += " " + " ".join(rest)
            super().__init__(amount=float(length), unit=LINEAR_UNITS(unit))
        else:
            super().__init__(amount=float(length), unit=LINEAR_UNITS[unit])

    @property
    def length(self) -> int | float:
        return self.amount

    @length.setter
    def length(self: Self, value: int | float) -> None:
        self.amount = value

    @property
    def unit(self) -> LINEAR_UNITS:
        return LINEAR_UNITS(self.base_unit)

    @unit.setter
    def unit(self: Self, unit: LINEAR_UNITS) -> None:
        self.base_unit = unit

    def to_unit(self: Self, output_unit: LINEAR_UNITS) -> Self:
        """Convert Distance to output_unit factoring in length size."""
        out = copy(self)
        out.length = self.length * arcpy.LinearUnitConversionFactor(str(self.unit), str(output_unit))
        out.unit = output_unit
        return out

    def __eq__(self: Self, other) -> bool:
        # Equals
        if not isinstance(other, Distance):
            return False
        else:
            other_length = other.length * arcpy.LinearUnitConversionFactor(str(other.unit), str(self.unit))
            return self.length == other_length

    def __ne__(self: Self, other) -> bool:
        # Not equals
        return not self.__eq__(other)

    def __lt__(self: Self, other: Self) -> bool:
        # Less than
        other_length = other.length * arcpy.LinearUnitConversionFactor(str(other.unit), str(self.unit))
        return self.length < other_length

    def __gt__(self: Self, other: Self) -> bool:
        # Greater than
        other_length = other.length * arcpy.LinearUnitConversionFactor(str(other.unit), str(self.unit))
        return self.length > other_length

    def __le__(self: Self, other: Self) -> bool:
        # Less or equal
        other_length = other.length * arcpy.LinearUnitConversionFactor(str(other.unit), str(self.unit))
        return self.length <= other_length

    def __ge__(self: Self, other: Self) -> bool:
        # Greater or equal
        other_length = other.length * arcpy.LinearUnitConversionFactor(str(other.unit), str(self.unit))
        return self.length >= other_length

    def __add__(self: Self, other: Self) -> Self:
        other_length = other.length * arcpy.LinearUnitConversionFactor(str(other.unit), str(self.unit))
        out = copy(self)
        out.length += other_length
        return out

    def __sub__(self: Self, other: Self) -> Self:
        other_length = other.length * arcpy.LinearUnitConversionFactor(str(other.unit), str(self.unit))
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
        raise TypeError(
            f"Parameters must either be one of 1) input: str, unit: None 2) input: float | int, unit: str | AREAL_UNITS. Received {input}"
        )

    @__init__.register
    def _(self, area: int | float, unit: str | AREAL_UNITS):
        unit, *rest = unit.split(" ")
        if rest:
            unit += " " + " ".join(rest)
            super().__init__(amount=area, unit=AREAL_UNITS(unit))
        else:
            super().__init__(amount=area, unit=AREAL_UNITS[unit])

    @__init__.register
    def _(self, quantity: str):
        area, unit, *rest = quantity.split(" ")
        if rest:
            unit += " " + " ".join(rest)
            super().__init__(amount=float(area), unit=AREAL_UNITS(unit))
        else:
            super().__init__(amount=float(area), unit=AREAL_UNITS[unit])

    @property
    def area(self) -> int | float:
        return self.amount

    @area.setter
    def area(self: Self, value: int | float) -> None:
        self.amount = value

    @property
    def unit(self) -> AREAL_UNITS:
        return AREAL_UNITS(self.base_unit)

    @unit.setter
    def unit(self: Self, unit: AREAL_UNITS) -> None:
        self.base_unit = unit

    def to_unit(self: Self, output_unit: AREAL_UNITS) -> Self:
        """Convert Distance to output_unit factoring in area size."""
        out = copy(self)
        out.area = self.area * arcpy.ArealUnitConversionFactor(str(self.unit), str(output_unit))
        out.unit = output_unit
        return out

    def __eq__(self: Self, other) -> bool:
        # Equals
        if not isinstance(other, Area):
            return False
        else:
            other_area = other.area * arcpy.ArealUnitConversionFactor(str(other.unit), str(self.unit))
            return self.area == other_area

    def __ne__(self: Self, other) -> bool:
        # Not equals
        return not self.__eq__(other)

    def __lt__(self: Self, other: Self) -> bool:
        # Less than
        other_area = other.length * arcpy.ArealUnitConversionFactor(str(other.unit), str(self.unit))
        return self.length < other_area

    def __gt__(self: Self, other: Self) -> bool:
        # Greater than
        other_area = other.area * arcpy.ArealUnitConversionFactor(str(other.unit), str(self.unit))
        return self.area > other_area

    def __le__(self: Self, other: Self) -> bool:
        # Less or equal
        other_area = other.area * arcpy.ArealUnitConversionFactor(str(other.unit), str(self.unit))
        return self.area <= other_area

    def __ge__(self: Self, other: Self) -> bool:
        # Greater or equal
        other_area = other.area * arcpy.ArealUnitConversionFactor(str(other.unit), str(self.unit))
        return self.area >= other_area

    def __add__(self: Self, other: Self) -> Self:
        other_area = other.area * arcpy.ArealUnitConversionFactor(str(other.unit), str(self.unit))
        out = copy(self)
        out.area += other_area
        return out

    def __sub__(self: Self, other: Self) -> Self:
        other_area = other.area * arcpy.ArealUnitConversionFactor(str(other.unit), str(self.unit))
        out = copy(self)
        out.area -= other_area
        return out


class Flow(BaseAmount):
    # this project's type checker ty doesn't support singledispatchmethod yet :/
    # (https://github.com/astral-sh/ty/issues/2805)
    @singledispatchmethod
    def __init__(self, input):
        """Accepts distance and unit either:
        1) Separately:
           - Flow(4, "CFS")
           - Flow(5, "cf^3")
           - Flow(4, FLOW_UNITS.CFS)
        2) Together:
           - Flow("4 CFS")
           - Flow("5 cf^3")
        """
        raise TypeError(
            f"Parameters must either be one of 1) input: str, unit: None 2) input: float | int, unit: str | FLOW_UNITS. Received {input}"
        )

    @__init__.register
    def _(self, discharge: int | float, unit: str | FLOW_UNITS):
        unit, *rest = unit.split(" ")
        if rest:
            unit += " " + " ".join(rest)
            super().__init__(amount=discharge, unit=FLOW_UNITS(unit))
        else:
            super().__init__(amount=discharge, unit=FLOW_UNITS[unit])

    @__init__.register
    def _(self, quantity: str):
        discharge, unit, *rest = quantity.split(" ")
        if rest:
            unit += " " + " ".join(rest)
            super().__init__(amount=float(discharge), unit=FLOW_UNITS(unit))
        else:
            super().__init__(amount=float(discharge), unit=FLOW_UNITS[unit])

    @property
    def discharge(self) -> int | float:
        return self.amount

    @discharge.setter
    def discharge(self: Self, value: int | float) -> None:
        self.amount = value

    @property
    def unit(self) -> FLOW_UNITS:
        return FLOW_UNITS(self.base_unit)

    @unit.setter
    def unit(self: Self, unit: FLOW_UNITS) -> None:
        self.base_unit = unit

    def to_unit(self: Self, to_unit: FLOW_UNITS) -> Self:
        out = copy(self)
        match self.unit:
            case FLOW_UNITS.CFS:
                match to_unit:
                    case FLOW_UNITS.CFS:
                        out.flow = self.discharge
                    case FLOW_UNITS.CMS:
                        out.discharge = self.discharge * 0.028317
            case FLOW_UNITS.CMS:
                match to_unit:
                    case FLOW_UNITS.CFS:
                        out.discharge = self.discharge / 0.028317
                    case FLOW_UNITS.CMS:
                        out.discharge = self.discharge
        out.unit = to_unit
        return out

    def __eq__(self: Self, other) -> bool:
        # Equals
        if not isinstance(other, Flow):
            return False
        else:
            other_discharge = other.to_unit(self.unit).discharge
            return self.discharge == other_discharge

    def __ne__(self: Self, other) -> bool:
        # Not equals
        return not self.__eq__(other)

    def __lt__(self: Self, other: Self) -> bool:
        # Less than
        other_discharge = other.to_unit(self.unit).discharge
        return self.discharge < other_discharge

    def __gt__(self: Self, other: Self) -> bool:
        # Greater than
        other_discharge = other.to_unit(self.unit).discharge
        return self.discharge > other_discharge

    def __le__(self: Self, other: Self) -> bool:
        # Less or equal
        other_discharge = other.to_unit(self.unit).discharge
        return self.discharge <= other_discharge

    def __ge__(self: Self, other: Self) -> bool:
        # Greater or equal
        other_discharge = other.to_unit(self.unit).discharge
        return self.discharge >= other_discharge

    def __add__(self: Self, other: Self) -> Self:
        other_discharge = other.to_unit(self.unit).discharge
        out = copy(self)
        out.discharge += other_discharge
        return out

    def __sub__(self: Self, other: Self) -> Self:
        other_discharge = other.to_unit(self.unit).discharge
        out = copy(self)
        out.discharge -= other_discharge
        return out


class Slope(BaseAmount):
    # this project's type checker ty doesn't support singledispatchmethod yet :/
    # (https://github.com/astral-sh/ty/issues/2805)
    @singledispatchmethod
    def __init__(self, input):
        """Accepts distance and unit either:
        1) Separately:
           - Slope(4, "CFS")
           - Slope(5, "cf^3")
           - Slope(4, SLOPE_UNITS.CFS)
        2) Together:
           - Slope("4 CFS")
           - Slope("5 cf^3")
        """
        raise TypeError(
            f"Parameters must either be one of 1) input: str, unit: None 2) input: float | int, unit: str | SLOPE_UNITS. Received {input}"
        )

    @__init__.register
    def _(self, slope: int | float, unit: str | SLOPE_UNITS):
        unit, *rest = unit.split(" ")
        if rest:
            unit += " " + " ".join(rest)
            super().__init__(amount=slope, unit=SLOPE_UNITS(unit))
        else:
            super().__init__(amount=slope, unit=SLOPE_UNITS[unit])

    @__init__.register
    def _(self, quantity: str):
        slope, unit, *rest = quantity.split(" ")
        if rest:
            unit += " " + " ".join(rest)
            super().__init__(amount=float(slope), unit=SLOPE_UNITS(unit))
        else:
            super().__init__(amount=float(slope), unit=SLOPE_UNITS[unit])

    @property
    def slope(self) -> int | float:
        return self.amount

    @slope.setter
    def slope(self: Self, value: int | float) -> None:
        self.amount = value

    @property
    def unit(self) -> SLOPE_UNITS:
        return SLOPE_UNITS(self.base_unit)

    @unit.setter
    def unit(self: Self, unit: SLOPE_UNITS) -> None:
        self.base_unit = unit

    def to_unit(self: Self, to_unit: SLOPE_UNITS) -> Self:
        out = copy(self)
        match self.unit:
            case SLOPE_UNITS.Degrees:
                match to_unit:
                    case SLOPE_UNITS.Degrees:
                        out.slope = self.slope
                    case SLOPE_UNITS.Radians:
                        out.slope = math.radians(self.slope)
                    case SLOPE_UNITS.Percent:
                        out.slope = math.tan(math.radians(self.slope))*100
                    case SLOPE_UNITS.Ratio:
                        out.slope = math.tan(math.radians(self.slope))
            case SLOPE_UNITS.Radians:
                match to_unit:
                    case SLOPE_UNITS.Degrees:
                        out.slope = math.degrees(self.slope)
                    case SLOPE_UNITS.Radians:
                        out.slope = self.slope
                    case SLOPE_UNITS.Percent:
                        out.slope = self.to_unit(SLOPE_UNITS.Degrees).to_unit(SLOPE_UNITS.Percent).slope
                    case SLOPE_UNITS.Ratio:
                        out.slope = self.to_unit(SLOPE_UNITS.Percent).to_unit(SLOPE_UNITS.Ratio).slope
            case SLOPE_UNITS.Percent:
                match to_unit:
                    case SLOPE_UNITS.Degrees:
                        out.slope = math.degrees(math.atan(self.slope / 100))
                    case SLOPE_UNITS.Radians:
                        out.slope = math.radians(self.to_unit(SLOPE_UNITS.Degrees).slope)
                    case SLOPE_UNITS.Percent:
                        out.slope = self.slope
                    case SLOPE_UNITS.Ratio:
                        out.slope = self.slope / 100
            case SLOPE_UNITS.Ratio:
                match to_unit:
                    case SLOPE_UNITS.Degrees:
                        out.slope = self.to_unit(SLOPE_UNITS.Percent).to_unit(SLOPE_UNITS.Degrees).slope
                    case SLOPE_UNITS.Radians:
                        out.slope = self.to_unit(SLOPE_UNITS.Percent).to_unit(SLOPE_UNITS.Radians).slope
                    case SLOPE_UNITS.Percent:
                        out.slope = self.slope * 100
                    case SLOPE_UNITS.Ratio:
                        out.slope = self.slope
        out.unit = to_unit
        return out

    def __eq__(self: Self, other) -> bool:
        # Equals
        if not isinstance(other, Slope):
            return False
        else:
            other_slope = other.to_unit(self.unit).slope
            return self.slope == other_slope

    def __ne__(self: Self, other) -> bool:
        # Not equals
        return not self.__eq__(other)

    def __lt__(self: Self, other: Self) -> bool:
        # Less than
        other_slope = other.to_unit(self.unit).slope
        return self.slope < other_slope

    def __gt__(self: Self, other: Self) -> bool:
        # Greater than
        other_slope = other.to_unit(self.unit).slope
        return self.slope > other_slope

    def __le__(self: Self, other: Self) -> bool:
        # Less or equal
        other_slope = other.to_unit(self.unit).slope
        return self.slope <= other_slope

    def __ge__(self: Self, other: Self) -> bool:
        # Greater or equal
        other_slope = other.to_unit(self.unit).slope
        return self.slope >= other_slope

    def __add__(self: Self, other: Self) -> Self:
        other_slope = other.to_unit(self.unit).slope
        out = copy(self)
        out.slope += other_slope
        return out

    def __sub__(self: Self, other: Self) -> Self:
        other_slope = other.to_unit(self.unit).slope
        out = copy(self)
        out.slope -= other_slope
        return out
