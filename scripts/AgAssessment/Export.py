# --------------------------------------------------------------------------------
# Name:        Export
# Purpose:     This tool exports the needed layouts into the output folder
#
# License:     GNU Affero General Public License v3.
#              Full license in LICENSE file, or at <https://www.gnu.org/licenses/>
# --------------------------------------------------------------------------------

import os
import json

from ..helpers import license, reload_module
from ..helpers import print_messages as log
from ..helpers import setup_environment as setup
from ..helpers import validate_spatial_reference as validate

class Export(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "4. Export Layouts"
        self.description = "Run to export layouts"
        self.category = "Automated Ag Assessment"
        self.canRunInBackground = False

    def getParameterInfo(self):
        """Define parameter definitions"""
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
        project_dir = project.homeFolder
        cache_file_path = "{}/.ag_cache.json".format(project_dir)

        # read in json
        log("reading in cache")
        cache = {}
        with open(cache_file_path) as file:
            cache = json.load(file)
        parcels = set(cache["parcels"])
        output_folder = cache["output_folder"]

        # Export layouts
        log("exporting layouts")
        layouts = project.listLayouts()
        for layout in layouts:
            if layout.name in parcels:
                layout_file_path = "{}\{}.pdf".format(output_folder, layout.name)
                layout.exportToPDF(layout_file_path)

        # Open project folder
        log("opening project folder")
        os.startfile(output_folder)

        return
