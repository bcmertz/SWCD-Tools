# --------------------------------------------------------------------------------------------------
# Name:        Topographic Position Index (TPI)
# Purpose:     Calculates topographic position index for a raster and a given neighborhood size. This
#              allows versions of ArcGIS Pro earlier than 3.6 to calculate TPI.
#
# License:     Contextual Copyleft AI (CCAI) License v1.0.
#              Full license in LICENSE file.
# --------------------------------------------------------------------------------------------------

import arcpy

from ..helpers import license, reload_module, log, add_layer_to_group, convert_length
from ..helpers import setup_environment as setup
from ..helpers import validate_spatial_reference as validate

class TopographicPositionIndex(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Topographic Position Index (TPI)"
        self.description = "TODO"
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
            displayName="Focal Width",
            name="focal_width",
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
        focal_width = parameters[2].valueAsText # TODO explain focal width should be larger than features trying to see
        # warn if focal_width is too big for dem cell size
        output_file = parameters[3].valueAsText

        # set analysis extent
        if extent:
            arcpy.env.extent = extent

        # convert focal_width map units
        width = convert_length(focal_width, active_map.mapUnits).split(" ")[0]
        height = width

        # calculate mean
        log("calculating mean elevations with {} cell".format(focal_width))
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
