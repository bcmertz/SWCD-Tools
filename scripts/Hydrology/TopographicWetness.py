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
from validate_spatial_reference import validate_spatial_reference as validate

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

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool parameter."""
        validate(parameters)
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
        output_file = parameters[2].valueAsText

        # create scratch layers
        log("creating scratch layers")
        scratch_dem = "{}\\dem_raster_clip".format(arcpy.env.workspace)
        fill_raster_scratch = arcpy.CreateScratchName("tmp", data_type="RasterDataset", workspace=arcpy.env.scratchFolder)
        flow_accumulation_scratch = arcpy.CreateScratchName("tmp", data_type="RasterDataset", workspace=arcpy.env.scratchFolder)

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

        log("cleaning up")
        arcpy.management.Delete([scratch_dem,fill_raster_scratch,flow_accumulation_scratch])

        # save and exit program successfully
        log("saving project")
        project.save()
        
        return
