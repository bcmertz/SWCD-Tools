# --------------------------------------------------------------------------------
# Name:        Dam Removal
# Purpose:     This tool removes the footprint of a dam from a DEM and estimates
#              the ground surface beneath the currently inundated area.
#
# License:     GNU Affero General Public License v3.
#              Full license in LICENSE file, or at <https://www.gnu.org/licenses/>
# --------------------------------------------------------------------------------

import arcpy
from math import atan2, pi

from helpers import license, pixel_type, get_linear_unit, empty_workspace
from helpers import print_messages as log
from helpers import setup_environment as setup
from helpers import validate_spatial_reference as validate

class DamRemoval(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Dam Removal"
        self.description = "Dam Removal"
        self.category = "Wetland Tools"
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
            displayName="Pond Centerline",
            name="centerline",
            datatype="GPFeatureLayer",
            parameterType="Required",
            direction="Input")
        param3.filter.list = ["Polyline"]
        param3.controlCLSID = '{60061247-BCA8-473E-A7AF-A2026DDE1C2D}' # allows line creation

        param4 = arcpy.Parameter(
            displayName="Ponded Area + Berm",
            name="pond",
            datatype="GPFeatureLayer",
            parameterType="Required",
            direction="Input")
        param4.filter.list = ["Polygon"]
        param4.controlCLSID = '{60061247-BCA8-473E-A7AF-A2026DDE1C2D}' # allows polygon creation

        param5 = arcpy.Parameter(
            displayName="Transect Spacing",
            name="transect_spacing",
            datatype="GPLinearUnit",
            parameterType="Required",
            direction="Input")

        param6 = arcpy.Parameter(
            displayName="Transect Point Spacing",
            name="transect_point_spacing",
            datatype="GPLinearUnit",
            parameterType="Required",
            direction="Input")

        param7 = arcpy.Parameter(
            displayName="Transect Width",
            name="transect_width",
            datatype="GPLinearUnit",
            parameterType="Required",
            direction="Input")

        params = [param0, param1, param2, param3, param4, param5, param6, param7]
        return params

    def updateParameters(self, parameters):
        # default transect spacing
        if parameters[5].value == None:
            parameters[5].value = "50 FeetUS"

        # default transect point spacing
        if parameters[6].value == None:
            parameters[6].value = "10 FeetUS"

        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool parameter."""
        validate(parameters)
        return

    def isLicensed(self):
        """Set whether the tool is licensed to execute."""
        return license(['Spatial'])

    def transectLine(self, stream_line, stream_vertex, transect_width):
        '''returns a transect to stream_line of length transect_width at stream_vertex point
        stream_line - arcpy.PolyLine() object
        stream_vertex - arcpy.Point() object
        transect_width - distance in meters of transect
        '''
        # epsilon
        e = 1e-5

        # get stream vertex
        stream_vertex = stream_line.queryPointAndDistance(stream_vertex, False)
        geom = stream_vertex[0]
        distance = stream_vertex[1]
        spatial_reference = stream_line.spatialReference

        # get points immediately before and after midpoint
        before = stream_line.positionAlongLine(distance-e, False)
        after = stream_line.positionAlongLine(distance+e, False)

        dX = after[0].X - before[0].X
        dY = after[0].Y - before[0].Y

        # angle of the midpoint segment
        angle = atan2(dX,dY) * 180 / pi

        first_tran_point = geom.pointFromAngleAndDistance(angle - 90, transect_width/2)
        last_tran_point = geom.pointFromAngleAndDistance(angle + 90, transect_width/2)
        dX = first_tran_point.firstPoint.X - last_tran_point.firstPoint.X
        dY = first_tran_point.firstPoint.Y - last_tran_point.firstPoint.Y

        transect = arcpy.Polyline(arcpy.Array((first_tran_point.firstPoint, last_tran_point.firstPoint)), spatial_reference, has_id=True)
        return transect


    def interpolateElevations(self, transect, dem_raster, lowpoint_elev, transect_width, transect_point_spacing, transect_point_spacing_unit, scratch_transect_points, scratch_transect_elev_points):
        '''return points along transect with elevations
        transect - arcpy.PolyLine() object
        dem_raster - elevation raster
        lowpoint_elev - elevation of streamline, considered lowpoint of constructed surface
        transect_width - width of transect
        transect_point_spacing - spacing between points on transect
        transect_point_spacing_unit - unit of transect point spacing
        scratch_transect_points - scratch layer for transect points
        scratch_transect_elev_points - scratch layer for transect points with elevations
        '''
        arcpy.management.GeneratePointsAlongLines(transect, scratch_transect_points, "DISTANCE", "{} {}".format(transect_point_spacing, transect_point_spacing_unit), "", "END_POINTS", "ADD_CHAINAGE")
        arcpy.sa.ExtractValuesToPoints(scratch_transect_points, dem_raster, scratch_transect_elev_points, "NONE", "VALUE_ONLY")

        # iterate through transect points
        # collect new points to add and interpolate elevations along them
        num_points = (not not transect_width % transect_point_spacing) + int(transect_width / transect_point_spacing) + 1
        slope = elev_start = elev_end = distance_start = distance_end = elev_prev = distance_prev = None
        new_points = []
        with arcpy.da.SearchCursor(scratch_transect_elev_points, ["SHAPE@", "RASTERVALU", "ORIG_LEN"]) as cursor:
            update_points = []
            idx = 0
            for point in cursor:
                elev, distance = point[1], point[2]
                point = list(point)
                # if middle streampoint, use elevation of streamline
                if idx == (num_points - 1) / 2:
                    elev = lowpoint_elev
                    point[1] = elev

                if elev == -9999:
                    # start of unknown section
                    if elev_prev != -9999:
                        elev_start = elev_prev
                        distance_start = distance_prev
                    update_points.append(point)
                else:
                    # found end of unknown elevation data
                    if elev_prev == -9999:
                        # end of unknown section
                        elev_end = elev
                        distance_end = distance

                    # add interpolated points to list of points to be added to DEM
                    if elev_start != None and elev_end != None:
                        slope = (elev_end - elev_start)/(distance_end - distance_start)
                        for i in update_points:
                            i[1] = slope * (i[2] - distance_start) + elev_start
                            new_points.append(tuple(i))

                        elev_start = elev_end
                        distance_start = distance_end
                        elev_end = None
                        distance_end = None
                        update_points = []

                    # add known elevation point to points to return
                    new_points.append(list(point))

                elev_prev = elev
                distance_prev = distance
                idx += 1
        return new_points

    def execute(self, parameters, messages):
        """The source code of the tool."""
        # Setup
        log("setting up project")
        project, active_map = setup()

        dem_layer = parameters[0].value
        dem = arcpy.Raster(dem_layer.name)
        dem_symbology = dem_layer.symbology
        extent = parameters[1].value
        output_file = parameters[2].valueAsText
        centerline = parameters[3].value
        linear_unit = get_linear_unit(centerline)
        pond = parameters[4].value
        transect_spacing = parameters[5].valueAsText
        transect_point_spacing, transect_point_spacing_unit = parameters[6].valueAsText.split(" ")
        transect_point_spacing = float(transect_point_spacing) * arcpy.LinearUnitConversionFactor(transect_point_spacing_unit, linear_unit)
        transect_width, transect_width_unit = parameters[7].valueAsText.split(" ")
        transect_width = float(transect_width) * arcpy.LinearUnitConversionFactor(transect_width_unit, linear_unit)

        # create scratch layers
        scratch_centerline = arcpy.CreateScratchName("scratch_centerline", data_type="FeatureClass", workspace=arcpy.env.scratchGDB)
        scratch_centerline_points = arcpy.CreateScratchName("scratch_centerline_points", data_type="FeatureClass", workspace=arcpy.env.scratchGDB)
        scratch_centerline_elev_points = arcpy.CreateScratchName("scratch_centerline_elev_points", data_type="FeatureClass", workspace=arcpy.env.scratchGDB)
        scratch_point_raster = arcpy.CreateScratchName("point_raster", data_type="RasterDataset", workspace=arcpy.env.scratchGDB)
        scratch_transect_points = arcpy.CreateScratchName("scratch_transect_points", data_type="FeatureClass", workspace=arcpy.env.scratchGDB)
        scratch_transect_elev_points = arcpy.CreateScratchName("scratch_transect_elev_points", data_type="FeatureClass", workspace=arcpy.env.scratchGDB)
        scratch_mosaic_raster = arcpy.CreateScratchName("mosaic_ras", data_type="RasterDataset", workspace=arcpy.env.scratchGDB)

        if extent:
            # set analysis extent
            arcpy.env.extent = extent

            # clip streams to analysis area
            log("clipping stream centerline to analysis area")
            arcpy.analysis.Clip(centerline, extent.polygon, scratch_centerline)
        else:
            scratch_centerline = centerline

        # extract by mask to remove pond from dem
        log("removing ponded area from dem")
        dem_pondless = arcpy.sa.ExtractByMask(dem, pond, "OUTSIDE")

        # generate points along line
        log("generating points along centerline")
        arcpy.management.GeneratePointsAlongLines(scratch_centerline, scratch_centerline_points, "DISTANCE", transect_spacing, "", "END_POINTS", "ADD_CHAINAGE")

        # extract values to points
        log("adding elevation data to centerline points")
        arcpy.sa.ExtractValuesToPoints(scratch_centerline_points, dem_pondless, scratch_centerline_elev_points, "NONE", "VALUE_ONLY")

        # iterate through centerline points
        log("finding known centerline points")
        slope = elev_high = elev_low = distance_high = distance_low = elev_prev = distance_prev = None
        with arcpy.da.SearchCursor(scratch_centerline_elev_points, ["RASTERVALU", "ORIG_LEN"]) as cursor:
            for point in cursor:
                if elev_high != None and elev_low != None:
                    break
                elev, distance = point[0], point[1]
                if elev_prev != None:
                    if elev == -9999 and elev_prev != -9999:
                        # elev low
                        elev_low = elev_prev
                        distance_low = distance_prev
                    elif elev != -9999 and elev_prev == -9999:
                        # elev high
                        elev_high = elev
                        distance_high = distance
                elev_prev = elev
                distance_prev = distance

        # calculate slope between known points
        log("calculating centerline slope")
        slope = (elev_high - elev_low)/(distance_high - distance_low)

        # iterate and add elevations to unknown points
        log("inferring unknown point elevations along centerline")
        with arcpy.da.UpdateCursor(scratch_centerline_elev_points, ["RASTERVALU", "ORIG_LEN"]) as cursor:
            for point in cursor:
                elev, distance = point[0], point[1]
                if elev == -9999:
                    point[0] = slope * (distance - distance_low) + elev_low
                cursor.updateRow(point)

        # do we still need this mosaic? A - no, we can just pass the elevation
        # Points to Raster
        log("creating raster from new points")
        arcpy.conversion.PointToRaster(scratch_centerline_elev_points, "RASTERVALU", scratch_point_raster, cellsize=3)

        # Mosaic dem_pondless, raster_points
        log("mosaic to new raster")
        dem_pondless_raster = arcpy.Raster(dem_pondless)
        mosaic_raster = scratch_mosaic_raster.split("\\")[-1]
        arcpy.management.MosaicToNewRaster(
            input_rasters=[dem_pondless, scratch_point_raster],
            output_location=arcpy.env.workspace,
            raster_dataset_name_with_extension=mosaic_raster,
            pixel_type=pixel_type(dem_pondless_raster),
            number_of_bands=dem_pondless_raster.bandCount,
            mosaic_method="LAST",
            mosaic_colormap_mode="FIRST"
        )

        # get polyline from centerline for use in transects
        # note - doesn't support multiple centerlines in fc
        log("getting stream centerline")
        centerline_polyline = None
        with arcpy.da.SearchCursor(centerline, ["SHAPE@"]) as cursor:
            centerline_polyline = cursor[0][0]

        # iterate through each point
        # impove point density with transects using the new mosaic
        log("creating transects and interpolating elevations")
        new_points = []
        with arcpy.da.SearchCursor(scratch_centerline_elev_points, ["SHAPE@", "RASTERVALU", "ORIG_LEN"]) as cursor:
            for point in cursor:
                # read in values
                shape, elev, distance = point[0], point[1], point[2]
                # create transect
                transect = self.transectLine(centerline_polyline, shape, transect_width)
                # interpolate elevations
                tmp_points = self.interpolateElevations(transect, mosaic_raster, elev, transect_width, transect_point_spacing, transect_point_spacing_unit, scratch_transect_points, scratch_transect_elev_points)
                # add points to list of new points
                new_points = new_points + tmp_points

        # add points to final point fc
        log("adding interpolated points to fc")
        scratch_final_idw_points = arcpy.management.CreateFeatureclass(arcpy.env.scratchGDB, "scratch_final_idw_points", "POINT", scratch_centerline_elev_points)
        with arcpy.da.InsertCursor(scratch_final_idw_points, ["SHAPE@", "RASTERVALU", "ORIG_LEN"]) as cursor:
            for point in new_points:
                cursor.insertRow(point)

        # IDW or Global Polynomial Interpolation
        ## depends whether we want to IDW points (must include all points then) or want to fill in DEM and interpolate voids
        log("performing IDW analysis on interpolated points")
        idw_raster = arcpy.sa.Idw(scratch_final_idw_points, "RASTERVALU")

        # extract by mask
        log("extracting ponded area from IDW raster")
        raster_output = arcpy.sa.ExtractByMask(idw_raster, pond, "INSIDE")
        raster_output.save(output_file)

        # add results to map
        log("adding results to map")
        rem_raster = active_map.addDataFromPath(output_file)

        # update raster symbology
        log("updating raster symbology")
        rem_raster.symbology = dem_symbology

        # cleanup
        log("deleting unneeded data")
        empty_workspace(arcpy.env.scratchGDB, keep=[])

        # save project
        log("saving project")
        project.save()

        return
