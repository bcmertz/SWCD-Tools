# -*- coding: utf-8 -*-

import arcpy
import pathlib
import openpyxl
import datetime
import math

from pprint import pprint

# import log tool
import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), "../helpers"))
from printmessages import printMessages as log

# TODO: Separate streamline tool -- create order to use tools for workflow / separate tools
# TODO: create stream profile (elevation) chart tool thing or data extractor

class StreamElevation(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Stream Elevation Profile"
        self.description = "Create profile of the stream throughout it's length"
        self.category = "Hydrology"
        self.canRunInBackground = False

    def getParameterInfo(self):
        """Define parameter definitions"""
        param0 = arcpy.Parameter(
            displayName="Stream Feature",
            name="stream",
            datatype="GPFeatureLayer",
            parameterType="Required",
            direction="Input")
        param0.filter.list = ["Line"]
        param0.controlCLSID = '{60061247-BCA8-473E-A7AF-A2026DDE1C2D}' # allows line creation

        param1 = arcpy.Parameter(
            displayName="DEM",
            name="dem",
            datatype="GPRasterLayer",
            parameterType="Required",
            direction="Input")

        param2 = arcpy.Parameter(
            displayName="Watershed",
            name="analysis_area",
            datatype="GPFeatureLayer",
            parameterType="Optional",
            direction="Input")
        param2.controlCLSID = '{60061247-BCA8-473E-A7AF-A2026DDE1C2D}' # allows polygon creation

        param3 = arcpy.Parameter(
            displayName="Output Features",
            name="out_features",
            datatype="DEFeatureClass",
            parameterType="Required",
            direction="Output")
        param3.parameterDependencies = [param0.name]
        param3.schema.clone = True
        
        params = [param0, param1, param2, param3]
        return params

    def updateParameters(self, parameters):
        return
    
    def updateMessages(self, parameters):
        return
    
    def execute(self, parameters, messages):
        """The source code of the tool."""
        # Setup
        arcpy.env.overwriteOutput = True

        project = arcpy.mp.ArcGISProject("Current")
        active_map = project.activeMap

        # read in parameters
        streamlines = parameters[0].value
        raster_layer = parameters[1].value
        log(parameters[2].value)
        watershed = parameters[2].value
        if parameters[2].value:
                extent.spatialReference = parameters[2].value.spatialReference
        output_file = parameters[3].valueAsText
      
        # create scratch layers
        log("creating scratch layers")
        scratch_dem = "{}\\dem_raster_clip".format(arcpy.env.workspace)
        streamlines_scratch = arcpy.CreateScratchName("scratch_streamlines",
                                               data_type="FeatureClass",
                                               workspace=arcpy.env.scratchFolder)
        
        if parameters[2].value:
            # clip streamlines to the study area
            log("clipping waterbody to analysis area")
            arcpy.analysis.Clip(streamlines, watershed, streamlines_scratch)

        # TODO: generate points along line

        # TODO: extract values to points

        # save and exit program successfully
        log("saving project")
        project.save()
        
        # remove temporary variables
        log("cleaning up")
        # TODO: FIX - ﻿arcgisscripting.ExecuteError: ERROR 000601: Cannot delete G:\GIS\Streamwork\OCCA Unadilla Culvert Sizing\scratch\temp0.  May be locked by another application.
        arcpy.management.Delete([fill_raster_scratch, flow_direction_scratch, flow_accumulation_scratch, con_accumulation_scratch])
        arcpy.management.Delete([scratch_dem, clip_flow_accumulation_scratch, pour_points_adjusted_scratch])
        return

class TopographicWetness(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Topographic Wetness Index (TWI)"
        self.description = "Calculate Topographic Wetness of a given area"
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
            displayName="Output Features",
            name="out_features",
            datatype="DEFeatureClass",
            parameterType="Required",
            direction="Output")
        param2.parameterDependencies = [param0.name]
        param2.schema.clone = True
        
        params = [param0, param1, param2]
        return params

    def execute(self, parameters, messages):
        """The source code of the tool."""
        # Setup
        arcpy.env.overwriteOutput = True

        project = arcpy.mp.ArcGISProject("Current")
        active_map = project.activeMap

        # read in parameters
        raster_layer = parameters[0].value
        XMin = parameters[1].value.XMin if parameters[1].value else 0
        YMin = parameters[1].value.YMin if parameters[1].value else 0
        XMax = parameters[1].value.XMax if parameters[1].value else 0
        YMax = parameters[1].value.YMax if parameters[1].value else 0
        extent = arcpy.Extent(XMin, YMin, XMax, YMax)
        if parameters[1].value:
                extent.spatialReference = parameters[1].value.spatialReference
        output_file = parameters[2].valueAsText

        # create scratch layers
        # TODO: remove unused
        log("creating scratch layers")
        scratch_dem = "{}\\dem_raster_clip".format(arcpy.env.workspace)
        fill_raster_scratch = arcpy.CreateScratchName("tmp", data_type="RasterDataset", workspace=arcpy.env.scratchFolder)
        flow_direction_scratch = "{}\\flowdir1.crf\\".format(arcpy.env.scratchFolder)
        flow_accumulation_scratch = arcpy.CreateScratchName("tmp", data_type="RasterDataset", workspace=arcpy.env.scratchFolder)
        slope_scratch = arcpy.CreateScratchName("tmp", data_type="RasterDataset", workspace=arcpy.env.scratchFolder)
        slope_tangent = arcpy.CreateScratchName("tmp", data_type="RasterDataset", workspace=arcpy.env.scratchFolder)

        if parameters[1].value:
            # clip DEM raster to the study area
            log("clipping raster to analysis area")
            rectangle = "{} {} {} {}".format(extent.XMin, extent.YMin, extent.XMax, extent.YMax)
            arcpy.management.Clip(raster_layer, rectangle, scratch_dem)
            raster_layer = scratch_dem

        # fill raster
        log("filling raster")
        fill_raster_scratch = arcpy.sa.Fill(raster_layer)
            
        # flow accumulation
        log("calculating flow accumulation")
        out_accumulation_raster = arcpy.sa.DeriveContinuousFlow(fill_raster_scratch, flow_direction_type="MFD")
        out_accumulation_raster.save(flow_accumulation_scratch)

        # int flow accumulation
        int_flow_accumulation = arcpy.sa.Float(flow_accumulation_scratch)

        # calculate slope
        log("calculating slope")
        slope_raster = arcpy.sa.Slope(raster_layer, "DEGREE", "", "GEODESIC", "METER")
        #slope_raster.save(slope_scratch)

        # convert slope to radians
        log("converting slope raster to radians")
        slope_radians = arcpy.sa.Float(slope_raster) * (math.pi / 180)

        # calculate slope tangent
        log("calculating slope tangent")
        out_slope_tan = arcpy.sa.Tan(slope_radians)
        
        # adjust flow accumulation
        log("adjusting flow accumulation")
        adjusted_flow_accumulation = int_flow_accumulation + 1

        # calculate topographic wetness index (TWI)
        log("calculating slope tangent")
        out_TWI = arcpy.sa.Ln(adjusted_flow_accumulation / out_slope_tan)
        out_TWI.save(output_file)
      
        # add TWI to map
        twi_layer = active_map.addDataFromPath(output_file)

        # save and exit program successfully
        log("saving project")
        project.save()
        
        # TODO: remove temporary variables
        #log("cleaning up")
        #arcpy.management.Delete([fill_raster_scratch, flow_direction_scratch, flow_accumulation_scratch, con_accumulation_scratch])
        #arcpy.management.Delete([scratch_dem, clip_flow_accumulation_scratch, pour_points_adjusted_scratch])
        return

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
        arcpy.env.overwriteOutput = True

        project = arcpy.mp.ArcGISProject("Current")
        active_map = project.activeMap

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
        clip_flow_accumulation_scratch = "{}\\flow_accumulation_clip".format(arcpy.env.workspace)
        pour_points_adjusted_scratch = "{}\\pour_points_adjusted_scratch".format(arcpy.env.workspace)
        fill_raster_scratch = arcpy.CreateScratchName("temp", data_type="RasterDataset", workspace=arcpy.env.scratchFolder)
        flow_direction_scratch = arcpy.CreateScratchName("temp", data_type="RasterDataset", workspace=arcpy.env.scratchFolder)
        flow_accumulation_scratch = arcpy.CreateScratchName("temp", data_type="RasterDataset", workspace=arcpy.env.scratchFolder)
        clip_flow_accumulation_scratch = arcpy.CreateScratchName("temp", data_type="RasterDataset", workspace=arcpy.env.scratchFolder)
        con_accumulation_scratch = arcpy.CreateScratchName("temp", data_type="RasterDataset", workspace=arcpy.env.scratchFolder)
        pour_points_adjusted_scratch = arcpy.CreateScratchName("temp", data_type="RasterDataset", workspace=arcpy.env.scratchFolder)

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

        # save and exit program successfully
        log("saving project")
        project.save()
        
        # remove temporary variables
        log("cleaning up")
        # TODO: FIX - ﻿arcgisscripting.ExecuteError: ERROR 000601: Cannot delete G:\GIS\Streamwork\OCCA Unadilla Culvert Sizing\scratch\temp0.  May be locked by another application.
        arcpy.management.Delete([fill_raster_scratch, flow_direction_scratch, flow_accumulation_scratch, con_accumulation_scratch])
        arcpy.management.Delete([scratch_dem, clip_flow_accumulation_scratch, pour_points_adjusted_scratch])
        return

class CalculateStreamline(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Calculate Streamline"
        self.description = "Calculate streamlines for a given watershed"
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
            displayName="Basin Shapefile",
            name="boundary",
            datatype="GPFeatureLayer",
            parameterType="Required",
            direction="Input")
        param1.filter.list = ["Polygon"]

        param2 = arcpy.Parameter(
            displayName="Stream Threshold Value",
            name="threshold",
            datatype="GPDouble",
            direction="Input")

        param3 = arcpy.Parameter(
            displayName="Output Features",
            name="out_features",
            datatype="DEFeatureClass",
            parameterType="Required",
            direction="Output")
        param3.parameterDependencies = [param0.name]
        param3.schema.clone = True
        
        params = [param0, param1, param2, param3]
        return params

    def updateParameters(self, parameters):
        # Default stream threshold value
        if parameters[2].value == None:
            parameters[2].value = 25000

    def execute(self, parameters, messages):
        """The source code of the tool."""
        # Setup
        arcpy.env.overwriteOutput = True

        project = arcpy.mp.ArcGISProject("Current")
        active_map = project.activeMap

        # read in parameters
        raster_layer = parameters[0].value
        watershed_polygon = parameters[1].value
        accumulation_threshold = parameters[2].value
        output_file = parameters[3].value

        # create scratch layers
        log("creating scratch layers")
        scratch_dem = "{}\\dem_raster_clip".format(arcpy.env.workspace)
        fill_raster_scratch = arcpy.CreateScratchName("temp", data_type="RasterDataset", workspace=arcpy.env.scratchFolder)
        flow_direction_scratch = arcpy.CreateScratchName("temp", data_type="RasterDataset", workspace=arcpy.env.scratchFolder)
        flow_accumulation_scratch = arcpy.CreateScratchName("temp", data_type="RasterDataset", workspace=arcpy.env.scratchFolder)
        #clip_flow_accumulation_scratch = "{}\\flow_accumulation_clip".format(arcpy.env.workspace)
        clip_flow_accumulation_scratch = arcpy.CreateScratchName("temp", data_type="RasterDataset", workspace=arcpy.env.scratchFolder)
        con_accumulation_scratch = arcpy.CreateScratchName("temp", data_type="RasterDataset", workspace=arcpy.env.scratchFolder)
        
        if parameters[1].value:
            # clip DEM raster to the study area
            log("clipping raster to analysis area")
            arcpy.management.Clip(raster_layer, watershed_polygon, scratch_dem)
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

        # save and exit program successfully
        log("saving project")
        project.save()
        
        # remove temporary variables
        log("cleaning up")
        arcpy.management.Delete([scratch_dem, fill_raster_scratch, flow_direction_scratch, flow_accumulation_scratch, clip_flow_accumulation_scratch, con_accumulation_scratch])

        return

class SubBasinDelineation(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Sub-Basin Delineation"
        self.description = "Calculate hydrology for all sub-basins and perform stream routing"
        self.category = "Hydrology"
        self.canRunInBackground = False

    def updateParameters(self, parameters):
        # Enable/Disable folder parameter based on if user will perform calculations
        if parameters[3].value == True:
            parameters[4].enabled = True
        if parameters[3].value == False:
            parameters[4].enabled = False

        # Default stream threshold value
        if parameters[2].value == None:
            parameters[2].value = 25000
        return
        
    def updateMessages(self, parameters):
        if parameters[3].value == True:
            parameters[4].setIDMessage("ERROR", 530)
        if parameters[3].value == False:
            parameters[4].clearMessage()
        if parameters[4].value:
            parameters[4].clearMessage()
        return

    def getParameterInfo(self):
        """Define parameter definitions"""
        param0 = arcpy.Parameter(
            displayName="DEM",
            name="dem",
            datatype="GPRasterLayer",
            parameterType="Required",
            direction="Input")
       
        param1 = arcpy.Parameter(
            displayName="Basin Shapefile",
            name="boundary",
            datatype="GPFeatureLayer",
            parameterType="Required",
            direction="Input")
        param1.filter.list = ["Polygon"]     

        param2 = arcpy.Parameter(
            displayName="Stream Threshold Value",
            name="threshold",
            datatype="GPDouble",
            parameterType="Optional",
            direction="Input")
        
        param3 = arcpy.Parameter(
            displayName="Perform hydrology calculations on each sub-basin?",
            name="calculations",
            datatype="GPBoolean",
            parameterType="Optional",
            direction="Input")

        param4 = arcpy.Parameter(
            displayName="Hydrology Calculations output folder",
            name="folder",
            datatype="DEFolder",
            enabled=False,
            parameterType="Optional",
            direction="Input")

        params = [param0, param1, param2, param3, param4]
        return params

    def execute(self, parameters, messages):
        """The source code of the tool."""
        # Setup
        arcpy.env.overwriteOutput = True

        project = arcpy.mp.ArcGISProject("Current")
        active_map = project.activeMap

        # read in parameters
        raster_layer = parameters[0].value
        watershed = parameters[1].value
        con_threshold = parameters[2].value if parameters[2].value else 25000
        hydrology_calculations = parameters[3].value
        calculations_folder = parameters[4].value

        # create scratch layers
        clip_raster_scratch = arcpy.CreateScratchName("temp", data_type="RasterDataset", workspace=arcpy.env.scratchFolder)
        fill_raster_scratch = arcpy.CreateScratchName("temp", data_type="RasterDataset", workspace=arcpy.env.scratchFolder)
        flow_direction_scratch = arcpy.CreateScratchName("temp", data_type="RasterDataset", workspace=arcpy.env.scratchFolder)
        flow_accumulation_scratch = arcpy.CreateScratchName("temp", data_type="RasterDataset", workspace=arcpy.env.scratchFolder)
        con_accumulation_scratch = arcpy.CreateScratchName("temp", data_type="RasterDataset", workspace=arcpy.env.scratchFolder)

        # clip DEM raster to the watershed
        log("clipping raster to watershed")
        arcpy.management.Clip(raster_layer, "", clip_raster_scratch, watershed, "#", "ClippingGeometry")
        
        # fill raster
        log("filling raster")
        fill_raster_scratch = arcpy.sa.Fill(clip_raster_scratch)
        
        # flow direction
        log("calculating flow direction")
        flow_direction_scratch = arcpy.sa.FlowDirection(fill_raster_scratch)
        
        # flow accumulation
        log("calculating flow accumulation")
        flow_accumulation_scratch = arcpy.sa.FlowAccumulation(flow_direction_scratch)
        
        # con
        log("converting raster to stream network")
        sql_query = "VALUE > {}".format(con_threshold)
        con_accumulation_scratch = arcpy.sa.Con(flow_accumulation_scratch, 1, "", sql_query)     
        
        # stream link
        log("calculating stream links")
        stream_link = arcpy.sa.StreamLink(con_accumulation_scratch, flow_direction_scratch)
        
        # watershed
        log("calculating watershed")
        watershed = arcpy.sa.Watershed(flow_direction_scratch, stream_link)
        
        # stream to feature
        log("craeting stream feature")
        stream_feature_path = "{}\\stream_to_feature".format(arcpy.env.workspace)
        stream_feature = arcpy.sa.StreamToFeature(con_accumulation_scratch, flow_direction_scratch, stream_feature_path, True)
        stream_feature = active_map.addDataFromPath(stream_feature)
        sym = stream_feature.symbology
        sym.renderer.symbol.color = {'RGB' : [0, 0, 0, 0]}
        sym.renderer.symbol.outlineColor = {'RGB' : [0, 112, 255, 100]}
        sym.renderer.symbol.size = 1.5
        stream_feature.symbology = sym
        
        # watershed raster to polyon
        log("converting watershed to polygon")
        watershed_polygon_path = "{}\\watershed_polygon".format(arcpy.env.workspace)
        watershed_polygon = arcpy.conversion.RasterToPolygon(watershed, watershed_polygon_path, create_multipart_features=True)
        watershed_polygon = active_map.addDataFromPath(watershed_polygon)
        sym = watershed_polygon.symbology
        sym.updateRenderer('UniqueValueRenderer')
        sym.renderer.fields = ['gridcode']
        watershed_polygon.symbology = sym
        watershed_polygon.visible = False
        
        # hydrology of each subbasin
        if hydrology_calculations == True:
            log("calculating watershed hydrology of each subbasin")
            arcpy.ImportToolbox("Watershed Hydrology.pyt", "Hydrology")
            basin_id = 0
            for row in arcpy.da.SearchCursor(watershed_polygon, "*"):
                sub_basin_path = "{}\\subbasin_{}".format(arcpy.env.workspace, basin_id)
                sql="""{0} = {1}""".format(arcpy.AddFieldDelimiters(watershed_polygon, arcpy.Describe(watershed_polygon).OIDFieldName),row[0])
                arcpy.analysis.Select(watershed_polygon, sub_basin_path, where_clause=sql)
                sub_basin = active_map.addDataFromPath(sub_basin_path)
                sub_basin.visible = False
                try:
                    arcpy.Hydrology.Calculate(sub_basin, clip_raster_scratch, calculations_folder)
                except arcpy.ExecuteError:
                    log(sub_basin.name, " failed calculation")
                    log(arcpy.GetMessages())
                    pprint(arcpy.GetAllMessages(), width=100)
                basin_id += 1
                sub_basin.visible = True

        watershed_polygon.visible = True
        # remove temporary variables
        log("cleaning up")
        arcpy.management.Delete([clip_raster_scratch, fill_raster_scratch, flow_direction_scratch, flow_accumulation_scratch, con_accumulation_scratch])
        
        return


class CalculateHydrology:
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "EFH-2 Calculation"
        self.category = "Hydrology"
        self.description = "Calculate the hydrology of the given watershed"

    def getParameterInfo(self):
        """Define parameter definitions"""
        param0 = arcpy.Parameter(
            displayName="Watershed Boundary Layer",
            name="watershed",
            datatype="GPFeatureLayer",
            parameterType="Required",
            multiValue=True,
            direction="Input")

        param1 = arcpy.Parameter(
            displayName="DEM",
            name="dem",
            datatype="GPRasterLayer",
            parameterType="Required",
            direction="Input")

        param2 = arcpy.Parameter(
            displayName="Output Folder",
            name="output_location",
            datatype="DEFolder",
            parameterType="Required",
            direction="Input")

        param3 = arcpy.Parameter(
            displayName="Stream Feature Class",
            name="streams",
            datatype="GPFeatureLayer",
            parameterType="Required",
            direction="Input")
        param3.filter.list = ["Polyline"]

        param4 = arcpy.Parameter(
            displayName="Land Use Data",
            name="land_use",
            datatype="GPRasterLayer",
            parameterType="Required",
            direction="Input")

        params = [param0, param1, param2, param3, param4]
        return params

    def addLayerToGroup(self, active_map, group, layer, hide=False):
        # add layer to group, remove old layer, return new layer
        active_map.addLayerToGroup(group, layer)
        layer_name = layer.name
        active_map.removeLayer(layer)
        new_layer = active_map.listLayers(layer_name)[0]
        if hide:
            new_layer.visible = False
        return new_layer
        
    def execute(self, parameters, messages):
        """The source code of the tool."""
        # setup
        addLayerToGroup=self.addLayerToGroup
        arcpy.env.overwriteOutput = True
        project = arcpy.mp.ArcGISProject("Current")

        # helper variables
        orig_map = project.activeMap
        orig_layout = project.listLayouts("Layout")[0]
        layouts = []

        # read in parameters
        log("reading in parameters")
        watershed_layers = parameters[0].valueAsText.replace("'","").split(";")
        raster_layer = parameters[1].value
        output_folder_path = parameters[2].valueAsText
        waterbodies_layer = parameters[3].value
        land_use_layer = parameters[4].value

        log("iterating through watersheds")
        for watershed_layer in watershed_layers:
            # create new map and make it active
            log("creating new map and layout")
            active_map = project.copyItem(orig_map, watershed_layer)
            active_map.openView()
            cam = project.activeView.camera

            hydrology_group_layer = active_map.listLayers("Hydrology Analysis")
            if len(hydrology_group_layer) == 0:
                hydrology_group_layer = active_map.createGroupLayer("Hydrology Analysis")
            else:
                hydrology_group_layer = active_map.listLayers("Hydrology Analysis")[0]

            # add watershed layer to new map if needed and rename map to just the name
            if not arcpy.Exists(watershed_layer):
                # need to add the layer to the map and make it a geodatabase
                watershed_layer = active_map.addDataFromPath(watershed_layer)
                active_map.name = watershed_layer.name
                watershed_layer_path = "{}\\{}".format(arcpy.env.workspace, watershed_layer.name)
                arcpy.conversion.ExportFeatures(watershed_layer, watershed_layer_path)
                watershed_layer = active_map.addDataFromPath(watershed_layer_path)
                watershed_layer = addLayerToGroup(active_map, hydrology_group_layer, watershed_layer, True)
                watershed_layer = active_map.listLayers(watershed_layer)[0]
            else:
                watershed_layer = active_map.listLayers(watershed_layer)[0]

            # create a new layout
            new_layout = project.copyItem(orig_layout, watershed_layer.name)
            new_layout.openView()
            layouts.append(new_layout)

            # set layout's map to new map created
            mf = new_layout.listElements("MAPFRAME_ELEMENT")[0]
            mf.map = active_map
            mf.name = watershed_layer.name
            
            # utils
            watershed_layer_id = arcpy.ValidateTableName(watershed_layer.name)

            # clip land use raster
            log("clip land use raster")
            land_use_path = "{}\\{}_{}".format(arcpy.env.workspace, "cblc_clip", watershed_layer_id)
            land_use_clip_layer = arcpy.management.Clip(land_use_layer, "", land_use_path, watershed_layer, "#", "ClippingGeometry")
            land_use_clip_layer = active_map.addDataFromPath(land_use_clip_layer)
            land_use_clip_layer.name = "Watershed Land Use Clip"
            land_use_clip_layer = addLayerToGroup(active_map, hydrology_group_layer, land_use_clip_layer, True)

            # land use raster to polygon
            log("create land use polygons")
            land_use_polygon_path = "{}_{}".format(land_use_path, "to_polygon")        
            land_use_polygon_layer = arcpy.conversion.RasterToPolygon(land_use_clip_layer, land_use_polygon_path, "NO_SIMPLIFY", "LandUse")
            land_use_polygon_layer = active_map.addDataFromPath(land_use_polygon_layer)
            land_use_polygon_layer.name = "Watershed Land Use Clip to Polygon {}".format(watershed_layer_id)
            land_use_polygon_layer = addLayerToGroup(active_map, hydrology_group_layer, land_use_polygon_layer, True)
            
            # join raster fields (rcns and LandUse fields)
            log("join runoff curve numbers to land use polygons")
            arcpy.management.JoinField(land_use_polygon_layer, "LandUse", land_use_clip_layer, "LandUse", ["RCNA", "RCNB", "RCNC", "RCND"])

            # intersect land cover and soils
            log("intersect land cover and soils")
            soils_layer = active_map.listLayers("Soils")[0]  
            intersection_name = "land_use_soils_intersection_{}".format(watershed_layer_id)
            land_use_soils_intersection = arcpy.analysis.PairwiseIntersect([land_use_polygon_layer, "Soils/Soils"], intersection_name)
            land_use_soils_intersection = active_map.addDataFromPath(land_use_soils_intersection)
            land_use_soils_intersection = addLayerToGroup(active_map, hydrology_group_layer, land_use_soils_intersection, True)

            # add column for runoff curve number
            arcpy.management.AddField(land_use_soils_intersection, "RCN", "Short", "", "", "", "Runoff Curve Number")

            # populate runoff curve numbers based off of hydrologic soil group
            log("populate soils data with runoff curve numbers")
            with arcpy.da.UpdateCursor(land_use_soils_intersection, ["hydgrpdcd","RCN", "RCNA", "RCNB", "RCNC", "RCND"]) as cursor:
                for row in cursor:
                    hsg = row[0]
                    if hsg == None:
                        hsg = "D"
                    elif len(hsg) != 1:
                        hsg = hsg.split("/")[0]
                    if hsg == "A":
                        row[1] = row[2]
                    elif hsg == "B":
                        row[1] = row[3]
                    elif hsg == "C":
                        row[1] = row[4]
                    elif hsg == "D":
                        row[1] = row[5]
                    cursor.updateRow(row)

            # delete unecessary fields
            log("cleaning up unecessary soils fields")
            arcpy.management.DeleteField(land_use_soils_intersection, ["LandUse", "hydgrpdcd", "Hydrologic Group - Dominant Conditions", "RCN", "MUSYM"], "KEEP_FIELDS")        

            # add acres field and calculate for land use / soils
            log("calculating acreage of different hydrologic land uses")
            if "Acres" not in [f.name for f in arcpy.ListFields(land_use_soils_intersection)]:
                arcpy.management.AddField(land_use_soils_intersection, "Acres", "FLOAT", field_precision=255, field_scale=2)
            arcpy.management.CalculateGeometryAttributes(in_features=land_use_soils_intersection.name, geometry_property=[["Acres", "AREA_GEODESIC"]], area_unit="ACRES_US")

            # add acres field and calculate for watershed
            log("calculating watershed size")
            if "Acres" not in [f.name for f in arcpy.ListFields(watershed_layer.dataSource)]:
                arcpy.management.AddField(watershed_layer, "Acres", "FLOAT", field_precision=255, field_scale=2)
            arcpy.management.CalculateGeometryAttributes(in_features=watershed_layer, geometry_property=[["Acres", "AREA_GEODESIC"]], area_unit="ACRES_US")
            acres = round(float([row[0] for row in arcpy.da.SearchCursor(watershed_layer, "Acres")][0]),2)
            subtitle = new_layout.listElements("TEXT_ELEMENT", "Subtitle")[0]
            subtitle.text = "Watershed: {} acres".format(acres)
            
            # clip DEM raster
            log("clipping elevation data to watershed")
            clip_1m_dem = raster_layer     
            out_dem_path = "{}\\{}_{}".format(arcpy.env.workspace, "DEM_1m_clip", watershed_layer_id)
            clip_1m_dem = arcpy.management.Clip(clip_1m_dem, "", out_dem_path, watershed_layer, "#", "ClippingGeometry")
            clip_1m_dem = active_map.addDataFromPath(clip_1m_dem)
            clip_1m_dem = addLayerToGroup(active_map, hydrology_group_layer, clip_1m_dem, True)

            # slope map
            log("creating slope map")
            out_slope_path = "{}\\w{}_slope".format(arcpy.env.workspace, len(layouts))
            # breaks the script for unknown reason, possibly related: https://community.esri.com/t5/arcgis-spatial-analyst-questions/using-arcpy-to-create-slope-surfaces/td-p/206039
            #if arcpy.Exists(out_slope_path):
            #    log("exists")
            #    arcpy.management.Delete(out_slope_path)
            slope_raster = arcpy.sa.Slope(clip_1m_dem.name, "PERCENT_RISE", "", "GEODESIC", "METER")
            slope_raster.save(out_slope_path)
            slope_raster = active_map.addDataFromPath(slope_raster)
            slope_raster = addLayerToGroup(active_map, hydrology_group_layer, slope_raster)

            # zonal statistics
            log("finding average slope")
            out_table_name = "zonalstatistics_{}".format(watershed_layer_id)
            out_table_path = "{}\\{}".format(arcpy.env.workspace, out_table_name)
            field_name = arcpy.Describe(watershed_layer).OIDFieldName
            arcpy.sa.ZonalStatisticsAsTable(watershed_layer, field_name, slope_raster, out_table_name, "", "MEAN")
            active_map.addDataFromPath(out_table_path)
            mean_slope = round(float([row[0] for row in arcpy.da.SearchCursor(out_table_path, "MEAN")][0]),2)

            # fill DEM to eventually find flow length of watershed
            log("filling DEM for flow direction calculation")
            out_fill_path = "{}_{}".format(out_dem_path, "fill")
            filled_dem = arcpy.sa.Fill(clip_1m_dem)
            filled_dem.save(out_fill_path)
            filled_dem = active_map.addDataFromPath(filled_dem)
            filled_dem = addLayerToGroup(active_map, hydrology_group_layer, filled_dem, True)

            # calculate flow directions
            log("calculating flow direction")
            out_flowdir_path = "{}\\flow_direction_{}".format(arcpy.env.workspace, watershed_layer_id)
            flow_direction_raster = arcpy.sa.FlowDirection(filled_dem)
            flow_direction_raster.save(out_flowdir_path)
            flow_direction_raster = active_map.addDataFromPath(flow_direction_raster)
            flow_direction_raster = addLayerToGroup(active_map, hydrology_group_layer, flow_direction_raster, True)
            
            # find flow lengths of watershed
            log("creating flow length raster")
            out_flow_length_path = "{}\\flow_length_{}".format(arcpy.env.workspace, watershed_layer_id)
            flow_length_raster = arcpy.sa.FlowLength(flow_direction_raster, "DOWNSTREAM")
            flow_length_raster.save(out_flow_length_path)
            flow_length_raster = active_map.addDataFromPath(flow_length_raster)
            flow_length_raster = addLayerToGroup(active_map, hydrology_group_layer, flow_length_raster, True)
            
            # find maximum flow length
            log("finding max flow length")
            ##flow_length_max_val = float(arcpy.management.GetRasterProperties(flow_length_raster, "MAXIMUM").getOutput(0)
            flow_length_maximum = int(float(arcpy.management.GetRasterProperties(flow_length_raster, "MAXIMUM").getOutput(0))*3.2808)

            # create max flow length raster
            log("creating max flow length raster")
            outZonalStats_path = "{}\\zonal_stats_{}".format(arcpy.env.workspace, watershed_layer_id)
            oidFieldName = arcpy.Describe(watershed_layer).oidFieldName
            outZonalStats = arcpy.sa.ZonalStatistics(watershed_layer, oidFieldName, flow_length_raster, "MAXIMUM")
            outZonalStats.save(outZonalStats_path)

            # raster calculator con to get max flow length and raster to point
            log("creating point at max flow length location")
            max_flow_point_raster_path = "{}\\max_flow_point_{}".format(arcpy.env.workspace, watershed_layer_id)
            max_flow_raster = arcpy.sa.RasterCalculator([outZonalStats.name,flow_length_raster.name], ["max_length", "flow_length"], r' Con(Raster("max_length") == Raster("flow_length"), Raster("flow_length"))')
            max_flow_raster.save(max_flow_point_raster_path)
            max_flow_length_point_path = "{}\\max_flow_length_point_{}".format(arcpy.env.workspace, watershed_layer_id)
            max_flow_length_point = arcpy.conversion.RasterToPoint(max_flow_raster, max_flow_length_point_path,"Value")

            # optimal path as raster
            log("creating optimal flow path raster")           
            optimal_path_raster_path = "{}\\optimal_path_raster_{}".format(arcpy.env.workspace, watershed_layer_id)
            out_path_accumulation_raster = arcpy.sa.OptimalPathAsRaster(max_flow_length_point, flow_length_raster, flow_direction_raster)
            out_path_accumulation_raster.save(optimal_path_raster_path)
            
            # raster to polyline
            log("converting optimal flow path raster to polyline")
            optimal_line_path = "{}\\optimal_line_{}".format(arcpy.env.workspace, watershed_layer_id)            
            optimal_line = arcpy.conversion.RasterToPolyline(out_path_accumulation_raster, optimal_line_path)
            active_map.addDataFromPath(optimal_line_path)

            # setup hydrology worksheet locations
            log("creating hydrology worksheet")
            hydrology_worksheet = 'O:\Stream and Culvert Projects\Hydrology Data Form.xlsx'
            output_worksheet_path = '{}\{}_hydrology.xlsx'.format(output_folder_path, watershed_layer_id)
            output_worksheet_path = pathlib.PureWindowsPath(output_worksheet_path).as_posix()

            # fill out hydrology worksheet
            log("filling out hydrology worksheet")
            hydrology_worksheet = openpyxl.load_workbook(hydrology_worksheet)
            ws_calculations = hydrology_worksheet['Calculations']
            ws_data = hydrology_worksheet['Data']
            ws_calculations["E1"] = project.filePath.split("\\")[-1][:-5]
            ws_calculations['F2'] = datetime.date.today().isoformat()
            ws_calculations['G2'] = datetime.datetime.now().strftime("%H:%M:%S")
            ws_calculations['H2'] = watershed_layer.name
            ws_calculations['G4'] = acres
            ws_calculations['G6'] = flow_length_maximum
            ws_calculations['G7'] = mean_slope

            with arcpy.da.SearchCursor(land_use_soils_intersection, ["RCN", "Acres", "LandUse", "hydgrpdcd"]) as cursor:
                idx = 1
                for row in cursor:
                    rcn = row[0]
                    acres = row[1]
                    land_use = row[2]
                    hsg = row[3]
                    ws_data["C"+str(idx)] = rcn
                    ws_data["D"+str(idx)] = acres
                    ws_data["A"+str(idx)] = land_use
                    ws_data["B"+str(idx)] = hsg
                    idx += 1
                    
            hydrology_worksheet.save(output_worksheet_path)

            # clip waterbodies
            log("clipping waterbodies")
            out_clip_waterbodies_path = "{}\\streams_clip_{}".format(arcpy.env.workspace, watershed_layer_id)
            waterbodies_clip_layer = arcpy.analysis.Clip(waterbodies_layer, watershed_layer, out_clip_waterbodies_path)
            waterbodies_clip_layer = active_map.addDataFromPath(waterbodies_clip_layer)
            waterbodies_clip_layer.name = "Waterbodies"
            waterbodies_clip_layer = addLayerToGroup(active_map, hydrology_group_layer, waterbodies_clip_layer)

            # waterbodies styling
            log("styling waterbodies")
            sym = waterbodies_clip_layer.symbology
            sym.renderer.symbol.color = {'RGB' : [0, 0, 0, 0]}
            sym.renderer.symbol.outlineColor = {'RGB' : [0, 112, 255, 100]}
            sym.renderer.symbol.size = 1.5
            waterbodies_clip_layer.symbology = sym
            waterbodies_clip_layer.showLabels = True
            
            # waterbody name
            log("updating waterbody label")
            waterbody_label_name = waterbodies_clip_layer.listLabelClasses()[0]
            waterbody_label_name.visible = True
            waterbody_label_name.expression = "$feature.NAME"
            l_cim = waterbodies_clip_layer.getDefinition('V3')
            lc = l_cim.labelClasses[0]

            # Update text properties of label
            lc.textSymbol.symbol.height = 10
            lc.textSymbol.symbol.symbol.symbolLayers = [
                {
                    "type": "CIMSolidFill",
                    "enable": True,
                    "color": {
                        "type": "CIMRGBColor",
                        "values": [0, 112, 255, 100]
                        }
                    }
                ]
            lc.maplexLabelPlacementProperties.linePlacementMethod = "OffsetHorizontalFromLine"
            lc.maplexLabelPlacementProperties.thinDuplicateLabels = True
            lc.maplexLabelPlacementProperties.thinningDistanceUnit = "Map"
            sym = arcpy.cim.CreateCIMObjectFromClassName('CIMPolygonSymbol', 'V3')
            sym.symbolLayers = [
                {
                    "type": "CIMSolidFill",
                    "enable": True,
                    "color": {
                        "type": "CIMRGBColor",
                        "values": [255, 255, 255, 100]
                        }
                    }
                ]
            lc.textSymbol.symbol.haloSize = 1
            lc.textSymbol.symbol.haloSymbol = sym
            waterbodies_clip_layer.setDefinition(l_cim)
            
            # create waterbody classification
            waterbody_label_classification = waterbodies_clip_layer.createLabelClass("Waterbody Classification", "$feature.STANDARD")
            waterbody_label_classification.visible = True
            waterbody_label_classification.expression = "$feature.STANDARD"
            l_cim = waterbodies_clip_layer.getDefinition('V3')
            lc = l_cim.labelClasses[1]

            # Update text properties of label
            lc.textSymbol.symbol.height = 10
            lc.textSymbol.symbol.symbol.symbolLayers = [
                {
                    "type": "CIMSolidFill",
                    "enable": True,
                    "color": {
                        "type": "CIMRGBColor",
                        "values": [0, 112, 255, 100]
                        }
                    }
                ]
            #lc.standardLabelPlacementProperties.numLabelsOption = "OneLabelPerName"
            lc.maplexLabelPlacementProperties.linePlacementMethod = "OffsetHorizontalFromLine"
            lc.maplexLabelPlacementProperties.thinDuplicateLabels = True            
            lc.maplexLabelPlacementProperties.thinningDistanceUnit = "Map"
            lc.textSymbol.symbol.haloSize = 1
            lc.textSymbol.symbol.haloSymbol = sym            
            waterbodies_clip_layer.setDefinition(l_cim)

            # move slope layer second
            log("moving layers and adjusting map zoom")
            active_map.moveLayer(waterbodies_clip_layer, slope_raster, "AFTER")
            
            # zoom to layer in map object
            ext = arcpy.Describe(watershed_layer).extent
            cam.setExtent(ext)

            # zoom layout to last active map
            mf = new_layout.listElements("MAPFRAME_ELEMENT")[0]
            mf.camera.setExtent(mf.getLayerExtent(watershed_layer))
            mf.camera.scale = mf.camera.scale * 1.1

            # Need to close layouts for camera change to take effect
            project.closeViews("LAYOUTS")

            # turn off unimportant legend item
            log("turning off unimportant legend items")
            legend = new_layout.listElements("LEGEND_ELEMENT")[0]
            legend_items = legend.items
            use_layer_names = [ watershed_layer.name, waterbodies_clip_layer.name ]
            for item in legend_items:
                if item.name in use_layer_names:
                    item.visible = True
            else:
                item.visible = False

        log("exporting layouts")
        for layout in layouts:
            layout.openView()
            layout_file_path = "{}\{}.pdf".format(output_folder_path, layout.name)
            layout.exportToPDF(layout_file_path)
                
        # save and exit program successfully
        log("saving project")
        project.save()

        # open hydrology worksheet
        log("opening hydrology worksheet folder")
        os.startfile(output_folder_path)        

        return


class RunoffPotential:
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Runoff Potential"
        self.category = "Hydrology"
        self.description = "Calculate the runoff potential of the given watershed"

    def getParameterInfo(self):
        """Define parameter definitions"""
        param0 = arcpy.Parameter(
            displayName="Watershed Boundary Layer",
            name="watershed",
            datatype="GPFeatureLayer",
            parameterType="Required",
            direction="Input")
        param0.filter.list = ["Polygon"]
        param0.controlCLSID = '{60061247-BCA8-473E-A7AF-A2026DDE1C2D}' # allows polygon creation

        param1 = arcpy.Parameter(
            displayName="Output Features",
            name="out_features",
            datatype="DEFeatureClass",
            parameterType="Required",
            direction="Output")
        param1.parameterDependencies = [param0.name]

        param2 = arcpy.Parameter(
            displayName="Soils Feature Class",
            name="soils",
            datatype="GPFeatureLayer",
            parameterType="Required",
            direction="Input")
        param2.filter.list = ["Polygon"]

        # TODO: ensure RCN fields (A,B,C,D) are present
        param3 = arcpy.Parameter(
            displayName="Land Use Data",
            name="land_use",
            datatype="GPRasterLayer",
            parameterType="Required",
            direction="Input")

        # TODO: summarize RCN for watershed into table?

        params = [param0, param1, param2, param3]
        return params
        
    def execute(self, parameters, messages):
        """The source code of the tool."""
        arcpy.env.overwriteOutput = True
        arcpy.env.qualifiedFieldNames = False

        # read in parameters
        watershed = parameters[0].value
        output_fc = parameters[1].valueAsText
        soils = parameters[2].value
        land_use_raster = parameters[3].value

        # project setup
        project = arcpy.mp.ArcGISProject("Current")
        active_map = project.activeMap

        
        #colorramps = project.listColorRamps()
        #for i in colorramps:
        #    log(i.name)
        #return

        # scratch layers
        log("creating scratch layers")
        soils_scratch = arcpy.CreateScratchName("soils_scratch", data_type="FeatureClass", workspace=arcpy.env.scratchFolder)
        land_use_raster_clip = "{}\\land_use_raster_clip".format(arcpy.env.workspace)
        scratch_land_use_polygon = arcpy.CreateScratchName("scratch_land_use_polygon", data_type="FeatureClass", workspace=arcpy.env.scratchFolder)
        scratch_joined_land_use_polygon = arcpy.CreateScratchName("scratch_joined_land_use_polygon", data_type="FeatureClass", workspace=arcpy.env.scratchFolder)
        scratch_pairwise_intersection = arcpy.CreateScratchName("scratch_pairwise_intersection", data_type="FeatureClass", workspace=arcpy.env.scratchFolder)

        # clip soils
        log("clipping soils to watershed")
        arcpy.analysis.Clip(soils, watershed, soils_scratch)

        # clip land use raster
        log("clipping land use raster to watershed")
        out_land_use_raster_clip = arcpy.sa.ExtractByMask(land_use_raster, watershed, "INSIDE")
        out_land_use_raster_clip.save(land_use_raster_clip)
        
        # convert land usage output to polygon
        # TODO: get land use field as param
        log("converting land use areas to polygon")
        arcpy.conversion.RasterToPolygon(land_use_raster_clip, scratch_land_use_polygon, "SIMPLIFY", "LandUse", "SINGLE_OUTER_PART")

        # join land use attributes to land use polygons
        # TODO: get land use field as param
        log("join land use RCN fields into polygon")
        joined_land_use_polygon = arcpy.management.AddJoin(scratch_land_use_polygon, "LandUse", land_use_raster_clip, "LandUse", "KEEP_ALL", "INDEX_JOIN_FIELDS")
        arcpy.management.CopyFeatures(joined_land_use_polygon, scratch_joined_land_use_polygon)

        # intersect land use and soils
        log("intersect land uses and soils")
        arcpy.analysis.PairwiseIntersect(
            in_features=[scratch_joined_land_use_polygon, soils_scratch],
            out_feature_class=scratch_pairwise_intersection,
            join_attributes="ALL",
            cluster_tolerance=None,
            output_type="INPUT"
        )

        # calculate RCN from HSG
        # TODO: get RCN, HSG, RCNA/B/C/D from params?
        log("calculate RCN from HSG")
        arcpy.management.CalculateField(
            in_table=scratch_pairwise_intersection,
            field="RCN",
            expression="calculate_value(!hydgrpdcd!, !RCNA!,!RCNB!,!RCNC!,!RCND!)",
            expression_type="PYTHON3",
            code_block="""def calculate_value(hsg, rcna, rcnb, rcnc, rcnd):
                if hsg == "A":
                    return rcna
                elif hsg == "B":
                    return rcnb
                elif hsg == "C":
                    return rcnc
                else:
                    return rcnd""",
            field_type="DOUBLE",
            enforce_domains="NO_ENFORCE_DOMAINS"
        )

        # dissolve RCN boundaries
        # TODO: get RCN field from params?
        log("dissolve RCN boundaries")
        arcpy.analysis.PairwiseDissolve(
            in_features=scratch_pairwise_intersection,
            out_feature_class=output_fc,
            dissolve_field="RCN",
            statistics_fields=None,
            multi_part="MULTI_PART",
            concatenation_separator=""
        )

        # add runoff layer to map
        log("add runoff layer to map")
        lyr = active_map.addDataFromPath(output_fc)

        # symbology based off of RCN range
        log("setting runoff layer symbology")
        if lyr.isFeatureLayer:
            sym = lyr.symbology
            if hasattr(sym, 'renderer'):
              if sym.renderer.type == 'SimpleRenderer':
                sym.updateRenderer('GraduatedColorsRenderer')
                sym.renderer.breakCount = 5
                sym.renderer.classificationMethod = 'NaturalBreaks'
                sym.renderer.classificationField = 'RCN'
                sym.renderer.colorRamp = project.listColorRamps('Orange-Red (5 Classes)')[0]
                lyr.symbology = sym

        # delete not needed scratch layers
        log("delete unused layers")
        arcpy.management.Delete([soils_scratch, land_use_raster_clip, scratch_land_use_polygon, scratch_joined_land_use_polygon, scratch_pairwise_intersection])
        
        # save project
        log("saving project")
        project.save()    

        return
