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
        param0.controlCLSID = '{60061247-BCA8-473E-A7AF-A2026DDE1C2D}' # allows polygon creation

        param1 = arcpy.Parameter(
            displayName="Connecting Edge Points",
            name="points",
            datatype="GPFeatureLayer",
            parameterType="Optional",
            multiValue=True,
            direction="Input")
        param1.filter.list = ["Point"]
        param1.controlCLSID = '{60061247-BCA8-473E-A7AF-A2026DDE1C2D}' # allows polygon creation

        # TODO: fill holes option

        # TODO: one centerline per polygon option using convex hull on polygon
        # https://github.com/bcmertz/SWCD-Tools/issues/161

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

        # create scratch layers
        scratch_polygon = arcpy.CreateScratchName("polygon", data_type="FeatureClass", workspace=arcpy.env.scratchGDB)
        scratch_vertices = arcpy.CreateScratchName("vertices", data_type="FeatureClass", workspace=arcpy.env.scratchGDB)
        scratch_thiessen = arcpy.CreateScratchName("thiessen", data_type="FeatureClass", workspace=arcpy.env.scratchGDB)
        scratch_line = arcpy.CreateScratchName("line", data_type="FeatureClass", workspace=arcpy.env.scratchGDB)
        scratch_dissolve = arcpy.CreateScratchName("dissolve", data_type="FeatureClass", workspace=arcpy.env.scratchGDB)
        scratch_dangling = arcpy.CreateScratchName("dangling", data_type="FeatureClass", workspace=arcpy.env.scratchGDB)

        # export polygon to scratch
        log("export")
        arcpy.management.CopyFeatures(polygon, scratch_polygon)

        # densify
        log("densify")
        arcpy.edit.Densify(
            in_features=scratch_polygon,
            densification_method="DISTANCE",
            distance="50 Meters",
            max_deviation="0.1 Meters",
        )

        # polygon to vertices
        log("feature vertices to points")
        arcpy.management.FeatureVerticesToPoints(
            in_features=scratch_polygon,
            out_feature_class=scratch_vertices,
            point_location="ALL"
        )

        # thiessen
        log("thiessen")
        arcpy.analysis.CreateThiessenPolygons(
            in_features=scratch_vertices,
            out_feature_class=scratch_thiessen,
            fields_to_copy="ONLY_FID"
        )

        # polygon to line
        log("polygon to line")
        arcpy.management.PolygonToLine(
            in_features=scratch_thiessen,
            out_feature_class=scratch_line,
            neighbor_option="IDENTIFY_NEIGHBORS"
        )

        # select by location: completely within
        log("select by location")
        completely_within, _, _ = arcpy.management.SelectLayerByLocation(
            in_layer=scratch_line,
            overlap_type="COMPLETELY_WITHIN",
            select_features=polygon,
            search_distance=None,
            selection_type="NEW_SELECTION",
            invert_spatial_relationship="NOT_INVERT"
        )

        # dissolve (single, unsplit)
        log("dissolve")
        arcpy.management.Dissolve(
            in_features=completely_within,
            out_feature_class=scratch_dissolve,
            multi_part="SINGLE_PART",
            unsplit_lines="UNSPLIT_LINES",
        )

        # feat vert to pts (dangling)
        log("dangling points")
        arcpy.management.FeatureVerticesToPoints(
            in_features=scratch_dissolve,
            out_feature_class=scratch_dangling,
            point_location="DANGLE"
        )

        # Selct by location (itnersect pt and line)
        log("select dangling")
        dangling, _, _ = arcpy.management.SelectLayerByLocation(
            in_layer=scratch_dissolve,
            overlap_type="INTERSECT",
            select_features=scratch_dangling,
            search_distance=None,
            selection_type="NEW_SELECTION",
            invert_spatial_relationship="NOT_INVERT"
        )

        # Delete selected
        log("delete selected")
        arcpy.management.DeleteFeatures(dangling)

        # dissolve (single, unsplit)
        log("dissolve to single part")
        arcpy.management.Dissolve(
            in_features=dangling,
            out_feature_class=output_file,
            dissolve_field=None,
            multi_part="MULTI_PART",
            unsplit_lines="DISSOLVE_LINES",
        )

        ### IF CONNECTION POINTS ###

        # # TODO: Generate near table
        # arcpy.analysis.GenerateNearTable(
        #     in_features="PolygonCenterlinePolygonPolygons_PolygonCenterline4",
        #     near_features="'Polygon Centerline Connecting Edge Points (Points) 2'",
        #     out_table=r"G:\GIS\Reya\tmp\MyPraaoject\MyPraaoject.gdb\PolygonCenterl_GenerateNearT",
        #     search_radius=None,
        #     location="LOCATION",
        #     angle="NO_ANGLE",
        #     closest="CLOSEST",
        #     closest_count=0,
        #     method="PLANAR",
        #     distance_unit=""
        # )

        # # TODO: XY to line from table\
        # arcpy.management.XYToLine(
        #     in_table="PolygonCenterl_GenerateNearT",
        #     out_featureclass=r"G:\GIS\Reya\tmp\MyPraaoject\MyPraaoject.gdb\PolygonCenterl_Gene_XYToLine",
        #     startx_field="FROM_X",
        #     starty_field="FROM_Y",
        #     endx_field="NEAR_X",
        #     endy_field="NEAR_Y",
        #     line_type="GEODESIC",
        #     id_field="IN_FID",
        #     spatial_reference='PROJCS["WGS_1984_UTM_Zone_18N",GEOGCS["GCS_WGS_1984",DATUM["D_WGS_1984",SPHEROID["WGS_1984",6378137.0,298.257223563]],PRIMEM["Greenwich",0.0],UNIT["Degree",0.0174532925199433]],PROJECTION["Transverse_Mercator"],PARAMETER["False_Easting",500000.0],PARAMETER["False_Northing",0.0],PARAMETER["Central_Meridian",-75.0],PARAMETER["Scale_Factor",0.9996],PARAMETER["Latitude_Of_Origin",0.0],UNIT["Meter",1.0]];-5120900 -9998100 10000;-100000 10000;-100000 10000;0.001;0.001;0.001;IsHighPrecision',
        #     attributes="NO_ATTRIBUTES"
        # )

        # TODO: Merge line with centerline

        # TODO: feature vertices to points dangling

        # TODO: dissolve (multi-part, dissolve)

        # TODO: Select by location (touching dangling)

        # TODO: Select by location (completely within VBET)

        # TODO: Delete selected

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
