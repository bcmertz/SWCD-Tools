# --------------------------------------------------------------------------------
# Name:        Stream Network
# Purpose:     This tool creates a stream network from a DEM, clipped to the extent
#              of a supplied stream layer
#
# License:     Contextual Copyleft AI (CCAI) License v1.0.
#              Full license in LICENSE file.
# --------------------------------------------------------------------------------
import os

import arcpy

from helpers.features import find_field, is_empty
from helpers.layers import get_oid
from helpers.logging import error, log
from helpers.parameter import raster_and_layer, set_required_parameter
from helpers.parameter import validate_spatial_reference as validate
from helpers.rasters import cell_area
from helpers.tool import (
    EXTENSIONS,
    empty_workspace,
    license,
    reload_module,
)
from helpers.tool import setup_environment as setup
from helpers.units import AREAL_UNITS, SPATIAL_UNITS, Area, Distance, get_linear_unit, get_z_unit
from Hydrology import STREAM_STATS_FIELD_MAPPING, calculate_statistics


class StreamNetwork:
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Calculate Stream Network"
        self.description = "Create stream network from DEM"
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

        # Note: this could be accomplished with a composite parameter, however
        # composite parameters don't have a way to introspect in updateParameters
        # what the user has toggled the composite parameter to as the dataType
        # we need that functionality in order to set defaults and controlCLSID's
        param3 = arcpy.Parameter(
            displayName="Stream Initiation Point Data Source",
            name="toggle",
            datatype="GPString",
            parameterType="Required",
            direction="Input")
        param3.filter.list = ["Existing Stream Lines", "Watershed Size Threshold"]

        param4 = arcpy.Parameter(
            displayName="Existing Stream Lines",
            name="stream",
            datatype="GPFeatureLayer",
            parameterType="Optional",
            direction="Input")
        param4.filter.list = ["Polyline"]
        param4.controlCLSID = '{60061247-BCA8-473E-A7AF-A2026DDE1C2D}' # allows line creation

        param5 = arcpy.Parameter(
            displayName="Watershed Size Threshold",
            name="threshold",
            datatype="GPArealUnit",
            parameterType="Optional",
            direction="Input")

        param6 = arcpy.Parameter(
            displayName="Fields to keep",
            name="keep",
            datatype="GPString",
            parameterType="Optional",
            multiValue="True",
            direction="Input")
        param6.filter.type = "ValueList"
        param6.filter.list = []

        param7 = arcpy.Parameter(
            displayName="Statistics to calculate",
            name="fields",
            datatype="GPString",
            parameterType="Optional",
            multiValue=True,
            direction="Input")
        param7.filter.list = ["Slope", "Watershed Size"] + list(STREAM_STATS_FIELD_MAPPING.keys())
        param7.value = ["Slope", "Watershed Size"]

        param8 = arcpy.Parameter(
            displayName="Watershed Size Output Unit",
            name="unit",
            datatype="GPString",
            parameterType="Optional",
            direction="Input")
        param8.filter.list = list(AREAL_UNITS)
        param8.value = AREAL_UNITS.SquareMilesUS

        param9 = arcpy.Parameter(
            displayName="Output Features",
            name="out_features",
            datatype="DEFeatureClass",
            parameterType="Required",
            direction="Output")
        param9.parameterDependencies = [param0.name]
        param9.schema.clone = True

        params = [param0, param1, param2, param3, param4, param5, param6, param7, param8, param9]
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


        # toggle initiation data source
        if not parameters[3].hasBeenValidated:
            if parameters[3].valueAsText == "Existing Stream Lines":
                parameters[4].enabled = True
                parameters[5].enabled = False
                parameters[5].value = None
            elif parameters[3].valueAsText == "Watershed Size Threshold":
                parameters[4].enabled = False
                parameters[4].value = None
                parameters[5].enabled = True
                parameters[6].enabled = False
                parameters[6].value = None
            else:
                parameters[4].enabled = False
                parameters[4].value = None
                parameters[5].enabled = False
                parameters[5].value = None
                parameters[6].enabled = False
                parameters[6].value = None

        # handle stream layer
        if not parameters[4].hasBeenValidated:
            if parameters[4].value:
                fields = [f.name for f in arcpy.ListFields(parameters[4].value)]
                parameters[6].enabled = True
                parameters[6].filter.list = fields
            else:
                parameters[6].enabled = False
                parameters[6].value = None

        # Default stream threshold value
        if not parameters[5].hasBeenValidated and parameters[5].value is None:
            parameters[5].value = "8 AcresUS"

        # toggle watershed size unit
        if not parameters[7].hasBeenValidated:
            if parameters[7].value is not None and "Watershed Size" in parameters[7].valueAsText.replace("'","").split(";"):
                parameters[8].enabled = True
            else:
                parameters[8].enabled = False
                parameters[8].value = None


    def isLicensed(self):
        """Set whether the tool is licensed to execute."""
        return license([EXTENSIONS.Spatial])

    def updateMessages(self, parameters):
        "Modify the messages created by internal validation for each tool parameter."""
        validate(parameters)

        # toggle existing stream lines /  watershed threshold
        set_required_parameter(parameters[3].valueAsText == "Existing Stream Lines", parameters[3])
        set_required_parameter(parameters[3].valueAsText == "Watershed Size Threshold", parameters[4])

        # toggle watershed size unit
        set_required_parameter(parameters[6].value is not None and "Watershed Size" in parameters[6].valueAsText.replace("'","").split(";"), parameters[7])


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
        # parameters[3] is just a toggle for updateParameters to visualize what the user is doing
        stream = parameters[4].value
        threshold = Area(parameters[5].valueAsText) if parameters[5].value is not None else None
        keep_fields = parameters[6].valueAsText.split(";") if parameters[6].value is not None else None
        calc_fields: set[str] = set(parameters[7].valueAsText.replace("'","").split(";"))
        # read in areal unit and map it's pretty string to the arcpy representation
        watershed_size_unit = AREAL_UNITS(parameters[8].valueAsText) if parameters[8].value is not None else None
        output_file = parameters[9].valueAsText

        # set analysis extent
        if extent:
            arcpy.env.extent = extent

        # create scratch layers
        log("creating scratch layers")
        scratch_watershed_size = arcpy.CreateScratchName("w_size", data_type="FeatureClass", workspace=arcpy.env.scratchGDB)
        scratch_initiations = arcpy.CreateScratchName("initiations", data_type="FeatureClass", workspace=arcpy.env.scratchGDB)
        scratch_end_points = arcpy.CreateScratchName("end_pts", data_type="FeatureClass", workspace=arcpy.env.scratchGDB)
        scratch_feature = arcpy.CreateScratchName("feature", data_type="FeatureClass", workspace=arcpy.env.scratchGDB)
        scratch_output = arcpy.CreateScratchName("output", data_type="FeatureClass", workspace=arcpy.env.scratchGDB)
        scratch_stream = arcpy.CreateScratchName("stream", data_type="FeatureClass", workspace=arcpy.env.scratchGDB)
        scratch_zonst = arcpy.CreateScratchName("zonst", data_type="RasterDataset", workspace=arcpy.env.scratchGDB)
        scratch_max = arcpy.CreateScratchName("max", data_type="FeatureClass", workspace=arcpy.env.scratchGDB)

        # fill DEM
        log("filling raster")
        fill_raster = arcpy.sa.Fill(dem)

        # flow direction
        log("calculating flow direction")
        flow_direction = arcpy.sa.FlowDirection(fill_raster)

        # flow accumulation
        log("calculating flow accumulation")
        flow_accumulation = arcpy.sa.FlowAccumulation(flow_direction)

        if stream:
            if extent:
                # necessary since FeatureVerticesToPoints won't see edge of extent as an endpoint otherwise
                arcpy.analysis.Clip(stream, extent.polygon, scratch_stream)
            else:
                scratch_stream = stream

            # get end points of existing lines
            log("finding existing streamline endpoints")
            arcpy.management.FeatureVerticesToPoints(scratch_stream, scratch_end_points, point_location="DANGLE")

            # snap stream initiation point to highest flow accumulation within snap_dist
            log("snap existing stream initiation points to flow accumulation model")
            snap_dist = Distance("200 Feet").to_unit(active_map.spatialReference.linearUnitName)

            stream_initiations_raster = arcpy.sa.SnapPourPoint(
                in_pour_point_data=scratch_end_points,
                in_accumulation_raster=flow_accumulation,
                snap_distance=str(snap_dist), # TODO: choose reasonable distance to look for initiation points, user option?
            )

            # convert stream initiation raster to points
            arcpy.conversion.RasterToPoint(stream_initiations_raster, scratch_initiations)

            # find flow path: optimal path as raster
            log("tracing downstream from stream initiation points")
            out_path_accumulation_raster = arcpy.sa.OptimalPathAsRaster(
                in_destination_data=scratch_initiations,
                in_distance_accumulation_raster=flow_accumulation,
                in_back_direction_raster=flow_direction,
                destination_field=get_oid(scratch_initiations)
            )

            if keep_fields:
                # stream to feature
                log("converting stream raster to output feature class")
                arcpy.sa.StreamToFeature(out_path_accumulation_raster, flow_direction, scratch_output, "SIMPLIFY")

                log("joining keep fields to output feature class")
                # create field mapping keeping only join feature fields specified
                field_mapping = arcpy.FieldMappings()
                field_mapping.addTable(scratch_stream)
                for field in field_mapping.fields:
                    if field.name not in keep_fields:
                        field_mapping.removeFieldMap(field_mapping.findFieldMapIndex(field.name))
                field_mapping.addTable(scratch_output)

                # perform spatial join
                arcpy.analysis.SpatialJoin(
                    target_features=scratch_output,
                    join_features=scratch_stream,
                    out_feature_class=scratch_feature,
                    join_operation="JOIN_ONE_TO_ONE",
                    join_type="KEEP_ALL",
                    field_mapping=field_mapping,
                    match_option="CLOSEST",
                    search_radius="25 Meters", # TODO: consider non-hardcoded alternative, user option same as above?
                )

                # remove `Join_Count` and `TARGET_FID` fields
                arcpy.management.DeleteField(scratch_feature, ["Join_Count", "TARGET_FID"])
            else:
                # stream to feature
                log("converting stream raster to output feature class")
                arcpy.sa.StreamToFeature(out_path_accumulation_raster, flow_direction, scratch_feature, "SIMPLIFY")
        else:
            # convert flow accumulation from number of cells to threshold area units
            log("calculating watershed size")
            cell_size = cell_area(dem).to_unit(threshold.unit).area
            watershed_size = flow_accumulation * cell_size

            # con
            log("applying watershed size threshold")
            sql_query = f"VALUE > {threshold.area}"
            con_accumulation = arcpy.sa.Con(watershed_size, 1, "", sql_query)

            # stream to feature
            log("creating stream feature")
            arcpy.sa.StreamToFeature(con_accumulation, flow_direction, scratch_feature, "SIMPLIFY")

        if calc_fields:
            if "Slope" in calc_fields:
                calc_fields.remove("Slope")

                linear_unit = get_linear_unit(scratch_feature)
                z_factor = str(Distance(1, z_unit).to_unit(linear_unit).amount)
                arcpy.sa.AddSurfaceInformation(
                    in_feature_class=scratch_feature,
                    in_surface=dem,
                    out_property="AVG_SLOPE",
                    method="BILINEAR",
                    z_factor=z_factor,
                )

            # calculate watershed size if asked for or if statistics requiring it are called for
            if ("Watershed Size" in calc_fields) or ("Watershed Size" not in calc_fields and calc_fields):
                # get rid of field if it exists
                calc_fields.discard("Watershed Size")

                # fields_set = set(calc_fields) - set("Watershed Size")
                if watershed_size_unit is None:
                    watershed_size_unit = AREAL_UNITS.SquareMilesUS

                # convert flow_accumulation raster to watershed_size_units
                log("calculating output watershed size attribute")
                cell_size = cell_area(dem).to_unit(watershed_size_unit).area
                watershed_size = flow_accumulation * cell_size

                # zonal statistics
                log("adding watershed size information to output")
                arcpy.sa.ZonalStatisticsAsTable(
                    in_zone_data=scratch_feature,
                    zone_field=get_oid(scratch_feature),
                    in_value_raster=watershed_size,
                    out_table=scratch_zonst,
                    ignore_nodata="DATA",
                    statistics_type="MAXIMUM",
                    out_join_layer=scratch_max,
                )

                # get unique max values:
                # the previously calculated values will be incorrect since the endpoint of a stream line at
                # each confluence will have the max flow accumulation equal to itself and its sister stream
                # it joins with so we want to set the flow acc raster values equal to these confluences null
                # to find the actual max flow accumulation value for each stream line
                log("removing confluence statistics")
                unique_vals = {}
                watershed_size_field = find_field(scratch_max, alias="MAX")
                with arcpy.da.SearchCursor(scratch_max, watershed_size_field.name) as cursor:
                    unique_vals = sorted({row[0] for row in cursor})
                sql_query = ' Or '.join(f"Value = {v!s}" for v in unique_vals)
                watershed_size = arcpy.sa.SetNull(watershed_size, watershed_size, where_clause=sql_query)

                # set max values to null and recalculate max values for output
                log("updating watershed size information")
                arcpy.sa.ZonalStatisticsAsTable(
                    in_zone_data=scratch_feature,
                    zone_field=get_oid(scratch_feature),
                    in_value_raster=watershed_size,
                    out_table=scratch_zonst,
                    ignore_nodata="DATA",
                    statistics_type="MAXIMUM",
                    out_join_layer=scratch_watershed_size,
                )

                # copy scratch watershed size to scratch_output
                # necessary because otherwise AlterField gets upset about altering a joined table
                log("copying watershed size data to new feature class")
                arcpy.management.CopyFeatures(scratch_watershed_size, scratch_output)
                scratch_feature = scratch_output # annoying workaround for https://pro.arcgis.com/en/pro-app/3.4/tool-reference/tool-errors-and-warnings/001001-010000/tool-errors-and-warnings-00726-00750-000733.htm

                # rename MAX field created by zonal stats
                watershed_size_field = find_field(scratch_feature, alias="MAX")
                arcpy.management.AlterField(
                    in_table=scratch_feature,
                    field=watershed_size_field.name,
                    new_field_name="wshed_area",
                    new_field_alias=f"Drainage Area ({watershed_size_unit})",
                )

            # calculate rest of asked for fields
            for field in calc_fields:
                # hydrologic information
                hydrologic_regions_91 = os.path.join(os.path.dirname(__file__), os.pardir, os.pardir, 'assets', 'NY Hydrologic Regions', 'NY_Hydrologic_Regions_91.shp')
                hydrologic_regions_06 = os.path.join(os.path.dirname(__file__), os.pardir, os.pardir, 'assets', 'NY Hydrologic Regions', 'NY_Hydrologic_Regions_06.shp')

                # intersect streams and hydrologic regions to get Region ID
                log("intersect stream lines with hydrologic regions info")
                arcpy.analysis.PairwiseIntersect(
                    in_features=[scratch_feature, hydrologic_regions_91],
                    out_feature_class=scratch_intersect,
                    join_attributes="ALL",
                    cluster_tolerance=None,
                    output_type="LINE"
                )
                arcpy.analysis.PairwiseIntersect(
                    in_features=[scratch_intersect, hydrologic_regions_06],
                    out_feature_class=scratch_feature,
                    join_attributes="ALL",
                    cluster_tolerance=None,
                    output_type="LINE"
                )

                field_name = STREAM_STATS_FIELD_MAPPING[field]
                field_alias = field
                fields_ex = [f.name for f in arcpy.ListFields(scratch_feature)]
                if field_name not in fields_ex:
                    log(f"adding and calculating field: {field_alias}")
                    arcpy.management.AddField(
                        in_table=scratch_feature,
                        field_name=field_name,
                        field_type="FLOAT",
                        field_alias=field_alias,
                    )
                else:
                    log(f"calculating field: {field_alias}")

                # calculate values from regression equations
                # for update cursor
                with arcpy.da.UpdateCursor(scratch_feature, ["wshed_area", "RegionID91", "RegionID06", field_name]) as cursor:
                    for line in cursor:
                        da, region91, region06 = line[0], line[1], line[2]
                        if da is not None:
                            line[3] = calculate_statistics(
                                region91=region91,
                                region06=region06,
                                field=field_name,
                                drainage_area=Area(da, watershed_size_unit)
                            )
                        cursor.updateRow(line)

        # warn about empty outputs
        if is_empty(scratch_feature):
            error("Warning: empty output created. Ensure stream initiation data and DEM are valid in study area selected.")

        # copy output to feature class
        log("copying output to feature class")
        arcpy.management.CopyFeatures(scratch_feature, output_file)

        # add flow path polyline to map
        log("adding output to map")
        active_map.addDataFromPath(output_file)

        # save and exit program successfully
        log("saving project")
        project.save()

        # cleanup
        log("deleting unneeded data")
        empty_workspace(arcpy.env.scratchGDB, keep=[])
