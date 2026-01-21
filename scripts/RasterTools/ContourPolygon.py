# --------------------------------------------------------------------------------
# Name:        Contour Polygon
# Purpose:     This tool takes a polygon and creates the specified contours in it.
#
# License:     GNU Affero General Public License v3.
#              Full license in LICENSE file, or at <https://www.gnu.org/licenses/>
# --------------------------------------------------------------------------------

import arcpy

from ..helpers import license, get_z_unit, z_units, reload_module
from ..helpers import print_messages as log
from ..helpers import setup_environment as setup
from ..helpers import validate_spatial_reference as validate

class ContourPolygon(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Contour Polygon"
        self.description = "Contour polygon from DEM"
        self.category = "Raster Tools"
        self.canRunInBackground = True

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
            displayName="Contour Area",
            name="polygon",
            datatype="GPFeatureLayer",
            parameterType="Required",
            direction="Input")
        param2.filter.list = ["Polygon"]
        param2.controlCLSID = '{60061247-BCA8-473E-A7AF-A2026DDE1C2D}' # allows polygon creation

        param3 = arcpy.Parameter(
            displayName="Output Features",
            name="out_features",
            datatype="DEFeatureClass",
            direction="Output")
        param3.parameterDependencies = [param0.name]
        param3.schema.clone = True

        param4 = arcpy.Parameter(
            displayName="Contour Interval",
            name="contour_interval",
            datatype="GPLinearUnit",
            parameterType="Required",
            direction="Input")

        params = [param0, param1, param2, param3, param4]
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

        if not parameters[4].value:
            parameters[4].value = "10 Feet"

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
        # setup
        log("setting up project")
        project, active_map = setup()

        # get parameters
        raster_layer = parameters[0].value
        z_unit = parameters[1].value
        polygon = parameters[2].value
        output_file = parameters[3].valueAsText
        contour_interval, contour_unit = parameters[4].valueAsText.split(" ")
        z_factor = arcpy.LinearUnitConversionFactor(z_unit, contour_unit)

        # clip raster to polyon
        log("clipping raster to polygon")
        outExtractByMask = arcpy.sa.ExtractByMask(raster_layer, polygon, "INSIDE")

        # create contour in polygon
        log("creating contour")
        arcpy.sa.Contour(
            in_raster=outExtractByMask,
            out_polyline_features=output_file,
            contour_interval=contour_interval,
            base_contour=0,
            z_factor=z_factor
        )

        # add contours to map
        log("adding contours to map")
        active_map.addDataFromPath(output_file)

        return
