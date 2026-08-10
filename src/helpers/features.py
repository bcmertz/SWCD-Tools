# -----------------------------------------------------------------------------------
# Name:        Features Helper
# Purpose:     This package contains various tools for working with arcpy features.
#
# License:     Contextual Copyleft AI (CCAI) License v1.0.
#              Full license in LICENSE file.
# -----------------------------------------------------------------------------------

import os

import arcpy

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
