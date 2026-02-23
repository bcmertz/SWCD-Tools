# --------------------------------------------------------------------------------
# Name:        Remove Unused
# Purpose:     This tool deletes feature classes in a workspace not used in any maps
#
# Notes:       Inspired by https://github.com/alex6H/ArcGIS_Toolbox/blob/main/Tools/unused_feature_class_finder.py
#
# License:     GNU Affero General Public License v3.
#              Full license in LICENSE file, or at <https://www.gnu.org/licenses/>
#
#              Unclear what license this tool should fall under. Assumed AGPL v3
#              due to no code being taken from alex6H just inspiration, but to be
#              safe this tool shouldn't be used for commercial purposes to comply
#              with the original tool's CC-SA-NA license. TODO: figure out if this is true
# --------------------------------------------------------------------------------

import arcpy
import os

from ..helpers import license, reload_module, log
from ..helpers import setup_environment as setup
from ..helpers import validate_spatial_reference as validate

class RemoveUnused(object):
    project = arcpy.mp.ArcGISProject("Current")

    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Remove Unused"
        self.description = "This tool deletes feature classes in a workspace not used in any maps"
        self.category = "Utilities"
        self.canRunInBackground = False

    def getParameterInfo(self):
        """Define parameter definitions"""

        # workspace
        param0 = arcpy.Parameter(
            displayName="Workspace",
            name="workspace",
            datatype="DEWorkspace",
            parameterType="Required",
            direction="Input")

        # unused
        param1 = arcpy.Parameter(
            displayName="Unused data in workspace to delete",
            name="unused",
            datatype="GPString",
            parameterType="Required",
            multiValue="True",
            direction="Input")
        param1.filter.type = "ValueList"
        param1.filter.list = []

        params = [param0, param1]
        return params

    def updateParameters(self, parameters):
        # find unused
        if not parameters[0].hasBeenValidated:
            if parameters[0].value:
                workspace = parameters[0].value
                options = set()

                # get all filepaths from workspace
                for dirpath, dirnames, filenames in arcpy.da.Walk(workspace):
                    for filename in filenames:
                        fc = os.path.join(dirpath, filename)
                        options.add(fc)

                # remove all used filepaths
                maps = self.project.listMaps()
                for m in maps:
                    options = options - set(l.dataSource for l in m.listLayers() if l.supports("DATASOURCE"))

                parameters[1].filter.list = list(options)
            else:
                parameters[1].value = None
                parameters[1].filter.list = []

        return

    def isLicensed(self):
        """Set whether the tool is licensed to execute."""
        return license()

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
        unused = parameters[1].valueAsText.replace("'","").split(";")

        log("deleting unused data")
        for fc in unused:
            arcpy.management.Delete(fc)

        # save and exit program successfully
        log("saving project")
        project.save()

        return
