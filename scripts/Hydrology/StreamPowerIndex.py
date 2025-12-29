# --------------------------------------------------------------------------------
# Name:        Stream Power Index (SPII)
# Purpose:     TODO
#
# License:     GNU Affero General Public License v3.
#              Full license in LICENSE file, or at <https://www.gnu.org/licenses/>
# --------------------------------------------------------------------------------

import math
import arcpy

from helpers import license
from helpers import print_messages as log
from helpers import setup_environment as setup
from helpers import validate_spatial_reference as validate

class StreamPowerIndex(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Stream Power Index (SPI)"
        self.description = "Calculate Stream Power Index"
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
            displayName="Analysis Mask - Stream, AOI, etc",
            name="stream",
            datatype="GPFeatureLayer",
            parameterType="Optional",
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

    def isLicensed(self):
        """Set whether the tool is licensed to execute."""
        return license(['Spatial'])

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
        dem_layer = parameters[0].value
        dem = arcpy.Raster(dem_layer.name)
        extent = parameters[1].value
        mask = parameters[2].value
        output_file = parameters[3].valueAsText

        # set analysis extent
        if extent:
            arcpy.env.extent = extent

        # fill raster
        log("filling raster")
        fill_raster_scratch = arcpy.sa.Fill(dem)

        # flow accumulation
        log("calculating flow accumulation")
        flow_accumulation_raster = arcpy.sa.DeriveContinuousFlow(fill_raster_scratch, flow_direction_type="MFD")
        flow_accumulation = arcpy.sa.Float(flow_accumulation_raster)

        # TODO: convert from # cells to units

        # TODO: limit analysis to mask
        if mask:
            log("masking analysis area")
            arcpy.env.cellSize = dem_layer.name
            arcpy.env.snapRaster = dem_layer.name
            arcpy.env.mask = mask.name

        # calculate slope
        log("calculating slope")
        # TODO: percent, units
        # TODO: TWI?
        slope_raster = arcpy.sa.Slope(dem, "DEGREE", "", "GEODESIC", "METER")

        # convert slope to radians
        log("converting slope raster to radians")
        slope_radians = arcpy.sa.Float(slope_raster) * (math.pi / 180)

        # calculate slope tangent
        log("calculating slope tangent")
        out_slope_tan = arcpy.sa.Tan(slope_radians)

        # calculate stream power index (SPI)
        log("calculating stream power index")
        out_SPI = arcpy.sa.Ln((flow_accumulation * out_slope_tan) + 0.001)
        out_SPI.save(output_file)

        # add SPI to map
        log("adding raster to map")
        spi_layer = active_map.addDataFromPath(output_file)

        # update raster symbology
        #log("updating SPI symbology")
        #sym = spi_layer.symbology
        #if hasattr(sym, 'colorizer'):
        #    if sym.colorizer.type != "RasterStretchColorizer":
        #        sym.updateColorizer("RasterStretchColorizer")
        #    sym.colorizer.colorRamp = project.listColorRamps('Blue Bright')[0]
        #    spi_layer.symbology = sym

        # save and exit program successfully
        log("saving project")
        project.save()

        return
