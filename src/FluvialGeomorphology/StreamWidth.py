# --------------------------------------------------------------------------------
# Name:        Stream Width
# Purpose:     This tool creates a raster represnting the width of an input polygon.
#
# License:     Contextual Copyleft AI (CCAI) License v1.0.
#              Full license in LICENSE file.
# --------------------------------------------------------------------------------
import arcpy
import numpy as np
from osgeo import gdal

from helpers.logging import log
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
from helpers.units import Distance


class StreamWidth:
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Stream Width"
        self.description = "Calculate stream width raster"
        self.category = "Fluvial Geomorphology"

    def getParameterInfo(self):
        """Define parameter definitions"""
        param0 = arcpy.Parameter(
            displayName="Stream Polygon",
            name="stream",
            datatype="GPFeatureLayer",
            parameterType="Optional",
            direction="Input")
        param0.filter.list = ["Polygon"]
        param0.controlCLSID = '{60061247-BCA8-473E-A7AF-A2026DDE1C2D}' # allows polygon creation

        param1 = arcpy.Parameter(
            displayName="Analysis Area",
            name="analysis_area",
            datatype="GPExtent",
            parameterType="Optional",
            direction="Input")
        param1.controlCLSID = '{15F0D1C1-F783-49BC-8D16-619B8E92F668}'

        param2 = arcpy.Parameter(
            displayName="Minimum stream width",
            name="threshold",
            datatype="GPLinearUnit",
            parameterType="Optional",
            direction="Input")

        param3 = arcpy.Parameter(
            displayName="Output Features",
            name="out_features",
            datatype="DEFeatureClass",
            direction="Output")
        param3.parameterDependencies = [param0.name]
        param3.schema.clone = True

        params = [param0, param1, param2, param3]
        return params

    def updateParameters(self, _parameters):
        return

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
        spatial_reference = active_map.spatialReference

        # read in parameters
        stream_polygon = parameters[0].valueAsText
        extent = parameters[1].value
        min_stream_radius = Distance(parameters[2].valueAsText) / 2 # width to radius
        output_file = parameters[3].valueAsText

        # set analysis extent
        if extent:
            arcpy.env.extent = extent

        # create scratch layers
        log("creating scratch layers")
        scratch_stream_lines = arcpy.CreateScratchName("lines", data_type="FeatureClass", workspace=arcpy.env.scratchGDB)
        scratch_distance = arcpy.CreateScratchName("distance", data_type="RasterDataset", workspace=arcpy.env.scratchFolder)
        scratch_points = arcpy.CreateScratchName("points", data_type="FeatureClass", workspace=arcpy.env.scratchGDB)

        # mask to polygon
        log("masking analysis to stream polygon")
        arcpy.env.mask = stream_polygon

        # polygon to line
        log("converting polygon to line feature")
        arcpy.management.PolygonToLine(stream_polygon, scratch_stream_lines)

        # distance accumulation
        log("finding distances to edge")
        distance_raster = arcpy.sa.DistanceAccumulation(
            in_source_data=scratch_stream_lines,
            distance_method="GEODESIC"
        )
        distance_raster.save(scratch_distance)

        # access size of file
        log("opening raster")
        ds = gdal.Open(scratch_distance)

        # calculate pixel size
        log("calculating pixel size")
        width = ds.RasterXSize
        height = ds.RasterYSize
        geotransform = ds.GetGeoTransform()
        pixelWidth = abs(geotransform[1])
        pixelHeight = abs(geotransform[5])
        pixelSize = (pixelWidth + pixelHeight) / 2

        # keep track of center vertices and widths
        log("calculating circle radius")
        linear_unit = get_linear_unit(scratch_distance)
        min_circle_size = min_stream_radius.to_unit(linear_unit).length

        # find the largest width, fill it with a circle of 1.5 * radius of the width
        # iterate, ignoring previously filled areas, until there are no distances left
        # >= the narrowest polygon width according to the user
        log("polygon width analysis")
        centers = []
        radius = min_circle_size
        mask = None
        while radius >= min_circle_size:
            if mask is not None:
                radius, x, y = raster_max_coordinates(scratch_distance, mask)
                center = (x, y)
                centers.append((center, radius * 2))
                mask = np.logical_or(mask, circular_mask(width, height, radius * 1.5 / pixelSize, coordinate_to_pixel(ds, x, y)))
            else:
                radius, x, y = raster_max_coordinates(scratch_distance)
                center = (x, y)
                centers.append((center, radius * 2))
                mask = circular_mask(width, height, radius * 1.5 / pixelSize, coordinate_to_pixel(ds, x, y))


        # create a numpy array with a tuple of x,y coordinates and a radius field
        log("converting point data to feature class")
        radius_field = "radius"
        array = np.array(centers, np.dtype([("XY", "<f8", 2), (radius_field, np.float64)]))
        arcpy.da.NumPyArrayToFeatureClass(array, scratch_points, ["XY"], spatial_reference)

        # IDW
        log("creating output width raster via interpolation")
        out_raster = arcpy.sa.Idw(
            in_point_features=scratch_points,
            z_field=radius_field,
            cell_size=str(cell_length(scratch_distance).length),
            power="4",
            search_radius="VARIABLE 6",
        )
        out_raster.save(output_file)

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
