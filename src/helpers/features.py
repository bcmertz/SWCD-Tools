# -----------------------------------------------------------------------------------
# Name:        Features Helper
# Purpose:     This package contains various tools for working with arcpy features.
#
# License:     Contextual Copyleft AI (CCAI) License v1.0.
#              Full license in LICENSE file.
# -----------------------------------------------------------------------------------

import os
from typing import Literal

import arcpy

from helpers.logging import warn


def fc_to_geometry(fc, keep_fields: list[str]):
    # geometry = arcpy.management.CopyFeatures(fc, arcpy.Geometry())
    if "SHAPE@" not in keep_fields:
        keep_fields = ["SHAPE@"] + keep_fields

    # fc_type = fc.shapeType
    out_geo = [list(row) for row in arcpy.da.SearchCursor(fc, keep_fields)]

    return out_geo


def geometry_to_fc(geo: list[arcpy.Geometry], fc: str, spatial_reference: arcpy.SpatialReference):
    out_name = fc.split("\\")[-1]
    out_dir = os.path.dirname(fc)

    geo_type = geo.geometry

    out_fc = arcpy.management.CreateFeatureclass(out_dir, out_name, geo_type, spatial_reference)
    with arcpy.da.InsertCursor(out_fc, ["SHAPE@"]) as cursor:
        for g in geo:
            cursor.insertRow([g])

    return out_fc


def is_empty(fc):
    """Return boolean representing if the feature class is empty."""
    return int(arcpy.management.GetCount(fc)[0]) == 0


def find_field(fc, name: str | None=None, alias: str | None=None) -> arcpy.Field | None:
    """Get a list of fields for each feature class."""
    field_list = arcpy.ListFields(fc)
    for field in field_list:
        if field.aliasName == alias or field.name == name:
            return field


def list_user_fields(fc) -> set[str]:
    """List only user editable fields in a feature class - ie not required."""
    return {f for f in arcpy.ListFields(fc) if not f.required}


def delete_field_safely(fc, field_name: str | list[str] | set[str], method: Literal["DELETE_FIELDS", "KEEP_FIELDS"] = "DELETE_FIELDS") -> None:
    """Delete fields safely by removing required fields from consideration."""
    field_names = set(field_name)
    if method == "KEEP_FIELDS":
        delete_fields = {f.name for f in list_user_fields(fc)} - field_names
        arcpy.management.DeleteField(fc, list(delete_fields), method="DELETE_FIELDS")
    elif method == "DELETE_FIELDS":
        unable_to_delete = field_names - {f.name for f in list_user_fields(fc)}
        if unable_to_delete:
            warn(f"Unable to delete: {unable_to_delete}, likely due to being required field(s)")
            field_names = field_names - unable_to_delete
        if not field_names:
            warn("No fields able to be deleted from supplied field names")
        else:
            arcpy.management.DeleteField(fc, list(field_names), method="DELETE_FIELDS")
    else:
        raise ValueError
