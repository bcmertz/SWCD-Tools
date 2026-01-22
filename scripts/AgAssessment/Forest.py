# --------------------------------------------------------------------------------
# Name:        Forest
# Purpose:     This tool categorizes a piece of land in an ag assessment as
#              forest land for further processing
#
# License:     GNU Affero General Public License v3.
#              Full license in LICENSE file, or at <https://www.gnu.org/licenses/>
# --------------------------------------------------------------------------------

import json
import arcpy

from ..helpers import sanitize, license, reload_module, log
from ..helpers import setup_environment as setup
from ..helpers import validate_spatial_reference as validate

class Forest(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "2c. Delineate Forest"
        self.category = "Automated Ag Assessment"
        self.description = "Select all forest land for delineation"

    def isLicensed(self):
        """Set whether the tool is licensed to execute."""
        return license()

    def getParameterInfo(self):
        """Define parameter definitions"""
        params = []
        return params

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
        project_dir = project.homeFolder
        cache_file_path = "{}/.ag_cache.json".format(project_dir)

        # read in json
        log("reading in cache")
        cache = {}
        with open(cache_file_path) as file:
            cache = json.load(file)
        parcels = cache["parcels"]

        log("iterating through maps and delineating forest land")
        for parcel in parcels:
            # find map of parcel
            m = None
            try:
                m = project.listMaps(parcel)[0]
            except:
                log("unable to find map for {}, results may be incomplete".format(parcel))
                continue

            # get parcel layer or drop off of map
            fc = None
            try:
                fc = m.listLayers("*_{}".format(parcel))[0]
            except:
                log("no appropriate parcel layer found for {}, results may be incomplete".format(parcel))
                continue

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
            arcpy.management.CopyFeatures(feat, layer_path)
            lyr = m.addDataFromPath(layer_path)
            lyr.name = "Forest_{}".format(sanitize(parcel)[-4:])

            # update symbology
            sym = lyr.symbology
            sym.renderer.symbol.color = {'RGB' : [0, 0, 0, 0]}
            sym.renderer.symbol.outlineColor = {'RGB' : [85, 255, 0, 100]}
            sym.renderer.symbol.size = 3
            lyr.symbology = sym

            # clear selection
            m.clearSelection()

        # Cleanup
        log("cleaning up")
        project.save()
        del project

        return
