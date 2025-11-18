import arcpy

from arcpy import env

# setup helpers
import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), "../helpers"))
from print_messages import print_messages as log
from setup_environment import setup_environment as setup

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
            parameterType="Required",
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

        param4 = arcpy.Parameter(
            displayName="Buffer Radius (ft)",
            name="buffer_radius",
            datatype="GPDouble",
            parameterType="Optional",
            direction="Input")

        param5 = arcpy.Parameter(
            displayName="Sampling Interval (ft)",
            name="sampling_interval",
            datatype="GPDouble",
            parameterType="Optional",
            direction="Input")
        
        
        params = [param0, param1, param2, param3, param4, param5]
        return params
    
    def updateParameters(self, parameters):
        # default buffer radius
        if parameters[4].value == None:
            parameters[4].value = 100
        # default simpling interval
        if parameters[5].value == None:
            parameters[5].value = 25
        return
    
    def execute(self, parameters, messages):
        """The source code of the tool."""
        # Setup
        log("setting up project")
        project, active_map = setup()
        arcpy.env.parallelProcessingFactor = "75%"

        dem_raster = parameters[0].value
        XMin = parameters[1].value.XMin
        YMin = parameters[1].value.YMin
        XMax = parameters[1].value.XMax
        YMax = parameters[1].value.YMax
        extent = arcpy.Extent(XMin, YMin, XMax, YMax)
        extent.spatialReference = parameters[1].value.spatialReference
        output_file = parameters[2].valueAsText
        stream_layer = parameters[3].value
        buffer_radius = int(parameters[4].value)
        sampling_interval = int(parameters[5].value)

        # create area to process from extent
        log("creating area from extent")
        pnt1 = arcpy.Point(XMin, YMin)
        pnt2 = arcpy.Point(XMin, YMax)
        pnt3 = arcpy.Point(XMax, YMax)
        pnt4 = arcpy.Point(XMax, YMin)
        array = arcpy.Array()
        array.add(pnt1)
        array.add(pnt2)
        array.add(pnt3)
        array.add(pnt4)
        array.add(pnt1)
        polygon = arcpy.Polygon(array)

        # clip streams to analysis area
        log("clipping stream centerline to analysis area")
        scratch_stream_layer = arcpy.CreateScratchName("scratch_stream_layer",
                                               data_type="FeatureClass",
                                               workspace=arcpy.env.scratchFolder)
        arcpy.analysis.Clip(stream_layer, polygon, scratch_stream_layer)

        # pairwise buffer stream
        # can't do flat end caps using analysis buffer tool instead because a sinousoidal stream will create heavy artifacts in the buffer
        log("creating buffer polygon around stream")
        scratch_stream_buffer = arcpy.CreateScratchName("scratch_stream_buffer",
                                               data_type="FeatureClass",
                                               workspace=arcpy.env.scratchFolder)          
        arcpy.analysis.PairwiseBuffer(scratch_stream_layer, scratch_stream_buffer, " Feet".format(buffer_radius), "ALL", "", "GEODESIC", "")

        # clip dem to buffer
        log("clipping DEM to buffer")
        dem_raster_clip = "{}\\dem_raster_clip".format(arcpy.env.workspace)
        # OLD CODE - slower (https://www.reddit.com/r/gis/comments/17act1u/comment/k5ddrpx/?utm_source=share&utm_medium=web3x&utm_name=web3xcss&utm_term=1&utm_content=share_button)
        out_raster_clip = arcpy.sa.ExtractByMask(dem_raster, scratch_stream_buffer, "INSIDE", "MINOF")
        out_raster_clip.save(dem_raster_clip)      
        # other method - doesn't restrict raster to shape
        #arcpy.management.Clip(dem_raster, scratch_stream_buffer, dem_raster_clip)


        # generate points along line
        log("generating points along stream")
        scratch_stream_points = arcpy.CreateScratchName("scratch_stream_points",
                                               data_type="FeatureClass",
                                               workspace=arcpy.env.scratchFolder)          
        arcpy.management.GeneratePointsAlongLines(scratch_stream_layer, scratch_stream_points, "DISTANCE", sampling_interval, "", "END_POINTS", "NO_CHAINAGE")
        
        # extract values to points
        log("adding elevation data to stream line points")
        scratch_stream_elev_points = arcpy.CreateScratchName("scratch_stream_elev_points",
                                               data_type="FeatureClass",
                                               workspace=arcpy.env.scratchFolder)          
        arcpy.sa.ExtractValuesToPoints(scratch_stream_points, dem_raster_clip, scratch_stream_elev_points, "NONE", "VALUE_ONLY")

        # IDW (to buffer extent)
        idw_raster = "{}\\idw_raster".format(arcpy.env.workspace)
        log("setting spatial processing environmental variables")
        arcpy.env.cellSize = dem_raster_clip
        arcpy.env.extent = scratch_stream_buffer
        log("calculating IDW raster")
        outIDW = arcpy.sa.Idw(scratch_stream_elev_points, "RASTERVALU", "", "", "", "")
        outIDW.save(idw_raster)

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

        log("setting custom raster statistics for a use minimum and maximum relative elevation")
        cim_layer = rem_raster.getDefinition("V3")
        cim_layer.colorizer.statsType = 'GlobalStats'
        #cim_layer.colorizer.useCustomStretchMinMax = True
        cim_layer.colorizer.customStretchMin = min_value
        cim_layer.colorizer.customStretchMax = max_value
        cim_layer.colorizer.stretchStats.max = max_value
        cim_layer.colorizer.stretchStats.min = min_value
        rem_raster.setDefinition(cim_layer)

        # delete scratch variables
        log("deleting unneeded data")
        arcpy.management.Delete(dem_raster_clip)
        arcpy.management.Delete(idw_raster)
        arcpy.management.Delete([scratch_stream_layer, scratch_stream_buffer,scratch_stream_points,scratch_stream_elev_points])

        # save project
        log("saving project")
        project.save()

        return
