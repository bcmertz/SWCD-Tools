# --------------------------------------------------------------------------------
# Name:        Stream Slope
# Purpose:     This tool calculates the percent slope of each stream feature
#              and outputs it in a new feature class.
#
# License:     Contextual Copyleft AI (CCAI) License v1.0.
#              Full license in LICENSE file.
# --------------------------------------------------------------------------------
import arcpy

from helpers.features import find_field
from helpers.logging import log
from helpers.parameter import raster_and_layer
from helpers.parameter import validate_spatial_reference as validate
from helpers.tool import (
    EXTENSIONS,
    empty_workspace,
    license,
    reload_module,
)
from helpers.tool import setup_environment as setup
from helpers.units import SPATIAL_UNITS, Distance, get_linear_unit, get_z_unit


def stream_slope(stream, dem, z_factor):
    # check if slope was calculated previously so we can overwrite it
    slope_prev = find_field(stream, name="slope_per")
    if slope_prev:
        log("removing old slope information")
        arcpy.management.DeleteField(stream, ["slope_per"])

    # calculate percent slope
    log("calculating percent slope")
    arcpy.sa.AddSurfaceInformation(
        in_feature_class=stream,
        in_surface=dem,
        out_property="AVG_SLOPE",
        method="BILINEAR",
        z_factor=z_factor,
    )

    # alias Avg_Slope field
    log("updating field name")
    slope_field = find_field(stream, name="Avg_Slope")
    arcpy.management.AlterField(
        in_table=stream,
        field=slope_field.name,
        new_field_name="slope_per",
        new_field_alias="Slope (%)",
    )

class StreamSlope:
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Stream Slope"
        self.description = "Calculate percent slope of each stream feature."
        self.category = "Fluvial Geomorphology"

    def getParameterInfo(self):
        """Define parameter definitions"""
        param0 = arcpy.Parameter(
            displayName="Hydro-Conditioned DEM",
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
        param1.filter.list = list(SPATIAL_UNITS)

        param2 = arcpy.Parameter(
            displayName="Analysis Area",
            name="analysis_area",
            datatype="GPExtent",
            parameterType="Optional",
            direction="Input")
        param2.controlCLSID = '{15F0D1C1-F783-49BC-8D16-619B8E92F668}'

        param3 = arcpy.Parameter(
            displayName="Stream Lines",
            name="stream",
            datatype="GPFeatureLayer",
            parameterType="Optional",
            direction="Input")
        param3.filter.list = ["Polyline"]
        param3.controlCLSID = '{60061247-BCA8-473E-A7AF-A2026DDE1C2D}' # allows line creation

        params = [param0, param1, param2, param3]
        return params

    def updateParameters(self, parameters):
        # find z unit of raster based on vertical coordinate system
        #  - if there is none, let the user define it
        #  - if it exists, set the value and hide the parameter
        #  - if it doesn't exist show the parameter and set the value to None
        if not parameters[0].hasBeenValidated:
            if parameters[0].value:
                z_unit = get_z_unit(parameters[0].value)
                if z_unit is not None:
                    parameters[1].enabled = False
                    parameters[1].value = z_unit
                else:
                    parameters[1].enabled = True
                    parameters[1].value = None
            else:
                parameters[1].enabled = False
                parameters[1].value = None

    def isLicensed(self):
        """Set whether the tool is licensed to execute."""
        return license([EXTENSIONS.Spatial])

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool parameter."""
        validate(parameters)

    @reload_module(__name__)
    def execute(self, parameters, _messages):
        """The source code of the tool."""
        # Setup
        log("setting up project")
        project, active_map = setup()

        # read in parameters
        dem, _ = raster_and_layer(parameters[0].value)
        z_unit = SPATIAL_UNITS[parameters[1].value].to_linear()
        extent = parameters[2].value
        stream = parameters[3].value

        # set analysis extent
        if extent:
            arcpy.env.extent = extent

        # z_factor converts dem z linear units to dem x,y linear units
        log("finding z_factor of dem")
        linear_unit = get_linear_unit(dem)
        z_factor = str(Distance(1, z_unit).to_unit(linear_unit).amount)

        # calculating stream slope
        stream_slope(stream, dem, z_factor)

        # TODO: check if stream fc is already in map
        # add output_file to map
        log("adding output to map")
        active_map.addDataFromPath(stream)

        # save and exit program successfully
        log("saving project")
        project.save()

        # cleanup
        log("deleting unneeded data")
        empty_workspace(arcpy.env.scratchGDB, keep=[])
