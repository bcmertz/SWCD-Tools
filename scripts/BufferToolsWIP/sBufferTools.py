# -*- coding: utf-8 -*-

import arcpy
import math

# import log tool
import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), "../helpers"))
from printmessages import printMessages

# TODO: buffer work area by 1/2 max width of cluster to prevent cluster / edge of work area overlap
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
        # TODO: add logs
        """The source code of the tool."""
        log=printMessages
        arcpy.env.overwriteOutput = True

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
        scratch_dissolve = arcpy.CreateScratchName("scratch_dissolve", data_type="DEFeatureClass", workspace=arcpy.env.scratchFolder)
        scratch_buffer = arcpy.CreateScratchName("scratch_buffer", data_type="DEFeatureClass", workspace=arcpy.env.scratchFolder)

        # dissolve
        arcpy.management.Dissolve(planting_area, scratch_dissolve, multi_part="MULTI_PART")
        
        # calculate total area of planting
        field_name = "Acres"
        arcpy.management.AddField(scratch_dissolve, field_name, "FLOAT")
        arcpy.management.CalculateGeometryAttributes(in_features=scratch_dissolve, geometry_property=[[field_name, "AREA_GEODESIC"]], area_unit="ACRES_US")

        # determine number of sampling plots
        # < 1 acres - plot radius 11.8ft; 10 / acre
        # < 5 acres - plot radius 26.3ft; 2 / acre
        # > 5 acres - plot radius 26.3ft; 1 / acre
        values = [row[0] for row in arcpy.da.SearchCursor(scratch_dissolve, field_name)]
        acreage = max(set(values))

        radius = 11.8/3
        num = 1

        if acreage < 1:
            num = int(math.ceil(acreage * 10))
        elif acreage >= 1 and acreage < 5:
            num = int(math.ceil(acreage * 2))
            radius = 26.3/3
        elif acreage >= 5 and not reduce_acreage:
            num = int(math.ceil(acreage * 2))
            radius = 26.3/3
        elif acreage >= 5 and reduce_acreage:
            num = int(math.ceil(acreage * 1))
            radius = 26.3/3
            
        # create buffer inside the planting area
        arcpy.analysis.PairwiseBuffer(scratch_dissolve, scratch_buffer, -radius)

        # create random plot centers
        arcpy.management.CreateSpatialSamplingLocations(scratch_buffer, output_file, sampling_method="STRAT_POLY", strata_id_field=None, strata_count_method="PROP_AREA", num_samples=num, geometry_type="POINT")

        # add plots to map
        # TODO: or add circles to map (would need to create circles)
        active_map.addDataFromPath(output_file)
                
        # TODO: output plot coordinates to csv at output file location
        
        # cleanup
        log("deleting unneeded data")
        arcpy.management.Delete([scratch_buffer, scratch_dissolve])

        # save
        log("saving project")
        project.save()
            
        return

# TODO: buffer work area by 1/2 max width of cluster to prevent cluster / edge of work area overlap
class ShrubClusters:
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Shrub Cluster Tool"
        self.description = "Shrub Cluster Tool"
        self.category = "Buffer tools"
        self.canRunInBackground = False

    def getParameterInfo(self):
        """Define the tool parameters."""
        param0 = arcpy.Parameter(
            displayName="Analysis Area",
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
            displayName="Cluster Width (ft)",
            name="width",
            datatype="GPDouble",
            parameterType="Required",
            direction="Input")
        
        param3 = arcpy.Parameter(
            displayName="Number of clusters",
            name="number",
            datatype="GPDouble",
            parameterType="Required",
            direction="Input")

        params = [param0, param1, param2, param3]
        return params

    def isLicensed(self):
        """Set whether the tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        # default search interval
        return

    def execute(self, parameters, messages):
        """The source code of the tool."""
        log=printMessages
        arcpy.env.overwriteOutput = True

        log("reading in parameters")
        area = parameters[0].value
        output_file = parameters[1].valueAsText
        width = parameters[2].value
        number = parameters[3].value

        # project setup
        log("setting up project")
        project = arcpy.mp.ArcGISProject("Current")
        active_map = project.activeMap

        # create scratch layers
        log("creating scratch layers")
        scratch_points = arcpy.CreateScratchName("scratch_points", data_type="DEFeatureClass", workspace=arcpy.env.scratchFolder)
        scratch_buffer = arcpy.CreateScratchName("scratch_buffer", data_type="DEFeatureClass", workspace=arcpy.env.scratchFolder)
        scratch_bounding = arcpy.CreateScratchName("scratch_bounding", data_type="DEFeatureClass", workspace=arcpy.env.scratchFolder)
        
        # create point locations
        arcpy.management.CreateSpatialSamplingLocations(
            in_study_area=area,
            out_features=scratch_points,
            sampling_method="SYSTEMATIC",
            bin_shape="HEXAGON",
            bin_size=number,
            geometry_type="POINT",
            spatial_relationship="HAVE_THEIR_CENTER_IN"
        )

        # buffer points by width
        arcpy.analysis.Buffer(
            in_features=scratch_points,
            out_feature_class=scratch_buffer,
            buffer_distance_or_field="{} Feet".format(width),
        )

        # make square around buffer
        arcpy.management.MinimumBoundingGeometry(
            in_features=scratch_buffer,
            out_feature_class=scratch_bounding,
            geometry_type="ENVELOPE",
            group_option="NONE",
        )

        # convert to feature class
        arcpy.management.FeatureEnvelopeToPolygon(
            in_features=scratch_bounding,
            out_feature_class=output_file,
            single_envelope="SINGLEPART"
        )

        # cleanup
        log("deleting unneeded data")
        arcpy.management.Delete([scratch_points, scratch_buffer, scratch_bounding])

        # save
        log("saving project")
        project.save()
            
        return


























    

