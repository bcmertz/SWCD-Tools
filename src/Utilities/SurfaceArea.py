# --------------------------------------------------------------------------------
# Name:        Surface Area
# Purpose:     This tool finds the area of a polygon in the specified units
#
# License:     Contextual Copyleft AI (CCAI) License v1.0.
#              Full license in LICENSE file.
# --------------------------------------------------------------------------------

import arcpy

from helpers.logging import log
from helpers.parameter import raster_and_layer
from helpers.tool import EXTENSIONS, license, reload_module
from helpers.tool import setup_environment as setup
from helpers.units import AREAL_UNITS, SPATIAL_UNITS, Area, Distance, get_linear_unit, get_z_unit


class SurfaceArea:
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Surface Area"
        self.category = "Utilities"

    def getParameterInfo(self):
        """Define the tool parameters."""
        param0 = arcpy.Parameter(
            displayName="Polygon",
            name="polygon",
            datatype="GPFeatureLayer",
            parameterType="Required",
            direction="Input")
        param0.filter.list = ["Polygon"]
        param0.controlCLSID = '{60061247-BCA8-473E-A7AF-A2026DDE1C2D}' # allows polygon creation

        param1 = arcpy.Parameter(
            displayName="DEM",
            name="dem",
            datatype="GPRasterLayer",
            parameterType="Required",
            direction="Input")

        param2 = arcpy.Parameter(
            displayName="Z Unit",
            name="z_unit",
            datatype="GPString",
            parameterType="Required",
            direction="Input")
        param2.filter.list = list(SPATIAL_UNITS)

        param3 = arcpy.Parameter(
            displayName="Watershed Area Unit",
            name="unit",
            datatype="GPString",
            parameterType="Required",
            direction="Input")
        param3.filter.list = list(AREAL_UNITS)
        param3.value = "US Survey Acres"

        params = [param0, param1, param2, param3]
        return params

    def updateParameters(self, parameters):
        # find z unit of raster based on vertical coordinate system
        #  - if there is none, let the user define it
        #  - if it exists, set the value and hide the parameter
        #  - if it doesn't exist show the parameter and set the value to None
        if not parameters[1].hasBeenValidated:
            if parameters[1].value:
                z_unit = get_z_unit(parameters[1].value)
                if z_unit is not None:
                    parameters[2].enabled = False
                    parameters[2].value = z_unit
                else:
                    parameters[2].enabled = True
                    parameters[2].value = None
            else:
                parameters[2].enabled = False
                parameters[2].value = None

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
        log("reading in parameters")
        feature = parameters[0].value
        dem, _ = raster_and_layer(parameters[1].value)
        z_unit = SPATIAL_UNITS[parameters[2].value].to_linear()
        areal_unit_output = AREAL_UNITS(parameters[3].value)

        # get linear output units
        log("finding output units")
        linear_unit = get_linear_unit(feature)
        z_factor = str(Distance(1, z_unit).to_unit(linear_unit).amount)
        log("z_factor:", z_factor)

        # get areal output units
        areal_unit_input = linear_unit.to_areal()
        log(areal_unit_input, areal_unit_output)
        scale_factor = Area(1, areal_unit_input).to_unit(areal_unit_output).amount
        log("scale_factor:", scale_factor)

        log("calculating surface area")
        out_fc = arcpy.sa.AddSurfaceInformation(
            in_feature_class=feature,
            in_surface=dem,
            out_property="SURFACE_AREA",
            method="BILINEAR",
            z_factor=z_factor,
        )

        log("scaling output measurements to units")
        with arcpy.da.UpdateCursor(out_fc, "SArea") as cursor:
            for polygon in cursor:
                polygon[0] = polygon[0] * scale_factor
                cursor.updateRow(polygon)

        # save and exit program successfully
        log("saving project")
        project.save()
