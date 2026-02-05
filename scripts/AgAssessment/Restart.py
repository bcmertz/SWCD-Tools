# --------------------------------------------------------------------------------
# Name:        Restart
# Purpose:     This tool allows you to clear out and restart an existing
#              run of the ag assessment tool.
#
# License:     GNU Affero General Public License v3.
#              Full license in LICENSE file, or at <https://www.gnu.org/licenses/>
# --------------------------------------------------------------------------------

import os
import json
import arcpy
import shutil

from ..helpers import license, reload_module, log, empty_workspace
from ..helpers import setup_environment as setup

class Restart(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Restart - clear out existing project info"
        self.description = "This tool allows the user to restart an ag assessment from scratch. Warning - This tool deletes the output folder, all feature classes in the workspace, and the cache of parcel numbers."
        self.category = "Automated Ag Assessment"
        self.canRunInBackground = False

    def getParameterInfo(self):
        """Define parameter definitions"""
        param0 = arcpy.Parameter(
            displayName="Delete ag assessment maps and layouts?",
            name="maps",
            datatype="GPBoolean",
            parameterType="Optional",
            direction="Input")

        param1 = arcpy.Parameter(
            displayName="Delete contents of output folder?",
            name="output_folder",
            datatype="GPBoolean",
            parameterType="Optional",
            direction="Input")

        param2 = arcpy.Parameter(
            displayName="Delete all feature feature classes in workspace: {}?".format(arcpy.env.workspace),
            name="workspace",
            datatype="GPBoolean",
            parameterType="Optional",
            direction="Input")

        params = [param0, param1, param2]
        return params

    def updateParameters(self, parameters):
        project = arcpy.mp.ArcGISProject("Current")
        project_dir = project.homeFolder
        cache_file_path = "{}/.ag_cache.json".format(project_dir)
        if not os.path.exists(cache_file_path):
            parameters[0].enabled = False
            parameters[0].value = False
            parameters[1].enabled = False
            parameters[1].value = False
        return

    def isLicensed(self):
        """Set whether the tool is licensed to execute."""
        return license()

    @reload_module(__name__)
    def execute(self, parameters, messages):
        """The source code of the tool."""
        # Setup
        log("setting up project")
        project, active_map = setup()
        project_dir = project.homeFolder
        cache_file_path = "{}/.ag_cache.json".format(project_dir)

        # Parameters
        log("reading in parameters")
        maps_bool = parameters[0].value
        folder_bool = parameters[1].value
        workspace_bool = parameters[2].value

        if maps_bool or folder_bool:
            # read in json
            log("reading in cache, will be deleted once maps and output folder are deleted")
            cache = {}
            try:
                with open(cache_file_path) as file:
                    cache = json.load(file)
                    parcels = cache["parcels"]
                output_folder = cache["output_folder"]
            except:
                log("Unable to find cache file and complete transaction. Please manually refresh the tool or manually clear out data.")

            # clear out maps, layouts, and feature classes
            if maps_bool:
                log("clearing out ag assessment maps and layouts")
                for parcel in parcels:
                    # find layout
                    lyt = None
                    try:
                        lyt = project.listLayouts(parcel)[0]
                    except:
                        log("couldn't find layout for parcel {}, results may be incomplete".format(parcel))
                        continue

                    # delete map
                    project.deleteItem(lyt)

                    # find map of parcel
                    m = None
                    try:
                        m = project.listMaps(parcel)[0]
                    except:
                        log("unable to find map for parcel {}, results may be incomplete".format(parcel))
                        continue

                    # delete map
                    project.deleteItem(m)

            if folder_bool:
                # clear out output folder
                log("clearing output folder")
                shutil.rmtree(output_folder)

            if not os.path.exists(output_folder) and maps_bool:
                # clear out cache
                log("clearing out cache file")
                os.remove(cache_file_path)

        if workspace_bool:
            # clear out feature classes from workspace
            log("clearing out feature classes from project workspace")
            empty_workspace(arcpy.env.workspace)

        # cleanup
        log("saving project")
        project.save()

        return
