# --------------------------------------------------------------------------------
# Name:        Stream Elevation
# Purpose:     This tool is a work-in-progress tool which will collect elevation
#              data along a drainage network for visualization.
#
# License:     GNU Affero General Public License v3.
#              Full license in LICENSE file, or at <https://www.gnu.org/licenses/>
# --------------------------------------------------------------------------------

import arcpy

from helpers import *
import print_messages as log
import setup_environment as setup
import validate_spatial_reference as validate
import license as license

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

    def isLicensed(self):
        """Set whether the tool is licensed to execute."""
        return license([])

    def updateMessages(self, parameters):
        ".sa""Modify the messages created by internal validation for each tool parameter."""
        validate(parameters)
        return

    def execute(self, parameters, messages):
        """The source code of the tool."""
        # Setup
        log("setting up project")
        project, active_map = setup()

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
