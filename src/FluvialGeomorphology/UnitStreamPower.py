# --------------------------------------------------------------------------------
# Name:        Unit Stream Power
# Purpose:     This tool creates a raster of unit or specific stream power within a
#              geometry
#
# License:     Contextual Copyleft AI (CCAI) License v1.0.
#              Full license in LICENSE file.
# --------------------------------------------------------------------------------
import arcpy

from helpers.logging import log
from helpers.parameter import raster_and_layer
from helpers.parameter import validate_spatial_reference as validate
from helpers.rasters import (
    cell_length,
    circular_mask,
    coordinate_to_pixel,
    raster_max_coordinates,
)
from helpers.spatial import get_linear_unit
from helpers.tool import (
    EXTENSIONS,
    empty_workspace,
    license,
    reload_module,
)
from helpers.tool import setup_environment as setup
from helpers.units import LINEAR_UNITS, Distance


class UnitStreamPower:
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Unit Stream Power"
        self.description = "Calculate stream power raster"
        self.category = "Fluvial Geomorphology"

    def getParameterInfo(self):
        """Define parameter definitions"""
        param0 = arcpy.Parameter(
            displayName="Stream Line",
            name="stream",
            datatype="GPFeatureLayer",
            parameterType="Optional",
            direction="Input")
        param0.filter.list = ["PolyLine"]

        param1 = arcpy.Parameter(
            displayName="Stream Power Field",
            name="flow_field",
            datatype="GPString",
            multiValue="True",
            parameterType="Required",
            direction="Input",
        )
        param1.filter.type = "ValueList"
        param1.filter.list = []

        param2 = arcpy.Parameter(
            displayName="Analysis Area",
            name="analysis_area",
            datatype="GPExtent",
            parameterType="Optional",
            direction="Input")
        param2.controlCLSID = '{15F0D1C1-F783-49BC-8D16-619B8E92F668}'

        param3 = arcpy.Parameter(
            displayName="Stream Width Raster",
            name="width",
            datatype="GPRasterLayer",
            parameterType="Required",
            direction="Input")

        param4 = arcpy.Parameter(
            displayName="Stream Width Unit",
            name="width_unit",
            datatype="GPString",
            parameterType="Required",
            direction="Input")
        param4.filter.list = list(LINEAR_UNITS)

        param5 = arcpy.Parameter(
            displayName="Output Features",
            name="out_features",
            datatype="DEFeatureClass",
            direction="Output")
        param5.parameterDependencies = [param0.name]
        param5.schema.clone = True

        params = [param0, param1, param2, param3, param4, param5]
        return params

    def updateParameters(self, parameters):
        # handle stream layer
        if not parameters[0].hasBeenValidated:
            if parameters[0].value:
                fields = [f.name for f in arcpy.ListFields(parameters[0].value)]
                parameters[2].enabled = True
                parameters[2].filter.list = fields
            else:
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
        streams = parameters[0].valueAsText
        power_field: set[str] = parameters[1].valueAsText
        extent = parameters[2].value
        width, _ = raster_and_layer(parameters[3].value)
        width_unit = LINEAR_UNITS[parameters[4].valueAsText]
        conversion_factor = Distance(1, width_unit).to_unit(LINEAR_UNITS.Meters).length # input unit to meters
        output_file = parameters[5].valueAsText

        # set analysis extent
        if extent:
            arcpy.env.extent = extent

        # create scratch layers
        log("creating scratch layers")
        scratch_streams = arcpy.CreateScratchName("streams", data_type="FeatureClass", workspace=arcpy.env.scratchGDB)
        scratch_points = arcpy.CreateScratchName("points", data_type="FeatureClass", workspace=arcpy.env.scratchGDB)

        # copy streams to scratch
        log("copy streams to scratch layer")
        arcpy.management.CopyFeatures(streams, scratch_streams)

        # simplify stream line
        log("simplifying stream line")
        arcpy.edit.Generalize(
            in_features=scratch_streams,
            tolerance="10 Meters", # TODO: consider making this a user options, really only needed to speed up processing
        )

        # line vertices to points
        log("converting line to points")
        arcpy.management.FeatureVerticesToPoints(
            in_features=scratch_streams,
            out_feature_class=scratch_points,
        )

        # IDW
        log("creating output width raster via interpolation")
        power = arcpy.sa.Idw(
            in_point_features=scratch_points,
            z_field=power_field,
        )

        # calculate unit stream power as power / width (m)
        log("calculating unit stream power")
        out = power / (width * conversion_factor)
        out.save(output_file)

        # add results to map
        log("adding results to map")
        distance_raster = active_map.addDataFromPath(output_file)

        # update raster symbology
        log("updating raster symbology")
        sym = distance_raster.symbology
        if hasattr(sym, 'colorizer'):
            if sym.colorizer.type != "RasterStretchColorizer":
                sym.updateColorizer("RasterStretchColorizer")
            sym.colorizer.colorRamp = project.listColorRamps("Red to Blue Diverging, Bright")[0]
            distance_raster.symbology = sym

        # save and exit program successfully
        log("saving project")
        project.save()

        # cleanup
        log("deleting unneeded data")
        empty_workspace(arcpy.env.scratchGDB, keep=[])
        empty_workspace(arcpy.env.scratchFolder, keep=[])
