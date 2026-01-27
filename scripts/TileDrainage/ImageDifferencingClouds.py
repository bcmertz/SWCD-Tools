# --------------------------------------------------------------------------------------------------
# Name:        Image Differencing - Cloud and Shadow Removal
# Purpose:     This tool finds agricultural areas where short-wave infrared radiation reflectance
#              in dry and post-storm conditions are similar, indicating potential drainage tile.
#
# License:     GNU Affero General Public License v3.
#              Full license in LICENSE file, or at <https://www.gnu.org/licenses/>
# --------------------------------------------------------------------------------------------------

import arcpy

from ..helpers import license, reload_module, log, empty_workspace
from ..helpers import setup_environment as setup
from ..helpers import validate_spatial_reference as validate

class ImageDifferencingClouds(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Image Differencing - Cloud and Shadow Removal"
        self.description = "This tool removes potential tiled areas based off of a cloud/shadow mask create in the Image Differencing tool."
        self.category = "Hydrology\\Drainage Tile"
        self.canRunInBackground = False

    def getParameterInfo(self):
        """Define parameter definitions"""
        param0 = arcpy.Parameter(
            displayName="Potentially Tiled Fields",
            name="tile",
            datatype="GPFeatureLayer",
            parameterType="Required",
            direction="Input")

        param1 = arcpy.Parameter(
            displayName="Cloud and shadow masks",
            name="masks",
            datatype="GPFeatureLayer",
            multiValue=True,
            parameterType="Required",
           direction="Input")
        param1.filter.list = ["Polygon"]

        param2 = arcpy.Parameter(
            displayName="Output Features",
            name="out_features",
            datatype="DEFeatureClass",
            direction="Output")
        param2.parameterDependencies = [param0.name]
        param2.schema.clone = True

        params = [param0, param1, param2]
        return params

    def isLicensed(self):
        """Set whether the tool is licensed to execute."""
        return license(['Spatial'])

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
        tile = parameters[0].value.dataSource
        masks = parameters[1].valueAsText.replace("'","").split(";")
        output_file = parameters[2].valueAsText

        # create scratch layers
        scratch_union = arcpy.CreateScratchName("union", data_type="FeatureClass", workspace=arcpy.env.scratchGDB)
        scratch_erase = arcpy.CreateScratchName("erase", data_type="FeatureClass", workspace=arcpy.env.scratchGDB)

        log("erasing mask layers from tile layer")
        # combine mask layers into one layer
        arcpy.analysis.Union(
            in_features=masks,
            out_feature_class=scratch_union
        )

        # erase combined mask layer from potential tile layer
        arcpy.analysis.PairwiseErase(
            in_features=tile,
            erase_features=scratch_union,
            out_feature_class=scratch_erase,
            cluster_tolerance=None,
        )

        # dissolve polygon boundaries
        log("dissolving output polygon boundaries")
        arcpy.analysis.PairwiseDissolve(
            in_features=scratch_erase,
            out_feature_class=output_file,
            dissolve_field=None,
            statistics_fields=None,
            multi_part="SINGLE_PART",
        )

        # cleanup
        log("deleting unneeded data")
        empty_workspace(arcpy.env.scratchGDB, keep=[scratch_erase])

        # add output to map
        log("adding output to map")
        active_map.addDataFromPath(output_file)

        # save project
        log("saving project")
        project.save()

        return
