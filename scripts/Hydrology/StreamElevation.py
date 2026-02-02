# ------------------------------------------------------------------------------------------
# Name:        Stream Elevation
# Purpose:     This tool collects elevation data along a drainage network for visualization.
#
# License:     GNU Affero General Public License v3.
#              Full license in LICENSE file, or at <https://www.gnu.org/licenses/>
# -------------------------------------------------------------------------------------------

import os
import arcpy

from ..helpers import license, empty_workspace, reload_module, log, get_linear_unit
from ..helpers import setup_environment as setup
from ..helpers import validate_spatial_reference as validate

class StreamElevation(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Stream Elevation Profile"
        self.description = "Create profile of the stream throughout it's length"
        self.category = "Hydrology"
        self.canRunInBackground = False

    def getParameterInfo(self):
        """Define parameter definitions"""
        param0 = arcpy.Parameter(
            displayName="Stream Feature",
            name="stream",
            datatype="GPFeatureLayer",
            parameterType="Required",
            direction="Input")
        param0.filter.list = ["Line"]
        param0.controlCLSID = '{60061247-BCA8-473E-A7AF-A2026DDE1C2D}' # allows line creation

        param1 = arcpy.Parameter(
            displayName="from_node field",
            name="from",
            datatype="GPString",
            parameterType="Required",
            direction="Input")
        param1.filter.type = "ValueList"
        param1.filter.list = []

        param2 = arcpy.Parameter(
            displayName="to_node field",
            name="to",
            datatype="GPString",
            parameterType="Required",
            direction="Input")
        param2.filter.type = "ValueList"
        param2.filter.list = []

        param3 = arcpy.Parameter(
            displayName="Fields to keep",
            name="keep",
            datatype="GPString",
            parameterType="Optional",
            multiValue="True",
            direction="Input")
        param3.filter.type = "ValueList"
        param3.filter.list = []

        param4 = arcpy.Parameter(
            displayName="DEM",
            name="dem",
            datatype="GPRasterLayer",
            parameterType="Required",
            direction="Input")

        param5 = arcpy.Parameter(
            displayName="Watershed",
            name="analysis_area",
            datatype="GPFeatureLayer",
            parameterType="Optional",
            direction="Input")
        param5.controlCLSID = '{60061247-BCA8-473E-A7AF-A2026DDE1C2D}' # allows polygon creation

        param6 = arcpy.Parameter(
            displayName="Point Spacing",
            name="point_spacing",
            datatype="GPLinearUnit",
            parameterType="Required",
            direction="Input")

        param7 = arcpy.Parameter(
            displayName="Output Table",
            name="out_table",
            datatype="DEFile",
            parameterType="Required",
            direction="Output")
        param7.filter.list = ['csv']

        params = [param0, param1, param2, param3, param4, param5, param6, param7]
        return params

    def updateParameters(self, parameters):
        # get stream line fields
        if not parameters[0].hasBeenValidated:
            if parameters[0].value:
                parameters[1].enabled = True
                parameters[2].enabled = True
                parameters[3].enabled = True
                fields = [f.name for f in arcpy.ListFields(parameters[0].value)]
                parameters[1].filter.list = fields
                parameters[2].filter.list = fields
                parameters[3].filter.list = fields
                if "from_node" in fields:
                    parameters[1].value = "from_node"
                if "to_node" in fields:
                    parameters[2].value = "to_node"
            else:
                parameters[1].enabled = False
                parameters[1].value = None
                parameters[2].enabled = False
                parameters[2].value = None
                parameters[3].enabled = False
                parameters[3].value = None

        # default point spacing
        if parameters[6].value is None:
            parameters[6].value = "50 FeetUS"
        return

    def isLicensed(self):
        """Set whether the tool is licensed to execute."""
        return license(['Foundation', 'Spatial'])

    def updateMessages(self, parameters):
        "Modify the messages created by internal validation for each tool parameter."""
        validate(parameters)
        return

    @reload_module(__name__)
    def execute(self, parameters, messages):
        """The source code of the tool."""
        # Setup
        log("setting up project")
        project, active_map = setup()

        # read in parameters
        streams = parameters[0].value
        from_node = parameters[1].value
        to_node = parameters[2].value
        keep_fields = parameters[3].valueAsText.split(";") if parameters[3].value else []
        dem = parameters[4].value
        watershed = parameters[5].value
        linear_unit = get_linear_unit(streams)
        point_spacing = parameters[6].valueAsText
        point_spacing_unit = point_spacing.split(" ")[1]
        output_file = parameters[7].valueAsText

        # create scratch layers
        log("creating scratch layers")
        scratch_streams = arcpy.CreateScratchName("streams", "FeatureClass", arcpy.env.scratchGDB)
        scratch_nodes = arcpy.CreateScratchName("nodes", "FeatureClass", arcpy.env.scratchGDB)
        scratch_points = arcpy.CreateScratchName("points", "FeatureClass", arcpy.env.scratchGDB)
        scratch_points_elev = arcpy.CreateScratchName("points_elev", "FeatureClass", arcpy.env.scratchGDB)

        # copy streamlines to a scratch feature to avoid altering the input lines
        # TODO: fix clip
        log("setting watershed boundaries")
        if watershed:
            arcpy.analysis.Clip(streams, watershed, scratch_streams)
        else:
            arcpy.management.CopyFeatures(streams, scratch_streams)

        # set line and segment direction
        #
        # use reverse direction since we accumulate downstream length
        log("setting topographic drainage directions")
        arcpy.topographic.SetLineDirection(scratch_streams, dem, line_direction="DOWNHILL", reverse_direction="REVERSE_DIRECTION")

        # calculate geometry lengths
        log("calculate segment lengths")
        field_name = "length"
        if field_name not in [f.name for f in arcpy.ListFields(scratch_streams)]:
            arcpy.management.AddField(scratch_streams, field_name, "DOUBLE")
        arcpy.management.CalculateGeometryAttributes(
            in_features=scratch_streams,
            geometry_property=[[field_name, "LENGTH_GEODESIC"]],
            length_unit="FEET_US",
            coordinate_format="SAME_AS_INPUT"
        )

        # construct DAG in reverse order - looking downstream to upstream
        # dag: {
        #     from_node: {
        #                    to_nodes: {
        #                        ID: length_to_node,
        #                    }
        #                    total_length: #
        #                }
        # }
        log("finding segment end points")
        arcpy.management.FeatureVerticesToPoints(
            in_features=scratch_streams,
            out_feature_class=scratch_nodes,
            point_location="END"
        )
        log("constructing directed acyclic graph")
        dag = {}
        to_nodes = set()
        from_nodes = set()
        with arcpy.da.SearchCursor(scratch_nodes, ["from_node", "to_node", "length"]) as cursor:
            for row in cursor:
                to_node = row[0]    # reversed since our dag "flows" upstream
                from_node = row[1]  # reversed since out dag "flows" upstream
                length = row[2]
                to_nodes.add(to_node)
                from_nodes.add(from_node)
                if from_node in dag:
                    dag[from_node]["to_nodes"][to_node] = length
                else:
                    dag[from_node] = {
                        "to_nodes": {to_node: length},
                        "downstream_length": 0,
                    }

        # find end nodes (furthest downstream) and start nodes (headwaters)
        log("finding start and end nodes")
        end_nodes = list(from_nodes - to_nodes)

        # for each end node, add downstream length info to all upstream nodes
        log("calculating accumulated segment lengths")
        def process_lengths(end_node_id, downstream_length):
            """Recursively traverse DAG and find all downstream lengths."""
            node = dag[end_node_id]
            to_nodes = node["to_nodes"]
            node["downstream_length"] = downstream_length
            for to_node in to_nodes:
                if to_node in dag:
                    length = to_nodes[to_node]
                    downstream_length = downstream_length + length
                    return process_lengths(to_node, downstream_length)
                else:
                    return
        for end_node in end_nodes:
            process_lengths(end_node_id=end_node, downstream_length=0)

        # generate points along line
        log("generate data points along lines")
        arcpy.management.GeneratePointsAlongLines(scratch_streams, scratch_points, "DISTANCE", point_spacing, Include_End_Points="END_POINTS", Add_Chainage_Fields="ADD_CHAINAGE")

        # extract values to points
        log("extract elevations at data points")
        arcpy.sa.ExtractValuesToPoints(scratch_points, dem, scratch_points_elev)

        # update lengths to include upstream length
        log("add downstream length to data points")
        with arcpy.da.UpdateCursor(scratch_points_elev, ["ORIG_LEN", "to_node"]) as cursor:
            for row in cursor:
                orig_len = row[0] * arcpy.LinearUnitConversionFactor(linear_unit, point_spacing_unit)
                to_node = row[1]
                row[0] = orig_len + dag[to_node]["downstream_length"]
                cursor.updateRow(row)

        # delete unnecessary fields
        log("deleting unnecessary fields")
        keep_fields = keep_fields + ["ORIG_LEN", "RASTERVALU"]
        arcpy.management.DeleteField(scratch_points_elev, keep_fields, method="KEEP_FIELDS")

        # export table to csv
        log("exporting elevation data to table")
        arcpy.conversion.ExportTable(scratch_points_elev, output_file)

        # open coordinates folder
        log("opening folder")
        os.startfile(output_file)

        # cleanup
        log("deleting unneeded data")
        empty_workspace(arcpy.env.scratchGDB, keep=[])

        # save and exit program successfully
        log("saving project")
        project.save()

        return
