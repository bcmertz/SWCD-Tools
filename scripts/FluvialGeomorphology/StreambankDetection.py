# --------------------------------------------------------------------------------
# Name:        Streambank Detection
# Purpose:     This tool uses the ratio of REM and Hydraulic Radius to detect
#              where breaks in bank grade occur.
#
# License:     GNU Affero General Public License v3.
#              Full license in LICENSE file, or at <https://www.gnu.org/licenses/>
# --------------------------------------------------------------------------------
import arcpy

from ..helpers import license, empty_workspace, get_oid, reload_module, log, min_cell_path
from ..helpers import setup_environment as setup
from ..helpers import validate_spatial_reference as validate

class StreambankDetection:
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Streambank Detection"
        self.category = "Fluvial Geomorphology"
        self.description = "Detect streambanks from REM"

    def getParameterInfo(self):
        """Define parameter definitions"""
        param0 = arcpy.Parameter(
            displayName="Existing Stream Lines",
            name="stream",
            datatype="GPFeatureLayer",
            parameterType="Optional",
            direction="Input")
        param0.filter.list = ["Line"]
        param0.controlCLSID = '{60061247-BCA8-473E-A7AF-A2026DDE1C2D}' # allows line creation

        param1 = arcpy.Parameter(
            displayName="Analysis Area",
            name="analysis_area",
            datatype="GPExtent",
            parameterType="Optional",
            direction="Input")
        param1.controlCLSID = '{15F0D1C1-F783-49BC-8D16-619B8E92F668}'

        param2 = arcpy.Parameter(
            displayName="REM",
            name="rem",
            datatype="GPRasterLayer",
            parameterType="Required",
            direction="Input")

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
        streams = parameters[0].value
        extent = parameters[1].value
        rem_layer = parameters[2].value
        rem = arcpy.Raster(rem_layer.name)
        output_file = parameters[3].valueAsText

        # set cell size
        arcpy.env.cellSize = min_cell_path(parameters)

        # set analysis extent
        if extent:
            arcpy.env.extent = extent

        # create scratch layers
        log("creating scratch layers")
        scratch_area = arcpy.CreateScratchName("area", data_type="RasterDataset", workspace=arcpy.env.scratchGDB)

        # create distance raster
        log("calculating distance to stream centerlines")
        distance = arcpy.sa.DistanceAccumulation(
            in_source_data=streams,
            distance_method="GEODESIC"
        )

        # smooth irregularities in streambed
        # TODO: low pass filter?
        log("smoothing streambed")
        sql_query = "VALUE < 0.25" # TODO: find something more reasonable
        con_rem = arcpy.sa.Con(rem, 0, rem, sql_query)

        # create distance cost raster "hydraulic area"
        # not actually hydraulic area since its the area under the curve not the area above the curve
        log("calculating hydraulic area")
        arcpy.sa.DistanceAllocation(
            in_source_data=streams,
            in_cost_raster=con_rem,
            out_distance_accumulation_raster=scratch_area,
            source_field=get_oid(streams),
            distance_method="GEODESIC"
        )

        # calculate output
        log("calculating relationship between height above thalweg and hydraulic depth")
        output = (rem * distance)/(scratch_area - rem)
        output.save(output_file)

        # add output to map
        log("adding output to map")
        output_layer = active_map.addDataFromPath(output_file)

        # update raster symbology
        log("updating output symbology")
        min_value = 0
        max_value = 25
        sym = output_layer.symbology
        if hasattr(sym, 'colorizer'):
            if sym.colorizer.type != "RasterStretchColorizer":
                sym.updateColorizer("RasterStretchColorizer")
            sym.colorizer.stretchType = "MinimumMaximum"
            sym.colorizer.minLabel = "{}".format(min_value)
            sym.colorizer.maxLabel = "{}".format(max_value)
            output_layer.symbology = sym
        cim_layer = output_layer.getDefinition("V3")
        cim_layer.colorizer.statsType = 'GlobalStats'
        #cim_layer.colorizer.useCustomStretchMinMax = True
        cim_layer.colorizer.customStretchMin = min_value
        cim_layer.colorizer.customStretchMax = max_value
        cim_layer.colorizer.stretchStats.max = max_value
        cim_layer.colorizer.stretchStats.min = min_value
        output_layer.setDefinition(cim_layer)


        # cleanup
        log("deleting unneeded data")
        empty_workspace(arcpy.env.scratchGDB)

        # save program successfully
        log("saving project")
        project.save()

        return
