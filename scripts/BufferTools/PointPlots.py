# -*- coding: utf-8 -*-
import arcpy
import math

# import log tool
import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), "../helpers"))
from printmessages import printMessages as log

class PointPlots:
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Point Plots"
        self.description = "Point Plots"
        self.category = "Buffer tools"
        self.canRunInBackground = False

    def getParameterInfo(self):
        """Define the tool parameters."""
        param0 = arcpy.Parameter(
            displayName="Project Area",
            name="polygon",
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
            displayName="Reduce surveyed area for large (> 5 acres) buffers to 5%?",
            name="reduce_acreage",
            datatype="GPBoolean",
            parameterType="Optional",
            direction="Input")

        params = [param0, param1, param2]
        return params

    def isLicensed(self):
        """Set whether the tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        # default search interval
        return

    def execute(self, parameters, messages):
        """The source code of the tool."""
        arcpy.env.overwriteOutput = True
        log("test76")

        log("reading in parameters")
        planting_area = parameters[0].value
        output_file = parameters[1].valueAsText
        reduce_acreage = parameters[2].value

        # project setup
        log("setting up project")
        project = arcpy.mp.ArcGISProject("Current")
        active_map = project.activeMap

        # create scratch layers
        log("creating scratch layers")
        scratch_buffer = arcpy.CreateScratchName("scratch_buffer", data_type="DEFeatureClass", workspace=arcpy.env.scratchFolder)
        scratch_dissolve = arcpy.CreateScratchName("scratch_dissolve", data_type="DEFeatureClass", workspace=arcpy.env.scratchFolder)
        log(scratch_buffer)

        # dissolve
        log("dissolve polygons")
        arcpy.management.Dissolve(planting_area, scratch_dissolve, multi_part="MULTI_PART")
        
        # calculate total area of planting
        log("calculate acreage")
        field_name = "Acres"
        arcpy.management.AddField(scratch_dissolve, field_name, "FLOAT")
        arcpy.management.CalculateGeometryAttributes(in_features=scratch_dissolve, geometry_property=[[field_name, "AREA_GEODESIC"]], area_unit="ACRES_US")

        # determine number of sampling plots
        # < 1 acres - plot radius 11.8ft; 10 / acre
        # < 5 acres - plot radius 26.3ft; 2 / acre
        # > 5 acres - plot radius 26.3ft; 1 / acre
        values = [row[0] for row in arcpy.da.SearchCursor(scratch_dissolve, field_name)]
        acreage = max(set(values))

        radius = 11.8
        num = 1

        if acreage < 1:
            num = int(math.ceil(acreage * 10))
        elif acreage >= 1 and acreage < 5:
            num = int(math.ceil(acreage * 2))
            radius = 26.3
        elif acreage >= 5 and not reduce_acreage:
            num = int(math.ceil(acreage * 2))
            radius = 26.3
        elif acreage >= 5 and reduce_acreage:
            num = int(math.ceil(acreage * 1))
            radius = 26.3

        # convert from feet to meter
        radius = radius / 3.2808
            
        # create buffer inside the planting area
        log("buffer output area")
        arcpy.analysis.PairwiseBuffer(scratch_dissolve, scratch_buffer, -radius)

        # create random plot centers
        log("create sampling locations")
        arcpy.management.CreateSpatialSamplingLocations(scratch_buffer, output_file, sampling_method="STRAT_POLY", strata_id_field=None, strata_count_method="PROP_AREA", num_samples=num, geometry_type="POINT", min_distance=radius*2)

        # add plots to map
        # TODO: or add circles to map (would need to create circles)
        log("add data to map")
        active_map.addDataFromPath(output_file)
                
        # TODO: output plot coordinates to csv at output file location
        
        # cleanup
        log("deleting unneeded data")
        arcpy.management.Delete([scratch_buffer, scratch_dissolve])

        # save
        log("saving project")
        project.save()
            
        return
