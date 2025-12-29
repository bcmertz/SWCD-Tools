# --------------------------------------------------------------------------------
# Name:        Calculate Streamline
# Purpose:     This tool uses flow accumulation to define stream lines from a DEM.
#
# License:     GNU Affero General Public License v3.
#              Full license in LICENSE file, or at <https://www.gnu.org/licenses/>
# --------------------------------------------------------------------------------

import arcpy

from helpers import license
from helpers import print_messages as log
from helpers import setup_environment as setup
from helpers import validate_spatial_reference as validate

class CalculateStreamline(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Calculate Streamline"
        self.description = "Calculate streamlines for a given watershed"
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

    def updateParameters(self, parameters):
        # Default stream threshold value
        if parameters[2].value == None:
            parameters[2].value = 25000
        return

    def execute(self, parameters, messages):
        """The source code of the tool."""
        # Setup
        log("setting up project")
        project, active_map = setup()

        # read in parameters
        raster_layer = parameters[0].value
        watershed_polygon = parameters[1].value
        accumulation_threshold = parameters[2].value
        stream_feature_path = parameters[3].value

        # create scratch layers
        log("creating scratch layers")
        scratch_dem = "{}\\dem_raster_clip".format(arcpy.env.workspace)
        fill_raster_scratch = arcpy.CreateScratchName("temp", data_type="RasterDataset", workspace=arcpy.env.scratchFolder)
        flow_direction_scratch = arcpy.CreateScratchName("temp", data_type="RasterDataset", workspace=arcpy.env.scratchFolder)
        flow_accumulation_scratch = arcpy.CreateScratchName("temp", data_type="RasterDataset", workspace=arcpy.env.scratchFolder)
        #clip_flow_accumulation_scratch = "{}\\flow_accumulation_clip".format(arcpy.env.workspace)
        clip_flow_accumulation_scratch = arcpy.CreateScratchName("temp", data_type="RasterDataset", workspace=arcpy.env.scratchFolder)
        con_accumulation_scratch = arcpy.CreateScratchName("temp", data_type="RasterDataset", workspace=arcpy.env.scratchFolder)

        if parameters[1].value:
            # clip DEM raster to the study area
            log("clipping raster to analysis area")
            arcpy.management.Clip(raster_layer, watershed_polygon, scratch_dem)
            raster_layer = scratch_dem

        # fill raster
        log("filling raster")
        fill_raster_scratch = arcpy.sa.Fill(raster_layer)

        # flow direction
        log("calculating flow direction")
        flow_direction_scratch = arcpy.sa.FlowDirection(fill_raster_scratch)

        # flow accumulation
        log("calculating flow accumulation")
        flow_accumulation_scratch = arcpy.sa.FlowAccumulation(flow_direction_scratch)

        # clip flow accumulation
        log("clipping flow accumulation raster to watershed shape")
        arcpy.management.Clip(flow_accumulation_scratch, "", clip_flow_accumulation_scratch, watershed_polygon, "#", "ClippingGeometry")

        # con
        log("converting raster to stream network")
        sql_query = "VALUE > {}".format(accumulation_threshold)
        con_accumulation_scratch = arcpy.sa.Con(clip_flow_accumulation_scratch, 1, "", sql_query)

        # stream to feature
        log("creating stream feature")
        stream_feature = arcpy.sa.StreamToFeature(con_accumulation_scratch, flow_direction_scratch, stream_feature_path, True)
        stream_feature = active_map.addDataFromPath(stream_feature)
        sym = stream_feature.symbology
        sym.renderer.symbol.color = {'RGB' : [0, 0, 0, 0]}
        sym.renderer.symbol.outlineColor = {'RGB' : [0, 112, 255, 100]}
        sym.renderer.symbol.size = 1.5
        stream_feature.symbology = sym

        # save and exit program successfully
        log("saving project")
        project.save()

        # remove temporary variables
        log("cleaning up")
        arcpy.management.Delete([scratch_dem, fill_raster_scratch, flow_direction_scratch, flow_accumulation_scratch, clip_flow_accumulation_scratch, con_accumulation_scratch])

        return
