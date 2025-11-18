# -*- coding: utf-8 -*-

import arcpy
import pathlib
import openpyxl
import datetime
import math

from pprint import pprint

# setup helpers
import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), "../helpers"))
from print_messages import print_messages as log
from setup_environment import setup_environment as setup

class WatershedDelineation(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Watershed Delineation"
        self.description = "Calculate watershed for a given point"
        self.category = "Hydrology"        
        self.canRunInBackground = False

    def getParameterInfo(self):
        """Define parameter definitions"""
        param0 = arcpy.Parameter(
            displayName="DEM",
            name="dem",
            datatype="GPRasterLayer",
            parameterType="Required",
            direction="Input")

        param1 = arcpy.Parameter(
            displayName="Analysis Area",
            name="analysis_area",
            datatype="GPExtent",
            parameterType="Optional",
            direction="Input")        
        param1.controlCLSID = '{15F0D1C1-F783-49BC-8D16-619B8E92F668}'

        param2 = arcpy.Parameter(
            displayName="Pour Point",
            name="boundary",
            datatype="GPFeatureLayer",
            parameterType="Required",
            direction="Input")
        param2.filter.list = ["Point"]
        param2.controlCLSID = '{60061247-BCA8-473E-A7AF-A2026DDE1C2D}' # allows point creation

        param3 = arcpy.Parameter(
            displayName="Snap Pour Point Max Adjustment Distance",
            name="snap_adjustment",
            datatype="GPDouble",
            parameterType="Required",
            direction="Input")
        
        param4 = arcpy.Parameter(
            displayName="Derive stream lines?",
            name="calculations",
            datatype="GPBoolean",
            parameterType="Optional",
            direction="Input")
        
        param5 = arcpy.Parameter(
            displayName="Stream Threshold Value",
            name="threshold",
            datatype="GPDouble",
            enabled=False,
            parameterType="Optional",
            direction="Input")

        param6 = arcpy.Parameter(
            displayName="Output Features",
            name="out_features",
            datatype="DEFeatureClass",
            parameterType="Required",
            direction="Output")
        param6.parameterDependencies = [param0.name]
        param6.schema.clone = True
        
        params = [param0, param1, param2, param3, param4, param5, param6]
        return params

    def updateParameters(self, parameters):
        # Enable/Disable folder parameter based on if user will perform calculations
        if parameters[4].value == True:
            parameters[5].enabled = True
        if parameters[4].value == False:
            parameters[5].enabled = False

        # Default stream threshold value
        if parameters[5].value == None:
            parameters[5].value = 25000

        # Default snap pour point adjustment value
        if parameters[3].value == None:
            parameters[3].value = 10
        return
    
    def updateMessages(self, parameters):
        if parameters[4].value == True:
            parameters[5].setIDMessage("ERROR", 530)
        if parameters[4].value == False:
            parameters[5].clearMessage()
        if parameters[4].value:
            parameters[5].clearMessage()
        return

    def execute(self, parameters, messages):
        """The source code of the tool."""
        # Setup
        log("setting up project")
        project, active_map = setup()

        # read in parameters
        raster_layer = parameters[0].value
        XMin = parameters[1].value.XMin if parameters[1].value else 0
        YMin = parameters[1].value.YMin if parameters[1].value else 0
        XMax = parameters[1].value.XMax if parameters[1].value else 0
        YMax = parameters[1].value.YMax if parameters[1].value else 0
        extent = arcpy.Extent(XMin, YMin, XMax, YMax)
        if parameters[1].value:
                extent.spatialReference = parameters[1].value.spatialReference
        pour_points = parameters[2].value
        snap_adjustment = parameters[3].value
        stream_lines_bool = parameters[4].value
        accumulation_threshold = parameters[5].value
        output_file = parameters[6].valueAsText

        # create scratch layers
        log("creating scratch layers")
        scratch_dem = "{}\\dem_raster_clip".format(arcpy.env.workspace)
        clip_flow_accumulation_scratch = arcpy.CreateScratchName("clip_flow_accumulation_scratch", data_type="RasterDataset", workspace=arcpy.env.scratchFolder)
        pour_points_adjusted_scratch = "{}\\pour_points_adjusted_scratch".format(arcpy.env.workspace)

        if parameters[1].value:
            # clip DEM raster to the study area
            log("clipping raster to analysis area")
            rectangle = "{} {} {} {}".format(extent.XMin, extent.YMin, extent.XMax, extent.YMax)
            arcpy.management.Clip(raster_layer, rectangle, scratch_dem)
            raster_layer = scratch_dem

        # fill raster
        log("filling raster")
        fill_raster_scratch = arcpy.sa.Fill(raster_layer)

        # flow direction
        log("calculating flow direction")
        flow_direction_scratch = arcpy.sa.FlowDirection(fill_raster_scratch)

        # flow accumulation
        log("calculating flow accumulation")
        flow_accumulation_scratch = arcpy.sa.FlowAccumulation(flow_direction_scratch)

        # adjust pour points
        log("adjusting pour point data")
        pour_points_oid = arcpy.Describe(pour_points).OIDFieldName
        pour_points_adjusted = arcpy.sa.SnapPourPoint(pour_points, flow_accumulation_scratch, snap_adjustment, pour_points_oid)
        pour_points_adjusted.save(pour_points_adjusted_scratch)

        # watershed
        log("delineating watershed")
        watershed = arcpy.sa.Watershed(flow_direction_scratch, pour_points_adjusted_scratch)
        
        # watershed raster to polyon
        log("converting watershed to polygon")       
        watershed_polygon_path = arcpy.CreateUniqueName(output_file)
        watershed_polygon = arcpy.conversion.RasterToPolygon(watershed, watershed_polygon_path, create_multipart_features=True)
        watershed_polygon = active_map.addDataFromPath(watershed_polygon)
        sym = watershed_polygon.symbology
        sym.updateRenderer('UniqueValueRenderer')
        sym.renderer.fields = ['gridcode']
        watershed_polygon.symbology = sym

        if stream_lines_bool:
            # clip flow accumulation
            log("clipping flow accumulation raster to watershed shape")
            arcpy.management.Clip(flow_accumulation_scratch, "", clip_flow_accumulation_scratch, watershed_polygon, "#", "ClippingGeometry")

            # con
            log("converting raster to stream network")
            sql_query = "VALUE > {}".format(accumulation_threshold)
            con_accumulation_scratch = arcpy.sa.Con(clip_flow_accumulation_scratch, 1, "", sql_query)     
            
            # stream link
            log("calculating stream links")
            stream_link = arcpy.sa.StreamLink(con_accumulation_scratch, flow_direction_scratch)
            
            # stream to feature
            log("creating stream feature")
            stream_feature_path = "{}\\stream_to_feature".format(arcpy.env.workspace)
            stream_feature = arcpy.sa.StreamToFeature(con_accumulation_scratch, flow_direction_scratch, stream_feature_path, True)
            stream_feature = active_map.addDataFromPath(stream_feature)
            sym = stream_feature.symbology
            sym.renderer.symbol.color = {'RGB' : [0, 0, 0, 0]}
            sym.renderer.symbol.outlineColor = {'RGB' : [0, 112, 255, 100]}
            sym.renderer.symbol.size = 1.5
            stream_feature.symbology = sym

        # remove temporary variables
        log("cleaning up")
        arcpy.management.Delete([scratch_dem, clip_flow_accumulation_scratch, pour_points_adjusted_scratch])

        # save and exit program successfully
        log("saving project")
        project.save()

        return
