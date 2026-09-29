# --------------------------------------------------------------------------------
# Name:        Sub-Basin Delineation
# Purpose:     This tool finds sub-basins within a given flow accumulation threshold
#              and defines their watersheds.
#
# License:     Contextual Copyleft AI (CCAI) License v1.0.
#              Full license in LICENSE file.
# --------------------------------------------------------------------------------

import arcpy

from helpers.logging import log, warn
from helpers.parameter import raster_and_layer
from helpers.parameter import validate_spatial_reference as validate
from helpers.rasters import cells_per_area
from helpers.tool import EXTENSIONS, license, reload_module
from helpers.tool import setup_environment as setup
from helpers.units import Area


class SubBasinDelineation:
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Sub-Basin Delineation"
        self.description = "Calculate hydrology for all sub-basins and perform stream routing"
        self.category = "Hydrology"

    def getParameterInfo(self):
        """Define parameter definitions"""
        param0 = arcpy.Parameter(
            displayName="DEM",
            name="dem",
            datatype="GPRasterLayer",
            parameterType="Required",
            direction="Input")

        param1 = arcpy.Parameter(
            displayName="Basin Shapefile",
            name="boundary",
            datatype="GPFeatureLayer",
            parameterType="Required",
            direction="Input")
        param1.filter.list = ["Polygon"]

        param2 = arcpy.Parameter(
            displayName="Stream Initiation Threshold",
            name="threshold",
            datatype="GPArealUnit",
            parameterType="Required",
            direction="Input")

        params = [param0, param1, param2]
        return params

    def updateParameters(self, parameters):
        # Default stream threshold value
        if parameters[2].value is None:
            parameters[2].value = "8 AcresUS"

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool parameter."""
        validate(parameters)

    def isLicensed(self):
        """Set whether the tool is licensed to execute."""
        return license([EXTENSIONS.Spatial])

    @reload_module(__name__)
    def execute(self, parameters, messages):
        """The source code of the tool."""
        # Setup
        log("setting up project")
        project, active_map = setup()

        # read in parameters
        dem, _ = raster_and_layer(parameters[0].value)
        watershed = parameters[1].value
        threshold = Area(parameters[2].valueAsText)

        # threshold in number of raster cells
        # assume 1m^2 cell, threshold ~8 acres in number of cells
        num_cells = 32000
        try:
            # find threshold in number of cells
            num_cells = cells_per_area(dem, threshold)
        except Exception:
            warn("failed to find raster linear unit, stream initiation threshold may be calculated incorrectly")

        # clip DEM raster to the watershed
        log("clipping raster to watershed")
        clip_raster_scratch = arcpy.sa.ExtractByMask(dem, watershed, "INSIDE")

        # fill raster
        log("filling raster")
        fill_raster_scratch = arcpy.sa.Fill(clip_raster_scratch)

        # flow direction
        log("calculating flow direction")
        flow_direction_scratch = arcpy.sa.FlowDirection(fill_raster_scratch)

        # flow accumulation
        log("calculating flow accumulation")
        flow_accumulation_scratch = arcpy.sa.FlowAccumulation(flow_direction_scratch)

        # con
        log("converting raster to stream network")
        sql_query = f"VALUE > {num_cells}"
        con_accumulation_scratch = arcpy.sa.Con(flow_accumulation_scratch, 1, "", sql_query)

        # stream link
        log("calculating stream links")
        stream_link = arcpy.sa.StreamLink(con_accumulation_scratch, flow_direction_scratch)

        # watershed
        log("calculating watershed")
        watershed = arcpy.sa.Watershed(flow_direction_scratch, stream_link)

        # stream to feature
        log("creating stream feature")
        stream_feature_path = f"{arcpy.env.workspace}\\stream_to_feature"
        stream_feature = arcpy.sa.StreamToFeature(con_accumulation_scratch, flow_direction_scratch, stream_feature_path, True)
        stream_feature = active_map.addDataFromPath(stream_feature)
        sym = stream_feature.symbology
        sym.renderer.symbol.color = {'RGB' : [0, 0, 0, 0]}
        sym.renderer.symbol.outlineColor = {'RGB' : [0, 112, 255, 100]}
        sym.renderer.symbol.size = 1.5
        stream_feature.symbology = sym

        # watershed raster to polyon
        log("converting watershed to polygon")
        watershed_polygon_path = f"{arcpy.env.workspace}\\watershed_polygon"
        watershed_polygon = arcpy.conversion.RasterToPolygon(watershed, watershed_polygon_path, create_multipart_features=True)
        watershed_polygon = active_map.addDataFromPath(watershed_polygon)
        sym = watershed_polygon.symbology
        sym.updateRenderer('UniqueValueRenderer')
        sym.renderer.fields = ['gridcode']
        watershed_polygon.symbology = sym
        watershed_polygon.visible = True

        # save and exit program successfully
        log("saving project")
        project.save()
