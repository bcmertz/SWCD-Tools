# --------------------------------------------------------------------------------
# Name:        Agland
# Purpose:     This tool categorizes a piece of land in an ag assessment as
#              agricultural land for further processing
#
# License:     Contextual Copyleft AI (CCAI) License v1.0.
#              Full license in LICENSE file.
# --------------------------------------------------------------------------------

import json

import arcpy
from helpers.logging import error, log, warn
from helpers.parameter import validate_spatial_reference as validate
from helpers.tool import (
    license,
    reload_module,
)
from helpers.tool import setup_environment as setup

from .DefineParcels import AG_ASSESSMENT_GDB_NAME


class Agland:
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "2a. Delineate Agland"
        self.category = "Automated Ag Assessment"
        self.description = "Select all agland for delineation"

    def getParameterInfo(self):
        """Define parameter definitions"""
        params = []
        return params

    def isLicensed(self):
        """Set whether the tool is licensed to execute."""
        return license()

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool parameter."""
        validate(parameters)

    @reload_module(__name__)
    def execute(self, parameters, messages):
        """The source code of the tool."""
        # Setup
        log("setting up project")
        project, active_map = setup()
        project_dir = project.homeFolder
        cache_file_path = f"{project_dir}/.ag_cache.json"

        # check for geodatabase and set it as workspace
        db_path = f"{project.homeFolder}\\{AG_ASSESSMENT_GDB_NAME}.gdb"
        if not arcpy.Exists(db_path):
            error(f"Ag assessment geodatase {db_path} does not exist. Please start over with step 1.")
        arcpy.env.workspace = db_path

        # read in json
        log("reading in cache")
        cache = {}
        with open(cache_file_path) as file:
            cache = json.load(file)
        parcels = cache["parcels"]

        log("iterating through parcels and delineated agland")
        for parcel in parcels:
            # find map of parcel
            m = None
            try:
                m = project.listMaps(parcel)[0]
            except Exception:
                warn(f"unable to find map for {parcel}, results may be incomplete")
                continue

            # get parcel layer or drop off of map
            parcel_lyr = None
            try:
                parcel_lyr = m.listLayers(f"*_{parcel}")[0]
            except Exception:
                warn(f"no appropriate parcel layer found for {parcel}, results may be incomplete")
                continue

            # check how many pieces are selected
            sel_set = parcel_lyr.getSelectionSet()
            if sel_set is None:
                continue

            # construct layer name and path
            parcel_lyr_path = parcel_lyr.dataSource
            layer_name = "Agland"
            layer_path = f"{parcel_lyr_path}_Agland"

            # export shape to new feature class
            arcpy.conversion.ExportFeatures(parcel_lyr, layer_path)
            lyr = m.addDataFromPath(layer_path)
            lyr.name = layer_name

            # update symbology
            sym = lyr.symbology
            sym.renderer.symbol.color = {"RGB": [0, 0, 0, 0]}
            sym.renderer.symbol.outlineColor = {"RGB": [255, 0, 0, 100]}
            sym.renderer.symbol.size = 3
            lyr.symbology = sym

            # clear selection
            m.clearSelection()

        # Cleanup
        log("cleaning up")
        project.save()
        del project
