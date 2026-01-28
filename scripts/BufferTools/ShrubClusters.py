# --------------------------------------------------------------------------------
# Name:        Shrub Clusters
# Purpose:     This tool creates shrub cluster polygons in a planting area for a
#              given number of clusters and cluster size
#
# License:     GNU Affero General Public License v3.
#              Full license in LICENSE file, or at <https://www.gnu.org/licenses/>
# --------------------------------------------------------------------------------

import math
import arcpy

from ..helpers import license, empty_workspace, reload_module, log
from ..helpers import setup_environment as setup
from ..helpers import validate_spatial_reference as validate

class ShrubClusters:
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Shrub Cluster Tool"
        self.description = "Shrub Clusters"
        self.category = "Buffer tools"
        self.canRunInBackground = False

    def getParameterInfo(self):
        """Define the tool parameters."""
        param0 = arcpy.Parameter(
            displayName="Analysis Area",
            name="polygon",
            datatype="GPFeatureLayer",
            parameterType="Required",
            direction="Input")
        param0.filter.list = ["Polygon"]
        param0.controlCLSID = '{60061247-BCA8-473E-A7AF-A2026DDE1C2D}' # allows polygon creation

        param1 = arcpy.Parameter(
            displayName="Output Features",
            name="out_features",
            datatype="DEFeatureClass",
            parameterType="Required",
            direction="Output")
        param1.parameterDependencies = [param0.name]

        param2 = arcpy.Parameter(
            displayName="Cluster Width",
            name="width",
            datatype="GPLinearUnit",
            parameterType="Required",
            direction="Input")

        param3 = arcpy.Parameter(
            displayName="Number of clusters",
            name="number",
            datatype="GPDouble",
            parameterType="Required",
            direction="Input")

        param4 = arcpy.Parameter(
            displayName="Cluster Shape",
            name="shape",
            datatype="GPString",
            parameterType="Required",
            direction="Input")
        param4.filter.type = "ValueList"
        param4.filter.list = ["Square", "Circle"]

        params = [param0, param1, param2, param3, param4]
        return params

    def isLicensed(self):
        """Set whether the tool is licensed to execute."""
        return license()

    def updateParameters(self, parameters):
        # set default cluster shape
        if parameters[4].value is None:
            parameters[4].value = "Square"

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

        log("reading in parameters")
        area = parameters[0].value
        output_file = parameters[1].valueAsText
        width, width_unit = parameters[2].valueAsText.split(" ")
        width = float(width) / 2

        number = parameters[3].value
        geom_type = "CIRCLE" if parameters[4].valueAsText == "Circle" else "ENVELOPE"

        # create scratch layers
        log("creating scratch layers")
        scratch_area = arcpy.CreateScratchName("scratch_area", data_type="DEFeatureClass", workspace=arcpy.env.scratchGDB)
        scratch_points = arcpy.CreateScratchName("scratch_points", data_type="DEFeatureClass", workspace=arcpy.env.scratchGDB)
        scratch_buffer = arcpy.CreateScratchName("scratch_buffer", data_type="DEFeatureClass", workspace=arcpy.env.scratchGDB)

        # create buffer inside the planting area
        log("buffer output area")
        buffer_width = -width
        if geom_type == "ENVELOPE":
            buffer_width = buffer_width*math.sqrt(2)
        arcpy.analysis.PairwiseBuffer(area, scratch_area, "{} {}".format(buffer_width, width_unit))

        # create point locations
        log("creating shrub cluster point locations")
        arcpy.management.CreateSpatialSamplingLocations(
            in_study_area=scratch_area,
            out_features=scratch_points,
            sampling_method="SYSTEMATIC",
            bin_shape="HEXAGON",
            bin_size=number,
            geometry_type="POINT",
            spatial_relationship="HAVE_THEIR_CENTER_IN"
        )

        # buffer points by width
        log("creating buffer around shrub cluster points")
        arcpy.analysis.Buffer(
            in_features=scratch_points,
            out_feature_class=scratch_buffer,
            buffer_distance_or_field="{} {}".format(width, width_unit),
        )

        # make square around buffer
        log("creating {} {} shrub clusters".format(int(number), parameters[4].valueAsText.lower()))
        arcpy.management.MinimumBoundingGeometry(
            in_features=scratch_buffer,
            out_feature_class=output_file,
            geometry_type=geom_type,
            group_option="NONE",
            group_field=None,
            mbg_fields_option="NO_MBG_FIELDS"
        )

        # cleanup
        log("deleting unneeded data")
        empty_workspace(arcpy.env.scratchGDB, keep=[])

        # save
        log("saving project")
        project.save()

        return
