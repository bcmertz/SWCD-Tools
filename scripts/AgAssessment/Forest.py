# --------------------------------------------------------------------------------
# Name:        Forest
# Purpose:     This tool categorizes a piece of land in an ag assessment as
#              forest land for further processing
#
# Author:      Reya Mertz
#
# Created:     11/2025
# Modified:    11/2025
# License:     GNU Affero General Public License v3.
#              Full license in LICENSE file, or at <https://www.gnu.org/licenses/>
# --------------------------------------------------------------------------------

import arcpy
import re

# setup helpers
import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), "../helpers"))
from print_messages import print_messages as log
from setup_environment import setup_environment as setup
from sanitize import sanitize
from validate_spatial_reference import validate_spatial_reference as validate
from license import license as license

class Forest(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "2c. Delineate Forest"
        self.category = "Automated Ag Assessment"
        self.description = "Select all forest land for delineation"

    def isLicensed(self):
        """Set whether the tool is licensed to execute."""
        return license([])

    def getParameterInfo(self):
        """Define parameter definitions"""
        params = []
        return params

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool parameter."""
        validate(parameters)
        return

    def execute(self, parameters, messages):
        """The source code of the tool."""
        # Setup
        log("setting up project")
        project, active_map = setup()

        maps = project.listMaps()
        # Check if we're on a created map
        map_name_format = re.compile('[0-9]+\.[0-9]+\-[0-9]\-[0-9]+\.[0-9]+')
        log("iterating through maps and delineating forest land")
        for m in maps:
            # Get Tax ID Number for map
            tax_id_num = m.name
            # look at next map if this one isn't a tax id number map
            if map_name_format.match(tax_id_num) is None:
                continue

            # get parcel layer or drop off of map
            lyrs = m.listLayers("*_{}".format(tax_id_num))
            if len(lyrs) == 0:
                log("no appropriate parcel layer found")
                continue

            # get cursor shape
            fc = lyrs[0]
            #fc_print_key = [row[0] for row in arcpy.da.SearchCursor(fc, "PRINT_KEY")][0]

            # check how many pieces are selected
            sel_set = fc.getSelectionSet()
            if sel_set == None:
                continue

            # construct layer names and paths
            layer_name = "{}_Forest".format(fc.name)
            sanitized_name = sanitize(layer_name)
            layer_path = "{}\\{}".format(arcpy.env.workspace, sanitized_name)

            # export shape to new feature class
            feat = arcpy.management.MakeFeatureLayer(fc, layer_name)
            log("layer_path: ", layer_path)
            arcpy.management.CopyFeatures(feat, layer_path)
            lyr = m.addDataFromPath(layer_path)
            lyr.name = "Forest_{}".format(sanitize(tax_id_num.split("-")[-1]))

            # update symbology
            sym = lyr.symbology
            sym.renderer.symbol.color = {'RGB' : [0, 0, 0, 0]}
            sym.renderer.symbol.outlineColor = {'RGB' : [85, 255, 0, 100]}
            sym.renderer.symbol.size = 3
            lyr.symbology = sym

            # clear selection
            m.clearSelection()

        # Save
        log("saving project")
        project.save()
        return
