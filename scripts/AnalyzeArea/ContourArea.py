# --------------------------------------------------------------------------------
# Name:        Contour Area
# Purpose:     This tool takes an area of interest and creates the specified
#              contours in it
#
# License:     GNU Affero General Public License v3.
#              Full license in LICENSE file, or at <https://www.gnu.org/licenses/>
# --------------------------------------------------------------------------------

import arcpy

# setup helpers
import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), "../helpers"))
from print_messages import print_messages as log
from setup_environment import setup_environment as setup
from validate_spatial_reference import validate_spatial_reference as validate
from license import license as license

class ContourArea(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Contour Area"
        self.description = "Contour specific area of DEM"
        self.category = "Analyze Area"
        self.canRunInBackground = True

    def getParameterInfo(self):
        """Define parameter definitions"""
        param0 = arcpy.Parameter(
            displayName="DEM",
            name="dem",
            datatype="GPRasterLayer",
            parameterType="Required",
            direction="Input")

        param1 = arcpy.Parameter(
            displayName="Contour Area",
            name="contour_area",
            datatype="GPExtent",
            parameterType="Required",
            direction="Input")
        param1.controlCLSID = '{15F0D1C1-F783-49BC-8D16-619B8E92F668}'

        param2 = arcpy.Parameter(
            displayName="Output Features",
            name="out_features",
            datatype="DEFeatureClass",
            direction="Output")

        param2.parameterDependencies = [param0.name]
        param2.schema.clone = True

        param3 = arcpy.Parameter(
            displayName="Contour Interval (ft)",
            name="contour_interval",
            datatype="GPLong",
            parameterType="Required",
            direction="Input")

        # TODO: just ask for DEM units instead
        #desc = arcpy.Describe(raster_layer)
        #log(desc.spatialReference.linearUnitName)
        param4 = arcpy.Parameter(
            displayName="Z Factor",
            name="z_factor",
            datatype="GPDouble",
            parameterType="Required",
            direction="Input")

        params = [param0, param1, param2, param3, param4]
        return params

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool parameter."""
        validate(parameters)
        return

    def isLicensed(self):
        """Set whether the tool is licensed to execute."""
        return license(['Spatial'])

    def execute(self, parameters, messages):
        """The source code of the tool."""
        # Setup
        log("setting up project")
        project, active_map = setup()

        raster_layer = parameters[0].value
        extent = arcpy.Extent(XMin = parameters[1].value.XMin,
                              YMin = parameters[1].value.YMin,
                              XMax = parameters[1].value.XMax,
                              YMax = parameters[1].value.YMax)
        extent.spatialReference = parameters[1].value.spatialReference
        output_file = parameters[2].valueAsText
        contour_interval = parameters[3].valueAsText
        z_factor = parameters[4].valueAsText

        log("clipping raster")
        scratch_dem = arcpy.CreateScratchName("temp",
                                               data_type="RasterDataset",
                                               workspace=arcpy.env.scratchFolder)

        rectangle = "{} {} {} {}".format(extent.XMin, extent.YMin, extent.XMax, extent.YMax)
        arcpy.management.Clip(raster_layer, rectangle, scratch_dem)

        log("creating contour")
        arcpy.sa.Contour(scratch_dem, output_file, contour_interval, z_factor=z_factor)

        log("adding contours to map")
        active_map.addDataFromPath(output_file)

        # Delete scratch dataset
        log("finishing up")
        arcpy.management.Delete(scratch_dem)

        return
