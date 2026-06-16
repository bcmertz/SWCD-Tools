# --------------------------------------------------------------------------------
# Name:        Generate Cross-Sections
# Purpose:     This tool creates cross-sections along a provided stream line.
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

def generate_transects(line, interval, width):
    """ Generate transects of length WIDTH along a LINE at a given INTERVAL.
    line - arcpy.PolyLine() object
    interval - <GPLinearUnit>
    width - <GPLinearUnit>
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

def transect_line(line, point, transect_width):
    """Returns a transect to LINE at POINT of length TRANSECT_WIDTH.
    line - arcpy.PolyLine() object
    point - arcpy.Point() object
    transect_width - <GPLinearUnit>
    """

    # epsilon
    e = 1e-5

    # get stream vertex
    point = line.queryPointAndDistance(point, False)
    geom = point[0]
    distance = point[1]
    spatial_reference = line.spatialReference
    line_unit = spatial_reference.linearUnitName
    transect_length, transect_length_unit = transect_width.split(" ")
    transect_length = float(transect_length) * arcpy.LinearUnitConversionFactor(transect_length_unit, line_unit)

    # get points immediately before and after midpoint
    before = line.positionAlongLine(distance-e, False)
    after = line.positionAlongLine(distance+e, False)

    dX = after[0].X - before[0].X
    dY = after[0].Y - before[0].Y

    # angle of the midpoint segment
    angle = math.atan2(dX,dY) * 180 / math.pi

    first_tran_point = geom.pointFromAngleAndDistance(angle - 90, transect_length/2)
    last_tran_point = geom.pointFromAngleAndDistance(angle + 90, transect_length/2)

    transect = arcpy.Polyline(arcpy.Array((first_tran_point.firstPoint, last_tran_point.firstPoint)), spatial_reference)
    return transect

class GenerateCrossSections(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Generate Cross-Sections"
        self.description = "Generate Cross-Sections"
        self.category = "Fluvial Geomorphology"

    def getParameterInfo(self):
        """Define parameter definitions"""
        param0 = arcpy.Parameter(
            displayName="Stream Feature Class",
            name="line",
            datatype="GPFeatureLayer",
            parameterType="Required",
            direction="Input")
        param0.filter.list = ["Polyline"]

        param1 = arcpy.Parameter(
            displayName="Analysis Area",
            name="analysis_area",
            datatype="GPExtent",
            parameterType="Optional",
            direction="Input")
        param1.controlCLSID = '{15F0D1C1-F783-49BC-8D16-619B8E92F668}'

        param2 = arcpy.Parameter(
            displayName="Output Features",
            name="out_features",
            datatype="DEFeatureClass",
            parameterType="Required",
            direction="Output")
        param2.parameterDependencies = [param0.name]
        param2.schema.clone = True

        param3 = arcpy.Parameter(
            displayName="Cross-Section Width",
            name="width",
            datatype="GPLinearUnit",
            parameterType="Required",
            direction="Input")

        param4 = arcpy.Parameter(
            displayName="Cross-Section Interval",
            name="interval",
            datatype="GPLinearUnit",
            parameterType="Required",
            direction="Input")

        param5 = arcpy.Parameter(
            displayName="Remove output line intersections?",
            name="remove",
            datatype="GPBoolean",
            parameterType="Optional",
            direction="Input")
        param5.value = True

        params = [param0, param1, param2, param3, param4, param5]
        return params

    def updateParameters(self, parameters):
        # default transect width
        if parameters[3].value is None:
            parameters[3].value = "100 FeetUS"

        # default transect spacing
        if parameters[4].value is None:
            parameters[4].value = "100 FeetUS"

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
        streams = parameters[0].value
        extent = parameters[1].value
        output_file = parameters[2].valueAsText
        out_name = output_file.split("\\")[-1]
        out_dir = os.path.dirname(output_file)
        width = parameters[3].valueAsText
        interval = parameters[4].valueAsText
        remove = parameters[5].value

        # create scratch layers
        log("creating scratch layers")
        scratch_streams = arcpy.CreateScratchName("streams", data_type="FeatureClass", workspace=arcpy.env.scratchGDB)
        scratch_intersection = arcpy.CreateScratchName("intersect", data_type="FeatureClass", workspace=arcpy.env.scratchGDB)
        scratch_transects = arcpy.CreateScratchName("transects", data_type="FeatureClass", workspace=arcpy.env.scratchGDB)

        # set analysis extent
        if extent:
            log("setting analysis extent")
            arcpy.env.extent = extent
            arcpy.analysis.Clip(streams, extent.polygon, scratch_streams)
        else:
            scratch_streams = streams

        # output spatial reference
        log("finding output spatial reference")
        stream_desc = arcpy.Describe(scratch_streams)
        spatial_reference = stream_desc.spatialReference.name

        # create output feature class
        log("creating output feature class")
        transects_fc = arcpy.management.CreateFeatureclass(out_dir, out_name, "POLYLINE", spatial_reference=spatial_reference, has_m="ENABLED", has_z="ENABLED")

        # generating transects
        log("generating transects")
        n = len([row[0] for row in arcpy.da.SearchCursor(scratch_streams, ["SHAPE@"])])
        log("iterating through {} stream lines".format(n))
        with arcpy.da.SearchCursor(scratch_streams, ["SHAPE@"]) as stream_cursor:
            with arcpy.da.InsertCursor(transects_fc, ["SHAPE@"]) as transect_cursor:
                for stream_line in stream_cursor:
                    transects = generate_transects(stream_line[0], interval, width)
                    for transect in transects:
                        transect_cursor.insertRow([transect])


        # optionally remove intersections
        if remove:
            log("removing intersections in output cross-sections")

            # create intersection points
            arcpy.analysis.Intersect(
                in_features=transects_fc,
                out_feature_class=scratch_intersection,
                join_attributes="ALL",
                cluster_tolerance=None,
                output_type="POINT"
            )

            # split cross-sections at points
            arcpy.management.SplitLineAtPoint(
                in_features=transects_fc,
                point_features=scratch_intersection,
                out_feature_class=scratch_transects,
                search_radius="0.001 Feet"
            )

            # copy scratch_transects to transects_fc
            log("adding transect data")
            arcpy.management.CopyFeatures(scratch_transects, transects_fc)
            transects_lyr = active_map.addDataFromPath(transects_fc)

            # select lines with intersections
            arcpy.management.SelectLayerByLocation(
                in_layer=transects_lyr,
                overlap_type="INTERSECT",
                select_features=scratch_intersection,
                search_distance=None,
                selection_type="NEW_SELECTION",
                invert_spatial_relationship="NOT_INVERT"
            )

            # select only the parts of those lines that don't pass through the stream line
            arcpy.management.SelectLayerByLocation(
                in_layer=transects_lyr,
                overlap_type="INTERSECT",
                select_features=streams,
                search_distance=None,
                selection_type="REMOVE_FROM_SELECTION",
                invert_spatial_relationship="NOT_INVERT"
            )

            # make sure something is selected
            sel_set = transects_lyr.getSelectionSet()
            if sel_set is not None:
                # deleted selected pieces / trim intersections
                arcpy.management.DeleteFeatures(transects_lyr)
        else:
            # add transect data
            log("adding transect data")
            active_map.addDataFromPath(transects_fc)

        # cleanup
        log("deleting unneeded data")
        empty_workspace(arcpy.env.scratchGDB)

        # save project
        log("saving project")
        project.save()

        return
