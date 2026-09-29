# --------------------------------------------------------------------------------
# Name:        Restart
# Purpose:     This tool allows you to clear out and restart an existing
#              run of the ag assessment tool.
#
# License:     Contextual Copyleft AI (CCAI) License v1.0.
#              Full license in LICENSE file.
# --------------------------------------------------------------------------------

import json
import os

import arcpy

from helpers.logging import log, warn
from helpers.tool import (
    empty_workspace,
    license,
    reload_module,
)
from helpers.tool import setup_environment as setup

from .DefineParcels import AG_ASSESSMENT_GDB_NAME


class Restart:
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Restart - clear out existing project info"
        self.description = "This tool allows the user to restart an ag assessment from scratch. Warning - This tool deletes permanently deletes maps, layouts, and workspace feature classes"
        self.category = "Automated Ag Assessment"

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
        cache_file_path = f"{project_dir}/.ag_cache.json"
        if not os.path.exists(cache_file_path):
            parameters[0].enabled = False
            parameters[0].value = False
        db_path = f"{project.homeFolder}\\{AG_ASSESSMENT_GDB_NAME}.gdb"
        if not arcpy.Exists(db_path):
            parameters[1].enabled = False
            parameters[1].value = False

    def isLicensed(self):
        """Set whether the tool is licensed to execute."""
        return license()

    @reload_module(__name__)
    def execute(self, parameters, _messages):
        """The source code of the tool."""
        # Setup
        log("setting up project")
        project, _active_map = setup()
        project_dir = project.homeFolder
        cache_file_path = f"{project_dir}/.ag_cache.json"

        # Parameters
        log("reading in parameters")
        maps_bool = parameters[0].value
        workspace_bool = parameters[1].value
        parcels = []

        if maps_bool:
            # read in json
            log("reading in cache - cache will be deleted once maps and layouts are deleted")
            try:
                with open(cache_file_path) as file:
                    cache = json.load(file)
                    parcels = cache["parcels"]
            except Exception:
                warn("Unable to find cache file and complete transaction. Please manually refresh the tool or manually clear out data.")
                return

            # clear out maps, layouts, and feature classes
            log("clearing out ag assessment maps and layouts")
            for parcel in parcels:
                # find layout
                try:
                    lyt = project.listLayouts(parcel)[0]
                except Exception:
                    warn(f"couldn't find layout for parcel {parcel}, results may be incomplete")
                    continue

                # delete map
                project.deleteItem(lyt)

                # find map of parcel
                try:
                    m = project.listMaps(parcel)[0]
                except Exception:
                    warn(f"unable to find map for parcel {parcel}, results may be incomplete")
                    continue

                # delete map
                project.deleteItem(m)

            # clear out cache
            log("clearing out parcel information cache")
            os.remove(cache_file_path)

        if workspace_bool:
            # check if project geodatabase exists
            db_path = f"{project.homeFolder}\\{AG_ASSESSMENT_GDB_NAME}.gdb"
            if arcpy.Exists(db_path):
                # clear out feature classes from workspace
                log("clearing out feature classes from project workspace")
                empty_workspace(db_path)
            else:
                log(f"project geodatabase {db_path} does not exist, nothing to delete")

        # cleanup
        log("saving project")
        project.save()

        return
