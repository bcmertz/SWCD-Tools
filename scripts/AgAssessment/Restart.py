# --------------------------------------------------------------------------------
# Name:        Restart
# Purpose:     This tool allows you to clear out and restart an existing
#              run of the ag assessment tool.
#
# License:     Contextual Copyleft AI (CCAI) License v1.0.
#              Full license in LICENSE file.
# --------------------------------------------------------------------------------

import os
import json
import arcpy
import shutil

from .DefineParcels import AG_ASSESSMENT_GDB_NAME
from ..helpers import license, reload_module, log, empty_workspace
from ..helpers import setup_environment as setup

class Restart(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Restart - clear out existing project info"
        self.description = "This tool allows the user to restart an ag assessment from scratch. Warning - This tool deletes permanently deletes maps, layouts, and workspace feature classes"
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
            displayName="Delete all feature feature classes in ag assessment workspace?",
            name="workspace",
            datatype="GPBoolean",
            parameterType="Optional",
            direction="Input")

        params = [param0, param1]
        return params

    def updateParameters(self, parameters):
        project = arcpy.mp.ArcGISProject("Current")
        project_dir = project.homeFolder
        cache_file_path = "{}/.ag_cache.json".format(project_dir)
        if not os.path.exists(cache_file_path):
            parameters[0].enabled = False
            parameters[0].value = False
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
        workspace_bool = parameters[1].value
        parcels = []
        output_folder = None

        if maps_bool:
            # read in json
            log("reading in cache, will be deleted once maps and layouts are deleted")
            cache = {}
            try:
                with open(cache_file_path) as file:
                    cache = json.load(file)
                    parcels = cache["parcels"]
                    output_folder = cache["output_folder"]
            except:
                log("Unable to find cache file and complete transaction. Please manually refresh the tool or manually clear out data.")
                return

            # clear out maps, layouts, and feature classes
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

            # clear out cache
            log("clearing out parcel information cache")
            os.remove(cache_file_path)

        if workspace_bool:
            # check if project geodatabase exists
            db_path = "{}\\{}.gdb".format(project.homeFolder, AG_ASSESSMENT_GDB_NAME)
            if arcpy.Exists(db_path):
                # clear out feature classes from workspace
                log("clearing out feature classes from project workspace")
                empty_workspace(db_path)
            else:
                log("project geodatabase {} does not exist".format(db_path))

        # cleanup
        log("saving project")
        project.save()

        return
