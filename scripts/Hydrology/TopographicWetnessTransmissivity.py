# --------------------------------------------------------------------------------
# Name:        Topographic Wetness Index (TWI) - Soil Transmissivity
# Purpose:     This tool calculates the TWI for an estimate of hydrologic activity.
#              It takes into account soil transmissivity - or the average K_sat
#              hydraulic conductivity of the soil above restrictive layer
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

class TopographicWetnessTransmissivity(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "WIP Topographic Wetness Index (TWI) - Soil Transmissivity"
        self.description = "Calculate Topographic Wetness of a given area incorporating soil transmissivity"
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
            displayName="Transmissivity",
            name="transmissivity",
            datatype="GPRasterLayer",
            parameterType="Required",
            direction="Input")

        param2 = arcpy.Parameter(
            displayName="Analysis Area",
            name="analysis_area",
            datatype="GPExtent",
            parameterType="Optional",
            direction="Input")
        param2.controlCLSID = '{15F0D1C1-F783-49BC-8D16-619B8E92F668}'

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
        raster_layer = parameters[0].value
        transmissivity = parameters[1].value
        XMin = parameters[2].value.XMin if parameters[1].value else 0
        YMin = parameters[2].value.YMin if parameters[1].value else 0
        XMax = parameters[2].value.XMax if parameters[1].value else 0
        YMax = parameters[2].value.YMax if parameters[1].value else 0
        extent = arcpy.Extent(XMin, YMin, XMax, YMax)
        if parameters[2].value:
                extent.spatialReference = parameters[2].value.spatialReference
        output_file = parameters[3].valueAsText

        # create scratch layers
        log("creating scratch layers")
        scratch_dem = "{}\\dem_raster_clip".format(arcpy.env.workspace)
        scratch_soils_raster = "{}\\scratch_soils".format(arcpy.env.workspace)
        fill_raster_scratch = arcpy.CreateScratchName("tmp", data_type="RasterDataset", workspace=arcpy.env.scratchFolder)
        flow_accumulation_scratch = arcpy.CreateScratchName("tmp", data_type="RasterDataset", workspace=arcpy.env.scratchFolder)

        if parameters[2].value:
            # clip DEM raster to the study area
            log("clipping raster to analysis area")
            rectangle = "{} {} {} {}".format(extent.XMin, extent.YMin, extent.XMax, extent.YMax)
            arcpy.management.Clip(raster_layer, rectangle, scratch_dem)
            raster_layer = scratch_dem

            # clip soil raster to the study area
            log("clipping soil raster to analysis area")
            rectangle = "{} {} {} {}".format(extent.XMin, extent.YMin, extent.XMax, extent.YMax)
            arcpy.management.Clip(transmissivity, rectangle, scratch_soils_raster)
            transmissivity = scratch_soils_raster

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
        out_TWI = arcpy.sa.Ln(adjusted_flow_accumulation / ((transmissivity * out_slope_tan) + 0.01)) # add 0.01 to avoid infinities, consider alternatives
        out_TWI.save(output_file)

        # add TWI to map
        log("adding twi to map")
        twi_layer = active_map.addDataFromPath(output_file)

        # update raster symbology
        log("updating twi symbology")
        sym = twi_layer.symbology
        if hasattr(sym, 'colorizer'):
            if sym.colorizer.type != "RasterStretchColorizer":
                sym.updateColorizer("RasterStretchColorizer")
            sym.colorizer.colorRamp = project.listColorRamps('Blue Bright')[0]
            twi_layer.symbology = sym

        log("cleaning up")
        arcpy.management.Delete([scratch_dem,fill_raster_scratch,flow_accumulation_scratch,scratch_soils_raster])

        # save and exit program successfully
        log("saving project")
        project.save()

        return
