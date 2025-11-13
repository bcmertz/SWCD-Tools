# -*- coding: utf-8 -*-
import arcpy

# import log tool
import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), "../helpers"))
from printmessages import printMessages as log

class ShrubClusters:
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Shrub Cluster Tool"
        self.description = "Shrub Clusters"
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













    

