# --------------------------------------------------------------------------------
# Name:        Wateshed Size
# Purpose:     This tool TODO
#
# License:     GNU Affero General Public License v3.
#              Full license in LICENSE file, or at <https://www.gnu.org/licenses/>
# --------------------------------------------------------------------------------
import arcpy

from ..helpers import license, reload_module, log, AREAL_UNITS, AREAL_UNITS_MAP, cell_area, convert_area
from ..helpers import setup_environment as setup
from ..helpers import validate_spatial_reference as validate

class WatershedSize:
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Watershed Size Raster"
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
            displayName="Analysis Area",
            name="analysis_area",
            datatype="GPExtent",
            parameterType="Optional",
            direction="Input")
        param1.controlCLSID = '{15F0D1C1-F783-49BC-8D16-619B8E92F668}'

        param2 = arcpy.Parameter(
            displayName="Watershed Area Unit",
            name="unit",
            datatype="GPString",
            parameterType="Required",
            direction="Input")
        param2.filter.list = AREAL_UNITS
        param2.value = "US Survey Acres"

        param3 = arcpy.Parameter(
            displayName="Output Raster",
            name="out_features",
            datatype="DEFeatureClass",
            direction="Output")
        param3.parameterDependencies = [param0.name, param2.name]
        param3.schema.clone = True

        params = [param0, param1, param2, param3]
        return params

    def updateParameters(self, parameters):
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
        dem = parameters[0].value
        extent = parameters[1].value
        # read in areal unit and map it's pretty string to the arcpy representation
        areal_unit = AREAL_UNITS_MAP[parameters[2].valueAsText]
        output_file = parameters[3].valueAsText

        # set analysis extent
        if extent:
            arcpy.env.extent = extent

        # fill raster
        log("filling raster")
        fill_dem = arcpy.sa.Fill(dem)

        # flow direction
        log("calculating flow direction")
        flow_direction = arcpy.sa.FlowDirection(fill_dem)

        # flow accumulation
        log("calculating flow accumulation")
        flow_accumulation = arcpy.sa.FlowAccumulation(flow_direction)

        # convert flow accumulation from number of cells to threshold area units
        log("calculating watershed size")
        raster_cell_area = cell_area(dem)
        cell_size = convert_area(raster_cell_area, areal_unit).split(" ")[0]
        watershed_size = flow_accumulation * float(cell_size)

        # save output to file
        log("saving output to file")
        watershed_size.save(output_file)

        # add watershed size raster to map
        log("adding watershed size raster to map")
        active_map.addDataFromPath(output_file)

        # save program successfully
        log("saving project")
        project.save()

        return
