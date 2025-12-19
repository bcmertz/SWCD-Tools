# --------------------------------------------------------------------------------
# Name:        Contour Polygon
# Purpose:     This tool takes a polygon and creates the specified contours in it.
#
# License:     GNU Affero General Public License v3.
#              Full license in LICENSE file, or at <https://www.gnu.org/licenses/>
# --------------------------------------------------------------------------------

import arcpy

from helpers import license
from helpers import print_messages as log
from helpers import setup_environment as setup
from helpers import validate_spatial_reference as validate

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
            displayName="Contour Area",
            name="polygon",
            datatype="GPFeatureLayer",
            parameterType="Required",
            direction="Input")
        param1.filter.list = ["Polygon"]
        param1.controlCLSID = '{60061247-BCA8-473E-A7AF-A2026DDE1C2D}' # allows polygon creation

        param2 = arcpy.Parameter(
            displayName="Output Features",
            name="out_features",
            datatype="DEFeatureClass",
            direction="Output")

        param2.parameterDependencies = [param0.name]
        param2.schema.clone = True

        param3 = arcpy.Parameter(
            displayName="Contour Interval (ft)",
            name="contour_interval",
            datatype="GPLong",
            parameterType="Required",
            direction="Input")

        param4 = arcpy.Parameter(
            displayName="Z Unit",
            name="z_unit",
            datatype="GPString",
            parameterType="Required",
            direction="Input")
        param4.filter.list = ["METER", "FOOT"]

        params = [param0, param1, param2, param3, param4]
        return params

    def updateParameters(self, parameters):
        # find z unit of raster
        if not parameters[0].hasBeenValidated:
            if parameters[0].value:
                desc = arcpy.Describe(parameters[0].value)
                if desc.spatialReference.VCS:
                    if desc.spatialReference.VCS.linearUnitName == "METER":
                        parameters[4] = "METER"
                    elif desc.spatialReference.VCS.linearUnitName == "FOOT":
                        parameters[4] = "FOOT"
                    else:
                        parameters[4] = None
                else:
                    parameters[4] = None

        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool parameter."""
        validate(parameters)
        return

    def isLicensed(self):
        """Set whether the tool is licensed to execute."""
        return license(['Spatial'])

    def execute(self, parameters, messages):
        """The source code of the tool."""
        # setup
        log("setting up project")
        project, active_map = setup()

        # get parameters
        raster_layer = parameters[0].value
        polygon = parameters[1].value
        output_file = parameters[2].valueAsText
        contour_interval = parameters[3].valueAsText
        z_unit = parameters[4].value

        # calculate z_factor
        z_factor = None
        if z_unit == "Meter":
            z_factor = 3.2808
        elif z_unit == "Foot":
            z_factor = 1
        else:
            raise ValueError("Bad z-unit value")

        # clip raster to polyon
        log("clipping raster to polygon")
        outExtractByMask = arcpy.sa.ExtractByMask(raster_layer, polygon, "INSIDE")

        # create contour in polygon
        log("creating contour")
        arcpy.sa.Contour(outExtractByMask, output_file, contour_interval, z_factor=z_factor)

        # add contours to map
        log("adding contours to map")
        active_map.addDataFromPath(output_file)

        return
