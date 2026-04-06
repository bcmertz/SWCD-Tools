# --------------------------------------------------------------------------------------------------
# Name:        Topographic Position Index (TPI)
# Purpose:     Calculates topographic position index for a raster and a given neighborhood size. This
#              allows versions of ArcGIS Pro earlier than 3.6 to calculate TPI.
#
# License:     Contextual Copyleft AI (CCAI) License v1.0.
#              Full license in LICENSE file.
# --------------------------------------------------------------------------------------------------

import arcpy

from ..helpers import license, reload_module, log, convert_length, cell_length, convert_length
from ..helpers import setup_environment as setup
from ..helpers import validate_spatial_reference as validate

class TopographicPositionIndex(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Topographic Position Index (TPI)"
        self.description = "Calculate Topographic Position Index (TPI)"
        self.category = "Terrain Analysis"
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
            displayName="Neighborhood",
            name="neighborhood",
            datatype="GPSANeighborhood",
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

    def updateParameters(self, parameters):
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool parameter."""
        validate(parameters)

        return

    @reload_module(__name__)
    def execute(self, parameters, messages):
        """The source code of the tool."""
        # Setup
        log("setting up project")
        project, active_map = setup()

        # read in parameters
        log("reading in parameters")
        dem_layer = parameters[0].value
        dem = arcpy.Raster(dem_layer.name)
        extent = parameters[1].value
        neighborhood = parameters[2].valueAsText
        output_file = parameters[3].valueAsText

        # set analysis extent
        if extent:
            arcpy.env.extent = extent

        # calculate mean
        log("calculating mean elevations in neighborhood")
        mean = arcpy.sa.FocalStatistics(
            in_raster=dem,
            neighborhood=neighborhood,
            statistics_type="MEAN",
            ignore_nodata="DATA",
        )

        # calculate smoothed vs unsmoothed diference
        # positive values indicate DEM elevations above average in neighborhood
        log("calculating topographic position index")
        diff = dem - mean

        # normalize tpi values to standard deviation (Weiss 2001)
        std_dev = float(arcpy.management.GetRasterProperties(diff, "STD").getOutput(0))
        tpi_std = arcpy.sa.Int(((diff / std_dev) * 100) + 0.5)
        tpi_std.save(output_file)

        # add results to map
        log("adding results to map")
        tpi_raster = active_map.addDataFromPath(output_file)

        # update raster symbology
        log("updating tpi raster symbology")
        sym = tpi_raster.symbology
        if hasattr(sym, 'colorizer'):
            if sym.colorizer.type != "RasterStretchColorizer":
                sym.updateColorizer("RasterStretchColorizer")
            sym.colorizer.stretchType = "MinimumMaximum"
            sym.colorizer.colorRamp = project.listColorRamps('Prediction')[0]
            tpi_raster.symbology = sym

        # save project
        log("saving project")
        project.save()

        return
