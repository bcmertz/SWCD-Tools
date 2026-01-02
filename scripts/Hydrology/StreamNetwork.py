# --------------------------------------------------------------------------------
# Name:        Stream Network
# Purpose:     This tool creates a stream network from a DEM, clipped to the extent
#              of a supplied stream layer
#
# License:     GNU Affero General Public License v3.
#              Full license in LICENSE file, or at <https://www.gnu.org/licenses/>
# --------------------------------------------------------------------------------

import arcpy

from helpers import license, get_oid, convert_units, get_linear_unit
from helpers import print_messages as log
from helpers import setup_environment as setup
from helpers import validate_spatial_reference as validate

class StreamNetwork(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Calculate Stream Network"
        self.description = "Create stream network from DEM"
        self.category = "Hydrology"
        self.canRunInBackground = False

    def getParameterInfo(self):
        """Define parameter definitions"""
        param0 = arcpy.Parameter(
            displayName="Hydro-Conditioned DEM",
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

        # NOTE: composite parameters not supported until ArcGIS Pro 3.4
        # once supported consider combining threshold and stream lines
        # into one parameter with a toggle
        param2 = arcpy.Parameter(
            displayName="Stream Initiation Threshold (acres)",
            name="threshold",
            datatype="GPDouble",
            parameterType="Required",
            direction="Input")

        param3 = arcpy.Parameter(
            displayName="Existing Stream Lines",
            name="stream",
            datatype="GPFeatureLayer",
            parameterType="Optional",
            direction="Input")
        param3.filter.list = ["Line"]
        param3.controlCLSID = '{60061247-BCA8-473E-A7AF-A2026DDE1C2D}' # allows line creation

        param4 = arcpy.Parameter(
            displayName="Output Features",
            name="out_features",
            datatype="DEFeatureClass",
            parameterType="Required",
            direction="Output")
        param4.parameterDependencies = [param0.name]
        param4.schema.clone = True

        params = [param0, param1, param2, param3, param4]
        return params

    def updateParameters(self, parameters):
        # Default stream threshold value
        if parameters[2].value == None:
            parameters[2].value = 8

        return

    def isLicensed(self):
        """Set whether the tool is licensed to execute."""
        return license(['Spatial'])

    def updateMessages(self, parameters):
        "Modify the messages created by internal validation for each tool parameter."""
        validate(parameters)
        return

    def execute(self, parameters, messages):
        """The source code of the tool."""
        # Setup
        log("setting up project")
        project, active_map = setup()

        # read in parameters
        dem = parameters[0].value
        extent = parameters[1].value
        theshold = parameters[2].value
        stream = parameters[3].value
        output_file = parameters[4].valueAsText

        # set analysis extent
        if extent:
            arcpy.env.extent = extent

        # find threshold in # cells
        linear_unit = get_linear_unit(dem)
        try:
            desc = arcpy.Describe(dem)
            cellsize_y = convert_units(desc.meanCellHeight, linear_unit, "FOOT")  # Cell size in the Y axis
            cellsize_x = convert_units(desc.meanCellWidth, linear_unit, "FOOT")   # Cell size in the X axis
            if linear_unit == None:
                log("unknown linear unit for DEM, stream initiation theshold may be calculated incorrectly")
            cell_area_ft2 = cellsize_x * cellsize_y
            threshold = int(theshold * (43560 / cell_area_ft2))
        except:
            log("failed to find raster linear unit, stream initiation threshold may be calculated incorrectly")
            threshold = 32000 # default to 1m^2 cell, threshold ~8 acres

        # create scratch layers
        log("creating scratch layers")
        scratch_streamlines = arcpy.CreateScratchName("scratch_streamlines", data_type="FeatureClass", workspace=arcpy.env.scratchFolder)
        scratch_end_points = arcpy.CreateScratchName("end_pts", data_type="FeatureClass", workspace=arcpy.env.scratchFolder)

        # fill DEM
        log("filling raster")
        fill_raster = arcpy.sa.Fill(dem)

        # flow direction
        log("calculating flow direction")
        flow_direction = arcpy.sa.FlowDirection(fill_raster)

        # flow accumulation
        log("calculating flow accumulation")
        flow_accumulation = arcpy.sa.FlowAccumulation(flow_direction)
        
        # con
        log("converting raster to stream network")
        sql_query = "VALUE > {}".format(threshold)
        con_accumulation = arcpy.sa.Con(flow_accumulation, 1, "", sql_query)

        if stream:
            # stream to feature
            log("creating stream feature")
            stream_feature = arcpy.sa.StreamToFeature(con_accumulation, flow_direction, scratch_streamlines, True)

            # get end points of existing lines
            log("finding existing streamline endpoints")
            arcpy.management.FeatureVerticesToPoints(stream, scratch_end_points, point_location="DANGLE")

            # get stream initiation point
            # choose max value, if beyond it the point doesn't snap which is usually fine if there's not a watershed divide in between
            log("snap existing stream initiation points to flow accumulation model")
            stream_initiations = arcpy.edit.Snap(scratch_end_points, snap_environment=[[scratch_streamlines, "EDGE", "200 Feet"]]) # TODO: choose reasonable distance to look for initiation points

            # find flow path: optimal path as raster
            log("tracing downstream from stream initiation points")
            out_path_accumulation_raster = arcpy.sa.OptimalPathAsRaster(
                in_destination_data=stream_initiations,
                in_distance_accumulation_raster=flow_accumulation,
                in_back_direction_raster=flow_direction,
                destination_field=get_oid(stream_initiations)
            )

            # stream to feature
            log("converting stream raster to output feature class")
            arcpy.sa.StreamToFeature(out_path_accumulation_raster, flow_direction, output_file, True)
        else:
            # stream to feature
            log("creating stream feature")
            arcpy.sa.StreamToFeature(con_accumulation, flow_direction, output_file, True)
                                             
        # add flow path polyline to map
        log("adding output to map")
        active_map.addDataFromPath(output_file)

        # save and exit program successfully
        log("saving project")
        project.save()

        # remove temporary variables
        log("cleaning up")
        arcpy.management.Delete([scratch_end_points, scratch_streamlines])

        return
