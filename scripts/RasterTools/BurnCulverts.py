# --------------------------------------------------------------------------------
# Name:        Burn Culverts into DEM
# Purpose:     This tool hydro-conditions a DEM, specifically removing obstructions.
#
# License:     GNU Affero General Public License v3.
#              Full license in LICENSE file, or at <https://www.gnu.org/licenses/>
# --------------------------------------------------------------------------------

import arcpy

from helpers import license, get_oid, pixel_type
from helpers import print_messages as log
from helpers import setup_environment as setup
from helpers import validate_spatial_reference as validate

class BurnCulverts(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Burn Culverts into DEM"
        self.description = "Remove obstructions for flow direction"
        self.category = "Raster Tools"
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
            displayName="Culverts",
            name="culverts",
            datatype="GPFeatureLayer",
            parameterType="Required",
            direction="Input")
        param3.filter.list = ["Points"]
        param3.controlCLSID = '{60061247-BCA8-473E-A7AF-A2026DDE1C2D}' # allows point creation

        param4 = arcpy.Parameter(
            displayName="Search Distance (ft)",
            name="distance",
            datatype="GPDouble",
            parameterType="Required",
            direction="Input")

        params = [param0, param1, param2, param3, param4]
        return params

    def updateParameters(self, parameters):
        # default search distance
        if parameters[4].value == None:
            parameters[4].value = 50

    def isLicensed(self):
        """Set whether the tool is licensed to execute."""
        return license(['Spatial'])

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool parameter."""
        validate(parameters)
        return

    def execute(self, parameters, messages):
        """The source code of the tool."""
        # Setup
        log("setting up project")
        project, active_map = setup()

        # read in parameters
        raster_layer = parameters[0].value
        extent = parameters[1].value.polygon
        output_file = parameters[2].valueAsText
        culverts = parameters[3].value
        distance = parameters[4].value
        desc = arcpy.Describe(parameters[3].value)
        spatial_reference = desc.spatialReference
        env_path = r"{}".format(arcpy.env.workspace)

        # create scratch layers
        log("creating scratch layers")
        scratch_dem = "{}\\dem_clip".format(arcpy.env.workspace)
        scratch_culverts = arcpy.CreateScratchName("culverts", data_type="FeatureClass", workspace=arcpy.env.scratchFolder)
        scratch_culvert_upstream = arcpy.CreateScratchName("upstream", data_type="FeatureClass", workspace=arcpy.env.scratchFolder)
        scratch_culvert_downstream = arcpy.CreateScratchName("downstream", data_type="FeatureClass", workspace=arcpy.env.scratchFolder)
        scratch_points_merge = arcpy.CreateScratchName("merge", data_type="FeatureClass", workspace=arcpy.env.scratchFolder)
        scratch_streams = arcpy.management.CreateFeatureclass(env_path, "lines", "POLYLINE", spatial_reference=spatial_reference)
        scratch_stream_buffer = arcpy.CreateScratchName("buffer", data_type="FeatureClass", workspace=arcpy.env.scratchFolder)
        scratch_burned_raster = "{}\\burned".format(arcpy.env.workspace)
        scratch_mosaic_raster = "{}\\mosaic".format(arcpy.env.workspace)

        if extent:
            # clip DEM raster to analysis area
            log("clipping raster to analysis area")
            arcpy.management.Clip(raster_layer, extent, scratch_dem)
            raster_layer = scratch_dem

            # clip culverts to analysis area
            log("clipping culverts to analysis area")
            arcpy.analysis.Clip(culverts, extent, scratch_culverts)
            culverts = scratch_culverts

        # fill clipped raster
        log("finding point upstream of culvert")
        fill_raster = arcpy.sa.Fill(raster_layer)

        # subtract filled - clipped raster
        difference = fill_raster - raster_layer

        # snap culvert to max difference
        culverts_oid_field = get_oid(culverts)
        culvert_raster_upstream = arcpy.sa.SnapPourPoint(culverts, difference, "{} Feet".format(distance), culverts_oid_field)
        arcpy.conversion.RasterToPoint(culvert_raster_upstream, scratch_culvert_upstream, "Value") #culverts_oid_field gets set to Value instead of the field name mapped over

        # 0 - Fill
        log("finding point downstream of culvert")
        negative_elev = -fill_raster

        # snap culvert to lowest point
        culvert_raster_downstream = arcpy.sa.SnapPourPoint(culverts, negative_elev, "{} Feet".format(distance), culverts_oid_field)
        arcpy.conversion.RasterToPoint(culvert_raster_downstream, scratch_culvert_downstream, "Value")

        log("creating local streamlines")
        arcpy.management.Merge([scratch_culvert_upstream,scratch_culvert_downstream],scratch_points_merge)
        # iterate through points and make lines from them
        #
        # can't use builtin pointtoline becase we only have two points per line :(
        lines = []
        with arcpy.da.SearchCursor(scratch_points_merge, ["SHAPE@XY", "grid_code"], sql_clause=(None, "ORDER BY grid_code")) as points:
            point_dict = {}
            for point in points:
                x, y = point[0]
                num = point[1]

                pnt = arcpy.Point()
                pnt.X = x
                pnt.Y = y

                if num in point_dict:
                    point_dict[num].add(pnt)
                    geom = arcpy.Polyline(point_dict[num], spatial_reference)
                    lines.append(geom)
                else:
                    point_dict[num] = arcpy.Array(pnt)

        # add lines to scratch stream feature class
        with arcpy.da.InsertCursor(scratch_streams, ["SHAPE@"]) as streams:
            for line in lines:
                streams.insertRow([line])

        # buffer line to make streambed
        log("burning-in crossings")
        arcpy.analysis.PairwiseBuffer(scratch_streams, scratch_stream_buffer, "10 Feet")

        # Add field elev
        elevation_field = "elev"
        arcpy.management.AddField(scratch_stream_buffer, elevation_field, "DOUBLE")

        # set elev to 0
        with arcpy.da.UpdateCursor(scratch_stream_buffer, [elevation_field]) as cursor:
            for point in cursor:
                point[0] = 0
                cursor.updateRow(point)

        # polygon to raster
        arcpy.conversion.PolygonToRaster(scratch_stream_buffer,elevation_field,scratch_burned_raster)

        # mosaic to new raster
        #r = difference.getRasterInfo()
        #num_bands = r.getBandCount()
        #pixel_type = pixel_typer.getPixelType() 
        mosaic_raster = scratch_mosaic_raster.split("\\")[-1]
        arcpy.management.MosaicToNewRaster(
            input_rasters=[raster_layer,scratch_burned_raster],
            output_location=arcpy.env.workspace,
            pixel_type=pixel_type(difference.pixelType),
            number_of_bands=difference.bandCount,
            raster_dataset_name_with_extension=mosaic_raster,
            mosaic_method="LAST",
            mosaic_colormap_mode="FIRST"
        )

        # fill
        out_surface_raster = arcpy.sa.Fill(scratch_mosaic_raster, z_limit=None)
        out_surface_raster.save(output_file)

        # add raster to map
        log("adding hydro-conditioned DEM to map")
        active_map.addDataFromPath(output_file)

        # delete scratch layers
        log("cleaning up")
        arcpy.management.Delete([scratch_dem, scratch_culverts, scratch_culvert_upstream, scratch_culvert_downstream, scratch_points_merge, scratch_streams, scratch_stream_buffer, scratch_burned_raster, scratch_mosaic_raster])

        # save and exit program successfully
        log("saving project")
        project.save()

        return
