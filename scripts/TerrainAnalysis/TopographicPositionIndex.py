# --------------------------------------------------------------------------------------------------
# Name:        Topographic Position Index (TPI)
# Purpose:     Calculates topographic position index for a raster and a given neighborhood size. This
#              allows versions of ArcGIS Pro earlier than 3.6 to calculate TPI.
#
# License:     Contextual Copyleft AI (CCAI) License v1.0.
#              Full license in LICENSE file.
# --------------------------------------------------------------------------------------------------

import arcpy

from ..helpers import license, reload_module, log, add_layer_to_group, convert_length, cell_length, convert_length
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
            displayName="Neighborhood Size",
            name="neighborhood",
            datatype="GPLinearUnit",
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
        return license()

    def updateParameters(self, parameters):
        # default focal width
        if parameters[2].value is None:
            parameters[2].value = "10 Feet"

        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool parameter."""
        validate(parameters)

        # check if neighborhood size is too small for given DEM
        if parameters[2].value and parameters[0].value:
            warning_message = "Neighborhood size is smaller than DEM cell size. This will lead to meaningless results."
            neighborhood = parameters[2].valueAsText
            dem_cell_size, dem_cell_unit = cell_length(parameters[0].value).split(" ")
            neighborhood_size = convert_length(neighborhood, dem_cell_unit).split(" ")[0]
            if neighborhood_size <= dem_cell_size:
                parameters[2].setWarningMessage(warning_message)
            else:
                if parameters[2].message == warning_message:
                    parameters[2].clearMessage()

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

        # convert neighborhood map units
        width = convert_length(neighborhood, active_map.mapUnits).split(" ")[0]
        height = width

        # calculate mean
        log("calculating mean elevations with {} cell".format(neighborhood))
        neighborhood = arcpy.sa.NbrRectangle(width, height, "MAP")
        log(neighborhood)
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
        diff.save(output_file)

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
