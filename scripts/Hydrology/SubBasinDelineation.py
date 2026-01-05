# --------------------------------------------------------------------------------
# Name:        Sub-Basin Delineation
# Purpose:     This tool finds sub-basins within a given flow accumulation threshold
#              and defines their watersheds.
#
# License:     GNU Affero General Public License v3.
#              Full license in LICENSE file, or at <https://www.gnu.org/licenses/>
# --------------------------------------------------------------------------------

import arcpy

from helpers import license, empty_workspace
from helpers import print_messages as log
from helpers import setup_environment as setup
from helpers import validate_spatial_reference as validate

class SubBasinDelineation(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Sub-Basin Delineation"
        self.description = "Calculate hydrology for all sub-basins and perform stream routing"
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
            displayName="Basin Shapefile",
            name="boundary",
            datatype="GPFeatureLayer",
            parameterType="Required",
            direction="Input")
        param1.filter.list = ["Polygon"]

        param2 = arcpy.Parameter(
            displayName="Stream Threshold Value",
            name="threshold",
            datatype="GPDouble",
            parameterType="Optional",
            direction="Input")

        params = [param0, param1, param2]
        return params

    def updateParameters(self, parameters):
        # Default stream threshold value
        if parameters[2].value == None:
            parameters[2].value = 25000
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool parameter."""
        validate(parameters)
        return

    def isLicensed(self):
        """Set whether the tool is licensed to execute."""
        return license()

    def execute(self, parameters, messages):
        """The source code of the tool."""
        # Setup
        log("setting up project")
        project, active_map = setup()

        # read in parameters
        raster_layer = parameters[0].value
        watershed = parameters[1].value
        con_threshold = parameters[2].value if parameters[2].value else 25000

        # create scratch layers
        clip_raster_scratch = arcpy.CreateScratchName("temp", data_type="RasterDataset", workspace=arcpy.env.scratchGDB)
        fill_raster_scratch = arcpy.CreateScratchName("temp", data_type="RasterDataset", workspace=arcpy.env.scratchGDB)
        flow_direction_scratch = arcpy.CreateScratchName("temp", data_type="RasterDataset", workspace=arcpy.env.scratchGDB)
        flow_accumulation_scratch = arcpy.CreateScratchName("temp", data_type="RasterDataset", workspace=arcpy.env.scratchGDB)
        con_accumulation_scratch = arcpy.CreateScratchName("temp", data_type="RasterDataset", workspace=arcpy.env.scratchGDB)

        # clip DEM raster to the watershed
        log("clipping raster to watershed")
        arcpy.management.Clip(raster_layer, "", clip_raster_scratch, watershed, "#", "ClippingGeometry")

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
        sql_query = "VALUE > {}".format(con_threshold)
        con_accumulation_scratch = arcpy.sa.Con(flow_accumulation_scratch, 1, "", sql_query)

        # stream link
        log("calculating stream links")
        stream_link = arcpy.sa.StreamLink(con_accumulation_scratch, flow_direction_scratch)

        # watershed
        log("calculating watershed")
        watershed = arcpy.sa.Watershed(flow_direction_scratch, stream_link)

        # stream to feature
        log("craeting stream feature")
        stream_feature_path = "{}\\stream_to_feature".format(arcpy.env.workspace)
        stream_feature = arcpy.sa.StreamToFeature(con_accumulation_scratch, flow_direction_scratch, stream_feature_path, True)
        stream_feature = active_map.addDataFromPath(stream_feature)
        sym = stream_feature.symbology
        sym.renderer.symbol.color = {'RGB' : [0, 0, 0, 0]}
        sym.renderer.symbol.outlineColor = {'RGB' : [0, 112, 255, 100]}
        sym.renderer.symbol.size = 1.5
        stream_feature.symbology = sym

        # watershed raster to polyon
        log("converting watershed to polygon")
        watershed_polygon_path = "{}\\watershed_polygon".format(arcpy.env.workspace)
        watershed_polygon = arcpy.conversion.RasterToPolygon(watershed, watershed_polygon_path, create_multipart_features=True)
        watershed_polygon = active_map.addDataFromPath(watershed_polygon)
        sym = watershed_polygon.symbology
        sym.updateRenderer('UniqueValueRenderer')
        sym.renderer.fields = ['gridcode']
        watershed_polygon.symbology = sym
        watershed_polygon.visible = True

        # cleanup
        log("deleting unneeded data")
        empty_workspace(arcpy.env.scratchGDB, keep=[])

        return
