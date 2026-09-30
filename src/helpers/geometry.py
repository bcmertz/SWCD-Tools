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


def bbox(arr):
    """Find bounding box of polygon represented by numpy.ndarr `arr`"""
    # rotate to get separate arrays of x and y coordinates
    arr_rot = np.rot90(arr, axes=(0,1))

    # flatten x and y coordinate arrays
    x_arr  = arr_rot[1].flatten()
    y_arr = arr_rot[0].flatten()

    # find bounding box min + max
    x_min = np.min(x_arr)
    x_max = np.max(x_arr)
    y_min = np.min(y_arr)
    y_max = np.max(y_arr)

    return [[x_min, y_min],[x_max, y_min],[x_max, y_max],[x_min, y_max]]


def delaunay_fc(in_fc, out_fc):
    """Calculate the Delaunay triangulation feature class from an input feature class' vertices."""
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


def voronoi(delaunay):
    """Calculate voronoi polygons from numpy array."""
    # calculate Delaunay triangulation
    triangles = delaunay.points[delaunay.simplices]

    # find circumcenters of Delaunay triangulation
    circum_centers = [triangle_csc(tri) for tri in triangles]

    # construct line segments between circumcenters
    segments = []
    for i, triangle in enumerate(triangles):
        circum_center = circum_centers[i]
        if circum_center is None:
            continue
        for j, neighbor in enumerate(delaunay.neighbors[i]):
            if neighbor != -1:
                if circum_centers[neighbor] is None:
                    continue
                segments.append((circum_center, circum_centers[neighbor]))
            else:
                ps = triangle[(j+1)%3] - triangle[(j-1)%3]
                ps = np.array((ps[1], -ps[0]))

                middle = (triangle[(j+1)%3] + triangle[(j-1)%3]) * 0.5
                di = middle - triangle[j]

                ps /= np.linalg.norm(ps)
                di /= np.linalg.norm(di)

                dot = np.dot(di, ps)

                if dot < 0.0:
                    ps *= -1000.0
                else:
                    ps *= 1000.0
                segments.append((circum_center, circum_center + ps))
    return segments


# voronoi polygon calculation
#
# modified from https://gist.github.com/letmaik/8803860 and
# https://stackoverflow.com/questions/10650645/python-calculate-voronoi-tesselation-from-scipys-delaunay-triangulation-in-3d/15783581#15783581
def voronoi_fc(delaunay_fc, out_fc):
    """Find voronoi polygon feature class from input."""
    spatial_ref = arcpy.Describe(delaunay_fc).spatialReference
    _, np_arr = fc_to_numpy_array(delaunay_fc)

    # calculate voronoi polygons numpy array
    vor = voronoi(np_arr)

    # construct arcpy features
    features = []
    for feature in vor:
        array = arcpy.Array([arcpy.Point(*coords) for coords in feature])
        polyline = arcpy.Polyline(array, spatial_ref)
        features.append(polyline)

    # create output fc from polygons
    arcpy.management.CopyFeatures(features, out_fc)
    return


# triangle circumcenter
#
# modified from https://stackoverflow.com/questions/10650645/python-calculate-voronoi-tesselation-from-scipys-delaunay-triangulation-in-3d/15783581#15783581
def triangle_csc(pts):
    """Find circumcenter coordinates of triangle."""
    rows, _ = pts.shape

    A = np.bmat([[2 * np.dot(pts, pts.T), np.ones((rows, 1))],
                 [np.ones((1, rows)), np.zeros((1, 1))]])

    b = np.hstack((np.sum(pts * pts, axis=1), np.ones((1))))
    try:
        x = np.linalg.solve(A,b)
    except Exception:
        return None
    bary_coords = x[:-1]
    sum =  np.sum(pts * np.tile(bary_coords.reshape((pts.shape[0], 1)), (1, pts.shape[1])), axis=0)

    return sum
