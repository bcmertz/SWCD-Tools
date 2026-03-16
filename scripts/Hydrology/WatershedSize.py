# --------------------------------------------------------------------------------
# Name:        Wateshed Size
# Purpose:     This tool TODO
#
# License:     GNU Affero General Public License v3.
#              Full license in LICENSE file, or at <https://www.gnu.org/licenses/>
# --------------------------------------------------------------------------------
import arcpy

from ..helpers import license, empty_workspace, reload_module, log, LINEAR_UNITS, get_z_unit
from ..helpers import setup_environment as setup
from ..helpers import validate_spatial_reference as validate

class WatershedSize:
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Watershed Size"
        self.category = "Hydrology"
        self.description = "Calculate Watershed Size"

    def getParameterInfo(self):
        """Define parameter definitions"""
        param0 = arcpy.Parameter(
            displayName="DEM",
            name="dem",
            datatype="GPRasterLayer",
            parameterType="Required",
            direction="Input")

        param1 = arcpy.Parameter(
            displayName="Z Unit",
            name="z_unit",
            datatype="GPString",
            parameterType="Required",
            direction="Input")
        param1.filter.list = LINEAR_UNITS

        param2 = arcpy.Parameter(
            displayName="Output Folder",
            name="output_location",
            datatype="DEFolder",
            parameterType="Required",
            direction="Input")

        params = [param0, param1, param2]
        return params

    def updateParameters(self, parameters):
        # find z unit of raster based on vertical coordinate system
        #  - if there is none, let the user define it
        #  - if it exists, set the value and hide the parameter
        #  - if it doesn't exist show the parameter and set the value to None
        if not parameters[0].hasBeenValidated:
            if parameters[0].value:
                z_unit = get_z_unit(parameters[0].value)
                if z_unit:
                    parameters[1].enabled = False
                    parameters[1].value = z_unit
                else:
                    parameters[1].enabled = True
                    parameters[1].value = None
            else:
                parameters[1].enabled = False
                parameters[1].value = None

        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool parameter."""
        validate(parameters)
        return

    def isLicensed(self):
        """Set whether the tool is licensed to execute."""
        return license(['Spatial'])

    @reload_module(__name__)
    def execute(self, parameters, messages):
        """The source code of the tool."""
        # Setup
        log("setting up project")
        project, active_map = setup()

        # read in parameters
        log("reading in parameters")
        raster_layer = parameters[0].value
        z_unit = parameters[1].value
        output_folder_path = parameters[2].valueAsText

        log(raster_layer, z_unit, output_folder_path)

        # cleanup
        log("deleting unneeded data")
        empty_workspace(arcpy.env.scratchGDB, keep=[])
        arcpy.management.Delete([])

        # save program successfully
        log("saving project")
        project.save()

        return
