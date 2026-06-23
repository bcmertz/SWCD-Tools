# ---------------------------------------------------------------------------------
# Name:        Geometry Helper
# Purpose:     This package contains various helpers and tools for analyzing geometry.
#
# License:     Contextual Copyleft AI (CCAI) License v1.0.
#              Full license in LICENSE file.
# ---------------------------------------------------------------------------------


import arcpy
import numpy as np
from scipy.spatial import Delaunay
from numpy.lib.recfunctions import structured_to_unstructured as stu

# modified from https://github.com/Dan-Patterson/numpy_geometry/blob/master/arcpro_npg/npg/npg/npg_arc_npg.py#L639
def fc_to_numpy_array(in_fc):
    """Get the geometry from a feature class and clean it up into a numpy.ndarray.
    Returns either a structured or unstructured numpy.ndarray.
    """
    arr = arcpy.da.FeatureClassToNumPyArray(
        in_table=in_fc,
        field_names=['SHAPE@X', 'SHAPE@Y'],
        explode_to_points=True
    )
    x, y = [arr[name] for name in ['SHAPE@X', 'SHAPE@Y']]
    a = np.empty((len(x), ), dtype=np.dtype([('X', np.float64), ('Y', np.float64)]))
    # round `X` and `Y` values
    a['X'] = np.round(x, 3)
    a['Y'] = np.round(y, 3)
    xy = stu(a)
    return a, xy

def delaunay(in_fc, out_fc):
    """Calculate the Delaunay triangulation of an input feature class' vertices."""
    spatial_ref = arcpy.Describe(in_fc).spatialReference
    _, np_arr = fc_to_numpy_array(in_fc)
    delaunay = Delaunay(np_arr).simplices

    # construct output polygons
    features = []
    for tri in delaunay:
        pts = [np_arr[idx] for idx in tri] # list of pt coords [[x1, y1], [x2, y2], ]
        features.append(arcpy.Polygon(arcpy.Array([arcpy.Point(*pt) for pt in pts]), spatial_reference=spatial_ref))

    # create output fc from polygons
    arcpy.management.CopyFeatures(features, out_fc)

    return

# TODO: consider manual voronoi polygon calculation
# https://gist.github.com/letmaik/8803860
# https://github.com/Dan-Patterson/numpy_geometry/blob/master/arcpro_npg/npg/tbx_tools.py
