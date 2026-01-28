# --------------------------------------------------------------------------------
# Name:        Relative Elevation Model (REM)
# Purpose:     This tool creates an REM from a DEM and streamline. This can be used
#              for modeling stream incision, geomorphic features, and other uses.
#
# License:     GNU Affero General Public License v3.
#              Full license in LICENSE file, or at <https://www.gnu.org/licenses/>
# --------------------------------------------------------------------------------

import arcpy

from ..helpers import license, empty_workspace, reload_module, log
from ..helpers import setup_environment as setup
from ..helpers import validate_spatial_reference as validate

class RelativeElevationModel(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Relative Elevation Model (REM)"
        self.description = "Compute REM"
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
            displayName="Analysis Area",
            name="analysis_area",
            datatype="GPExtent",
            parameterType="Optional",
            direction="Input")
        param1.controlCLSID = '{15F0D1C1-F783-49BC-8D16-619B8E92F668}'

        param2 = arcpy.Parameter(
            displayName="Output Features",
            name="out_features",
            datatype="DEFeatureClass",
            parameterType="Required",
            direction="Output")
        param2.parameterDependencies = [param0.name]
        param2.schema.clone = True

        param3 = arcpy.Parameter(
            displayName="Stream Feature Class",
            name="streams",
            datatype="GPFeatureLayer",
            parameterType="Required",
            direction="Input")
        param3.filter.list = ["Polyline"]
        param3.controlCLSID = '{60061247-BCA8-473E-A7AF-A2026DDE1C2D}' # allows line creation

        param4 = arcpy.Parameter(
            displayName="Buffer Radius",
            name="buffer_radius",
            datatype="GPLinearUnit",
            parameterType="Optional",
            direction="Input")

        param5 = arcpy.Parameter(
            displayName="Sampling Interval",
            name="sampling_interval",
            datatype="GPLinearUnit",
            parameterType="Optional",
            direction="Input")

        params = [param0, param1, param2, param3, param4, param5]
        return params

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool parameter."""
        validate(parameters)
        return

    def isLicensed(self):
        """Set whether the tool is licensed to execute."""
        return license(['Spatial'])

    def updateParameters(self, parameters):
        # default buffer radius
        if parameters[4].value is None:
            parameters[4].value = "100 Feet"
        # default simpling interval
        if parameters[5].value is None:
            parameters[5].value = "25 Feet"
        return

    @reload_module(__name__)
    def execute(self, parameters, messages):
        """The source code of the tool."""
        # Setup
        log("setting up project")
        project, active_map = setup()

        # read in parameters
        dem_raster = parameters[0].value
        extent = parameters[1].value
        output_file = parameters[2].valueAsText
        stream_layer = parameters[3].value
        buffer_radius = parameters[4].valueAsText
        sampling_interval = parameters[4].valueAsText

        # set analysis extent
        if extent:
            arcpy.env.extent = extent

        # create scratch layers
        log("creating scratch layers")
        scratch_stream_layer = arcpy.CreateScratchName("scratch_stream_layer", "FeatureClass", arcpy.env.scratchGDB)
        scratch_stream_buffer = arcpy.CreateScratchName("scratch_stream_buffer", "FeatureClass", arcpy.env.scratchGDB)
        scratch_stream_points = arcpy.CreateScratchName("scratch_stream_points", "FeatureClass", arcpy.env.scratchGDB)
        scratch_stream_elev_points = arcpy.CreateScratchName("scratch_stream_elev_points", "FeatureClass", arcpy.env.scratchGDB)

        if extent:
            # clip streams to analysis area
            log("clipping stream centerline to analysis area")
            arcpy.analysis.Clip(stream_layer, extent.polygon, scratch_stream_layer)
        else:
            scratch_stream_layer = stream_layer

        # pairwise buffer stream
        # can't do flat end caps using analysis buffer tool instead because a sinousoidal stream will create heavy artifacts in the buffer
        log("creating buffer polygon around stream")
        arcpy.analysis.PairwiseBuffer(scratch_stream_layer, scratch_stream_buffer, buffer_radius, "ALL", "", "GEODESIC", "")

        # clip dem to buffer
        log("clipping DEM to buffer")
        dem_raster_clip = arcpy.sa.ExtractByMask(dem_raster, scratch_stream_buffer, "INSIDE", "MINOF")

        # generate points along line
        log("generating points along stream")
        arcpy.management.GeneratePointsAlongLines(scratch_stream_layer, scratch_stream_points, "DISTANCE", sampling_interval, "", "END_POINTS", "NO_CHAINAGE")

        # extract values to points
        log("adding elevation data to stream line points")
        arcpy.sa.ExtractValuesToPoints(scratch_stream_points, dem_raster_clip, scratch_stream_elev_points, "NONE", "VALUE_ONLY")

        # IDW (to buffer extent)
        log("calculating IDW raster")
        arcpy.env.cellSize = dem_raster_clip
        arcpy.env.extent = scratch_stream_buffer
        idw_raster = arcpy.sa.Idw(scratch_stream_elev_points, "RASTERVALU", "", "", "", "")

        # raster calculator (DEM - IDW_new)
        log("calculating relative elevation difference")
        relative_elevation = arcpy.CreateUniqueName(output_file)
        out_rem = arcpy.sa.RasterCalculator([dem_raster_clip,idw_raster],["x","y"],"x-y", "FirstOf", "FirstOf")
        out_rem.save(relative_elevation)

        # add results to map
        log("adding results to map")
        rem_raster = active_map.addDataFromPath(out_rem)

        # update raster symbology
        log("updating raster symbology")
        min_value = 0
        max_value = 4
        sym = rem_raster.symbology
        if hasattr(sym, 'colorizer'):
            if sym.colorizer.type != "RasterStretchColorizer":
                sym.updateColorizer("RasterStretchColorizer")
            sym.colorizer.stretchType = "MinimumMaximum"
            sym.colorizer.colorRamp = project.listColorRamps('Spectrum By Wavelength-Full Bright')[0]
            sym.colorizer.minLabel = "{}".format(min_value)
            sym.colorizer.maxLabel = "{}".format(max_value)
            rem_raster.symbology = sym
        cim_layer = rem_raster.getDefinition("V3")
        cim_layer.colorizer.statsType = 'GlobalStats'
        #cim_layer.colorizer.useCustomStretchMinMax = True
        cim_layer.colorizer.customStretchMin = min_value
        cim_layer.colorizer.customStretchMax = max_value
        cim_layer.colorizer.stretchStats.max = max_value
        cim_layer.colorizer.stretchStats.min = min_value
        rem_raster.setDefinition(cim_layer)

        # cleanup
        log("deleting unneeded data")
        empty_workspace(arcpy.env.scratchGDB, keep=[])

        # save project
        log("saving project")
        project.save()

        return
