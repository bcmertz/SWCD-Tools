# --------------------------------------------------------------------------------
# Name:        Stream Network
# Purpose:     This tool creates a stream network from a DEM, clipped to the extent
#              of a supplied stream layer
#
# License:     Contextual Copyleft AI (CCAI) License v1.0.
#              Full license in LICENSE file.
# --------------------------------------------------------------------------------

import arcpy

from ..helpers import license, get_oid, empty_workspace, cell_area, convert_area, reload_module, log
from ..helpers import setup_environment as setup
from ..helpers import validate_spatial_reference as validate

class StreamNetwork(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Calculate Stream Network"
        self.description = "Create stream network from DEM"
        self.category = "Fluvial Geomorphology"
        self.canRunInBackground = False

    def getParameterInfo(self):
        """Define parameter definitions"""
        param0 = arcpy.Parameter(
            displayName="Hydro-Conditioned DEM",
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
            displayName="Existing Stream Lines",
            name="stream",
            datatype="GPFeatureLayer",
            parameterType="Optional",
            direction="Input")
        param2.filter.list = ["Line"]
        param2.controlCLSID = '{60061247-BCA8-473E-A7AF-A2026DDE1C2D}' # allows line creation

        # NOTE: composite parameters not supported until ArcGIS Pro 3.4
        # once supported consider combining threshold and stream lines
        # into one parameter with a toggle
        param3 = arcpy.Parameter(
            displayName="Stream Initiation Threshold",
            name="threshold",
            datatype="GPArealUnit",
            parameterType="Required",
            direction="Input")

        param4 = arcpy.Parameter(
            displayName="Fields to keep",
            name="keep",
            datatype="GPString",
            parameterType="Optional",
            multiValue="True",
            direction="Input")
        param4.filter.type = "ValueList"
        param4.filter.list = []

        param5 = arcpy.Parameter(
            displayName="Include calculated watershed size as attribute",
            name="size_bool",
            datatype="GPBoolean",
            parameterType="Optional",
            direction="Input")
        param5.value = True

        param6 = arcpy.Parameter(
            displayName="Output Features",
            name="out_features",
            datatype="DEFeatureClass",
            parameterType="Required",
            direction="Output")
        param6.parameterDependencies = [param0.name]
        param6.schema.clone = True

        params = [param0, param1, param2, param3, param4, param5, param6]
        return params

    def updateParameters(self, parameters):
        # get stream line fields
        if not parameters[2].hasBeenValidated:
            if parameters[2].value:
                fields = [f.name for f in arcpy.ListFields(parameters[2].value)]
                parameters[4].enabled = True
                parameters[4].filter.list = fields
            else:
                parameters[4].enabled = False
                parameters[4].value = None

        # Default stream threshold value
        if parameters[3].value is None:
            parameters[3].value = "8 AcresUS"

        return

    def isLicensed(self):
        """Set whether the tool is licensed to execute."""
        return license(['Spatial'])

    def updateMessages(self, parameters):
        "Modify the messages created by internal validation for each tool parameter."""
        validate(parameters)
        return

    @reload_module(__name__)
    def execute(self, parameters, messages):
        """The source code of the tool."""
        # Setup
        log("setting up project")
        project, active_map = setup()

        # read in parameters
        dem = parameters[0].value
        extent = parameters[1].value
        stream = parameters[2].value
        threshold_size, threshold_unit = parameters[3].valueAsText.split(" ")
        keep_fields = parameters[4].valueAsText.split(";") if parameters[4].value is not None else None
        watershed_size_bool = parameters[5].value
        output_file = parameters[6].valueAsText

        # set analysis extent
        if extent:
            arcpy.env.extent = extent

        # create scratch layers
        log("creating scratch layers")
        scratch_streamlines = arcpy.CreateScratchName("scratch_streamlines", data_type="FeatureClass", workspace=arcpy.env.scratchGDB)
        scratch_end_points = arcpy.CreateScratchName("end_pts", data_type="FeatureClass", workspace=arcpy.env.scratchGDB)
        scratch_output = arcpy.CreateScratchName("output", data_type="FeatureClass", workspace=arcpy.env.scratchGDB)
        scratch_zonst = arcpy.CreateScratchName("zonst", data_type="RasterDataset", workspace=arcpy.env.scratchGDB)

        # fill DEM
        log("filling raster")
        fill_raster = arcpy.sa.Fill(dem)

        # flow direction
        log("calculating flow direction")
        flow_direction = arcpy.sa.FlowDirection(fill_raster)

        # flow accumulation
        log("calculating flow accumulation")
        flow_accumulation = arcpy.sa.FlowAccumulation(flow_direction)

        # convert flow accumulation from number of cells to threshold area units
        log("calculating watershed size")
        raster_cell_area = cell_area(dem)
        cell_size = convert_area(raster_cell_area, threshold_unit).split(" ")[0]
        watershed_size = flow_accumulation * float(cell_size)

        # con
        log("applying watershed threshold")
        sql_query = "VALUE > {}".format(threshold_size)
        con_accumulation = arcpy.sa.Con(watershed_size, 1, "", sql_query)

        if stream:
            # stream to feature
            log("creating stream feature")
            arcpy.sa.StreamToFeature(con_accumulation, flow_direction, scratch_streamlines, True)

            # get end points of existing lines
            log("finding existing streamline endpoints")
            arcpy.management.FeatureVerticesToPoints(stream, scratch_end_points, point_location="DANGLE")

            # get stream initiation point
            # choose max value, if beyond it the point doesn't snap which is usually fine if there's not a watershed divide in between
            log("snap existing stream initiation points to flow accumulation model")
            stream_initiations = arcpy.edit.Snap(scratch_end_points, snap_environment=[[scratch_streamlines, "EDGE", "200 Feet"]]) # TODO: choose reasonable distance to look for initiation points

            # find flow path: optimal path as raster
            log("tracing downstream from stream initiation points")
            out_path_accumulation_raster = arcpy.sa.OptimalPathAsRaster(
                in_destination_data=stream_initiations,
                in_distance_accumulation_raster=flow_accumulation,
                in_back_direction_raster=flow_direction,
                destination_field=get_oid(stream_initiations)
            )

            if keep_fields:
                # stream to feature
                log("converting stream raster to output feature class")
                arcpy.sa.StreamToFeature(out_path_accumulation_raster, flow_direction, scratch_output, True)

                log("joining keep fields to output feature class")
                # create field mapping keeping only join feature fields specified
                field_mapping = arcpy.FieldMappings()
                field_mapping.addTable(stream)
                for field in field_mapping.fields:
                    if field.name not in keep_fields:
                        field_mapping.removeFieldMap(field_mapping.findFieldMapIndex(field.name))
                field_mapping.addTable(scratch_output)

                # perform spatial join
                arcpy.analysis.SpatialJoin(
                    target_features=scratch_output,
                    join_features=stream,
                    out_feature_class=output_file,
                    join_operation="JOIN_ONE_TO_ONE",
                    join_type="KEEP_ALL",
                    field_mapping=field_mapping,
                    match_option="CLOSEST",
                    search_radius="25 Meters", # consider non-hardcoded alternative
                )

                # remove `Join_Count` and `TARGET_FID` fields
                arcpy.management.DeleteField(output_file, ["Join_Count", "TARGET_FID"])
            else:
                # stream to feature
                log("converting stream raster to output feature class")
                arcpy.sa.StreamToFeature(out_path_accumulation_raster, flow_direction, output_file, True)
        else:
            # stream to feature
            log("creating stream feature")
            arcpy.sa.StreamToFeature(con_accumulation, flow_direction, output_file, True)

        # add watershed size information if requested
        if watershed_size_bool:
            # zonal statistics
            log("adding watershed size information to output")
            arcpy.sa.ZonalStatisticsAsTable(
                in_zone_data=output_file,
                zone_field=get_oid(output_file),
                in_value_raster=watershed_size,
                out_table=scratch_zonst,
                ignore_nodata="DATA",
                statistics_type="MAXIMUM",
                out_join_layer=scratch_output,
            )

            # copy scratch output to output file
            # necessary because otherwise AlterField gets
            # upset about altering a joined table
            arcpy.management.CopyFeatures(scratch_output, output_file)

            # rename MAX field created by zonal stats
            field_name = "MAX"
            fieldList = arcpy.ListFields(output_file)  # Get a list of fields for each feature class
            for field in fieldList:  # Lloop through each field
                if field.aliasName == 'MAX':
                    field_name = field.name
            arcpy.management.AlterField(
                in_table=output_file,
                field=field_name,
                new_field_name="watershed",
                new_field_alias="Watershed Size ({})".format(threshold_unit),
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

        return
