# --------------------------------------------------------------------------------
# Name:        Polygon Centerline
# Purpose:     This tool creates a polygon centerline optionally intersected to
#              edge points. This is a non-restrictively licensed alternative to
#              the Topographic Production Tools license "Polygon to Centerline" tool.
#
# License:     Contextual Copyleft AI (CCAI) License v1.0.
#              Full license in LICENSE file.
# --------------------------------------------------------------------------------

import os
import math
import arcpy

from ..helpers import license, reload_module, log, empty_workspace
from ..helpers import setup_environment as setup
from ..helpers import validate_spatial_reference as validate

def polygon_centerline(polygon, edge_points):
    """ TODO
    line - arcpy.PolyLine() object
    interval - <GPLinearUnit>
    """
    interval, interval_unit = interval.split(" ")
    transects = []

    # positionAlongLine fails to get start point dist=0 if using geodesic=True
    # so we use geodesic=False which uses Meters as linear unit instead of line unit
    interval = int(float(interval) * arcpy.LinearUnitConversionFactor(interval_unit, "Meters"))
    length = line.getLength("GEODESIC", units="Meters")
    for dist in range(0, int(length)+interval, interval):
        # get point at distance
        point = line.positionAlongLine(dist, geodesic=False)[0]

        #create transect at point
        transect = transect_line(line, point, width)
        transects.append(transect)

    return transects

class PolygonCenterline(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Polygon Centerline"
        self.description = "Generate polygon centerline"
        self.category = "Fluvial Geomorphology"
        self.canRunInBackground = False

    def getParameterInfo(self):
        """Define parameter definitions"""
        param0 = arcpy.Parameter(
            displayName="Polygon",
            name="polygon",
            datatype="GPFeatureLayer",
            parameterType="Required",
            direction="Input")
        param0.filter.list = ["Polygon"]

        param1 = arcpy.Parameter(
            displayName="Connecting Edge Points",
            name="points",
            datatype="GPFeatureLayer",
            parameterType="Optional",
            direction="Input")
        param1.filter.list = ["Point"]

        # TODO: fill holes option

        param2 = arcpy.Parameter(
            displayName="Output Features",
            name="out_features",
            datatype="DEFeatureClass",
            parameterType="Required",
            direction="Output")
        param2.parameterDependencies = [param0.name]
        param2.schema.clone = True

        params = [param0, param1, param2]
        return params

    def updateParameters(self, parameters):
        return

    def isLicensed(self):
        """Set whether the tool is licensed to execute."""
        return license()

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool parameter."""
        validate(parameters)
        return

    @reload_module(__name__)
    def execute(self, parameters, messages):
        """The source code of the tool."""
        # Setup
        log("setting up project")
        project, active_map = setup()

        # read in parameters
        polygon = parameters[0].value
        edge_points = parameters[1].value
        output_file = parameters[2].valueAsText

        # TODO: handle multiple polygons / points

        # find centerline
        centerline = polygon_centerline(polygon, edge_points)
        arcpy.conversion.ExportFeatures(centerline, output_file)

        # add data
        log("adding data")
        active_map.addDataFromPath(output_file)

        # cleanup
        log("deleting unneeded data")
        empty_workspace(arcpy.env.scratchGDB)

        # save project
        log("saving project")
        project.save()

        return
