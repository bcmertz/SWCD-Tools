# --------------------------------------------------------------------------------
# Name:        Topographic Wetness Index (TWI)
# Purpose:     This tool calculates the TWI for an estimate of hydrologic activity.
#
# License:     GNU Affero General Public License v3.
#              Full license in LICENSE file, or at <https://www.gnu.org/licenses/>
# --------------------------------------------------------------------------------

import math
import arcpy

from helpers import license, get_z_unit, z_units, reload_module
from helpers import print_messages as log
from helpers import setup_environment as setup
from helpers import validate_spatial_reference as validate

class TopographicWetness(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Topographic Wetness Index (TWI)"
        self.description = "Calculate Topographic Wetness of a given area"
        self.category = "Hydrology"
        self.canRunInBackground = False

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
        param1.filter.list = z_units

        param2 = arcpy.Parameter(
            displayName="Analysis Area",
            name="analysis_area",
            datatype="GPExtent",
            parameterType="Optional",
            direction="Input")
        param2.controlCLSID = '{15F0D1C1-F783-49BC-8D16-619B8E92F668}'

        param3 = arcpy.Parameter(
            displayName="Output Features",
            name="out_features",
            datatype="DEFeatureClass",
            parameterType="Required",
            direction="Output")
        param3.parameterDependencies = [param0.name]
        param3.schema.clone = True

        params = [param0, param1, param2, param3]
        return params

    def isLicensed(self):
        """Set whether the tool is licensed to execute."""
        return license(['Spatial'])

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

    @reload_module(__name__)
    def execute(self, parameters, messages):
        """The source code of the tool."""
        # Setup
        log("setting up project")
        project, active_map = setup()

        # read in parameters
        dem_layer = parameters[0].value
        dem = arcpy.Raster(dem_layer.name)
        z_unit = parameters[1].value
        extent = parameters[2].value
        output_file = parameters[3].valueAsText

        # set analysis extent
        if extent:
            arcpy.env.extent = extent

        # fill raster
        log("filling raster")
        fill_raster_scratch = arcpy.sa.Fill(dem)

        # flow accumulation
        log("calculating flow accumulation")
        out_accumulation_raster = arcpy.sa.DeriveContinuousFlow(fill_raster_scratch, flow_direction_type="MFD")
        flow_accumulation = arcpy.sa.Float(out_accumulation_raster)

        # calculate slope
        log("calculating slope")
        slope_raster = arcpy.sa.Slope(dem, "DEGREE", "", "GEODESIC", z_unit)

        # convert slope to radians
        log("converting slope raster to radians")
        slope_radians = arcpy.sa.Float(slope_raster) * (math.pi / 180)

        # calculate slope tangent
        log("calculating slope tangent")
        out_slope_tan = arcpy.sa.Tan(slope_radians)

        # adjust flow accumulation
        log("adjusting flow accumulation")
        adjusted_flow_accumulation = flow_accumulation + 1

        # calculate topographic wetness index (TWI)
        log("calculating topographic wetness index")
        out_TWI = arcpy.sa.Ln(adjusted_flow_accumulation / out_slope_tan)
        out_TWI.save(output_file)

        # add TWI to map
        log("adding twi to map")
        twi_layer = active_map.addDataFromPath(output_file)

        # update raster symbology
        log("updating twi symbology")
        sym = twi_layer.symbology
        if hasattr(sym, 'colorizer'):
            if sym.colorizer.type != "RasterStretchColorizer":
                sym.updateColorizer("RasterStretchColorizer")
            sym.colorizer.colorRamp = project.listColorRamps('Blue Bright')[0]
            twi_layer.symbology = sym

        # save and exit program successfully
        log("saving project")
        project.save()

        return
