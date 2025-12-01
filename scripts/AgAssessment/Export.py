# --------------------------------------------------------------------------------
# Name:        Export
# Purpose:     This tool exports the needed layouts into the output folder
#
# License:     GNU Affero General Public License v3.
#              Full license in LICENSE file, or at <https://www.gnu.org/licenses/>
# --------------------------------------------------------------------------------
import os
import datetime

from helpers import *
import print_messages as log
import setup_environment as setup
import validate_spatial_reference as validate
import license as license

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
        return license([])

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool parameter."""
        validate(parameters)
        return

    def execute(self, parameters, messages):
        """The source code of the tool."""
        # Setup
        log("setting up project")
        project, active_map = setup()

        # Helpers
        project_name = project.filePath.split("\\")[-1][:-5]

        # Path Root
        year = datetime.date.today().year
        path_root = "O:\Ag Assessments\{}\{}".format(year, project_name)

        # Export layouts
        log("exporting layouts")
        layouts = project.listLayouts()
        for layout in layouts:
            if layout.name == "Layout":
                continue
            layout_file_path = "{}\{}.pdf".format(path_root, layout.name)
            layout.exportToPDF(layout_file_path)

        # Open project folder
        log("opening project folder")
        os.startfile(path_root)

        return
