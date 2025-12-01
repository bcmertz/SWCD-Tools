# --------------------------------------------------------------------------------
# Name:        Slope Area
# Purpose:     This tool takes an area of interest and creates a slope raster
#              for it
#
# License:     GNU Affero General Public License v3.
#              Full license in LICENSE file, or at <https://www.gnu.org/licenses/>
# --------------------------------------------------------------------------------

import arcpy

from helpers import license
from helpers import print_messages as log
from helpers import setup_environment as setup
from helpers import validate_spatial_reference as validate

class SlopeArea(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Slope Area"
        self.description = "Create slope raster for specific area of DEM"
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
            displayName="Slope Area",
            name="slope_area",
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
            displayName="Output Measurement",
            name="measurement",
            datatype="GPString",
            parameterType="Optional",
            direction="Input")
        param3.filter.list = ["Degree", "Percent Slope"]

        param4 = arcpy.Parameter(
            displayName="Z Unit",
            name="z_unit",
            datatype="GPString",
            parameterType="Optional",
            direction="Input")
        param4.filter.list = ["METER", "FOOT"]

        params = [param0, param1, param2, param3, param4]
        return params

    def isLicensed(self):
        """Set whether the tool is licensed to execute."""
        return license(['Spatial'])

    def updateParameters(self, parameters):
        # Default stream threshold value
        if parameters[3].value == None:
            parameters[3].value = "Percent Slope"
        if parameters[4].value == None:
            parameters[4].value = "METER"

        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool parameter."""
        validate(parameters)
        return

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
        measurement = parameters[3].valueAsText
        z_unit = parameters[4].valueAsText

        if measurement == "Degree":
            measurement = "DEGREE"
        elif measurement == "Percent Slope":
            measurement = "PERCENT_RISE"
        else:
            raise ValueError("Bad output measurement value")

        if z_unit != "METER" and z_unit != "FOOT":
            raise ValueError("Bad z-unit value")

        log("clipping DEM")
        scratch_dem = arcpy.CreateScratchName("temp",
                                               data_type="RasterDataset",
                                               workspace=arcpy.env.scratchFolder)
        rectangle = "{} {} {} {}".format(extent.XMin, extent.YMin, extent.XMax, extent.YMax)
        arcpy.management.Clip(raster_layer, rectangle, scratch_dem)

        log("creating slope raster")
        out_slope = arcpy.sa.Slope(scratch_dem, measurement, "", "GEODESIC", z_unit)
        log("saving slope raster")
        out_slope.save(output_file)
        log("adding slope raster")
        active_map.addDataFromPath(output_file)

        # Delete scratch dataset
        arcpy.management.Delete(scratch_dem)

        return
