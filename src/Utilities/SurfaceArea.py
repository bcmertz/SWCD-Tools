# --------------------------------------------------------------------------------
# Name:        Surface Area
# Purpose:     This tool finds the area of a polygon in the specified units
#
# License:     Contextual Copyleft AI (CCAI) License v1.0.
#              Full license in LICENSE file.
# --------------------------------------------------------------------------------

import arcpy
from helpers import EXTENSIONS, license, log, reload_module
from helpers import setup_environment as setup


class SurfaceArea:
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Surface Area"
        self.category = "Utilities"

    def getParameterInfo(self):
        """Define the tool parameters."""
        param0 = arcpy.Parameter(
            displayName="Analysis Area",
            name="analysis_area",
            datatype="GPExtent",
            parameterType="Required",
            direction="Input")
        param0.controlCLSID = '{15F0D1C1-F783-49BC-8D16-619B8E92F668}'

        params = [param0]
        return params

    def isLicensed(self):
        """Set whether the tool is licensed to execute."""
        return license([EXTENSIONS.Spatial])

    @reload_module(__name__)
    def execute(self, parameters, _):
        """The source code of the tool."""
        # Setup
        log("setting up project")
        project, orig_map = setup()

        # reading in parameters
        extent = parameters[0].value
