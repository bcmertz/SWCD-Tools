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
    """Find centerline of polygon."""

    # TODO: densify
    arcpy.edit.Densify(
        in_features="vbet_SimplifyPolygon1",
        densification_method="DISTANCE",
        distance="50 Meters",
        max_deviation="0.1 Meters",
        max_angle=10,
        max_vertex_per_segment=None
    )

    # TODO: thiessen

    # TODO: polygon to line

    # TODO: select by location: completely within

    # TODO: Export to new fc

    # TODO: Dissolve (single, unsplit)

    # TODO: feat vert to pts (dangling)

    # TODO: Selct by location (itnersect pt and line)

    # TODO: Delete selected

    # TODO: Generate near table

    # TODO: XY to line from table

    # TODO: Merge line with centerline

    # TODO: Select by location (completely within VBET)

    # TODO: Delete selected

    return centerline

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
