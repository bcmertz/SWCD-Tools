# --------------------------------------------------------------------------------
# Name:        Stream Power
# Purpose:     This tool calculates stream power.
#
# License:     Contextual Copyleft AI (CCAI) License v1.0.
#              Full license in LICENSE file.
# --------------------------------------------------------------------------------
import arcpy

from helpers.logging import log
from helpers.parameter import validate_spatial_reference as validate
from helpers.tool import (
    EXTENSIONS,
    empty_workspace,
    license,
    reload_module,
)
from helpers.tool import setup_environment as setup
from helpers.units import FLOW_UNITS, SLOPE_UNITS, Flow, Slope


class StreamPower:
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Stream Power"
        self.description = "Calculate stream power"
        self.category = "Fluvial Geomorphology"

    def getParameterInfo(self):
        """Define parameter definitions"""
        param0 = arcpy.Parameter(
            displayName="Existing Stream Lines",
            name="stream",
            datatype="GPFeatureLayer",
            parameterType="Optional",
            direction="Input")
        param0.filter.list = ["Polyline"]
        param0.controlCLSID = '{60061247-BCA8-473E-A7AF-A2026DDE1C2D}' # allows line creation

        param1 = arcpy.Parameter(
            displayName="Analysis Area",
            name="analysis_area",
            datatype="GPExtent",
            parameterType="Optional",
            direction="Input")
        param1.controlCLSID = '{15F0D1C1-F783-49BC-8D16-619B8E92F668}'

        param2 = arcpy.Parameter(
            displayName="Slope Field",
            name="slope_field",
            datatype="GPString",
            parameterType="Required",
            direction="Input",
        )
        param2.filter.type = "ValueList"
        param2.filter.list = []

        param3 = arcpy.Parameter(
            displayName="Slope Unit",
            name="slope_unit",
            datatype="GPString",
            parameterType="Required",
            direction="Input")
        param3.filter.list = list(SLOPE_UNITS)

        param4 = arcpy.Parameter(
            displayName="Stream Flow Field",
            name="flow_field",
            datatype="GPString",
            multiValue="True",
            parameterType="Required",
            direction="Input",
        )
        param4.filter.type = "ValueList"
        param4.filter.list = []

        param5 = arcpy.Parameter(
            displayName="Flow Unit",
            name="flow_unit",
            datatype="GPString",
            parameterType="Required",
            direction="Input")
        param5.filter.list = list(FLOW_UNITS)

        param6 = arcpy.Parameter(
            displayName="Output Features",
            name="out_features",
            datatype="DEFeatureClass",
            direction="Output")
        param6.parameterDependencies = [param0.name]
        param6.schema.clone = True

        # TODO: type of power - specific, index, total

        params = [param0, param1, param2, param3, param4, param5, param6]
        return params

    def updateParameters(self, parameters):
        # handle stream layer
        if not parameters[0].hasBeenValidated:
            if parameters[0].value:
                parameters[2].enabled = True
                parameters[4].enabled = True
                fields = [f.name for f in arcpy.ListFields(parameters[0].value)]
                parameters[2].filter.list = fields
                parameters[4].filter.list = fields
            else:
                parameters[2].value = None
                parameters[2].enabled = False
                parameters[4].value = None
                parameters[4].enabled = False

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
        streams = parameters[0].value
        extent = parameters[1].value
        slope_field: set[str] = parameters[2].valueAsText
        slope_unit = SLOPE_UNITS(parameters[3].valueAsText)
        discharge_fields: set[str] = set(parameters[4].valueAsText.replace("'","").split(";"))
        flow_unit = FLOW_UNITS(parameters[5].valueAsText)
        output_file = parameters[6].valueAsText

        # set analysis extent
        if extent:
            arcpy.env.extent = extent

        # copy input to output fc
        log("copying features to output")
        arcpy.management.CopyFeatures(streams, output_file)

        # find unit conversions
        log("finding unit conversions")
        slope_adjust = Slope(1, slope_unit).to_unit(SLOPE_UNITS.Ratio).
        flow_adjust = Flow(1, flow_unit).to_unit(FLOW_UNITS.CMS)

        # calculate stream power for each discharge field
        log("calculating stream power at each discharge given")
        for discharge_field in discharge_fields:
            # add field and calculate power
            power_field = discharge_field[0:4] + "_power" # TODO add units
            arcpy.management.CalculateField(
                in_table=output_file,
                field=power_field,
                expression=f"!{slope_field}!*!{discharge_field}!*9800*{slope_adjust}*{flow_adjust}",
                expression_type="PYTHON3",
                code_block="",
                field_type="DOUBLE",
                enforce_domains="NO_ENFORCE_DOMAINS"
            )

        # add flow path polyline to map
        log("adding output to map")
        active_map.addDataFromPath(output_file)

        # save and exit program successfully
        log("saving project")
        project.save()

        # cleanup
        log("deleting unneeded data")
        empty_workspace(arcpy.env.scratchGDB, keep=[])
