# --------------------------------------------------------------------------------
# Name:        Stream Network
# Purpose:     This tool creates a stream network from a DEM, clipped to the extent
#              of a supplied stream layer
#
# License:     Contextual Copyleft AI (CCAI) License v1.0.
#              Full license in LICENSE file.
# --------------------------------------------------------------------------------

import arcpy

from ..helpers import license, get_oid, empty_workspace, convert_length, cell_area, reload_module,\
    log, set_required_parameter, AREAL_UNITS, AREAL_UNITS_MAP
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

        # Note: this could be accomplished with a composite parameter, however
        # composite parameters don't have a way to introspect in updateParameters
        # what the user has toggled the composite parameter to as the dataType
        # we need that functionality in order to set defaults and controlCLSID's
        param2 = arcpy.Parameter(
            displayName="Stream Initiation Point Data Source",
            name="toggle",
            datatype="GPString",
            parameterType="Required",
            direction="Input")
        param2.filter.list = ["Existing Stream Lines", "Watershed Size Threshold"]

        param3 = arcpy.Parameter(
            displayName="Existing Stream Lines",
            name="stream",
            datatype="GPFeatureLayer",
            parameterType="Optional",
            direction="Input")
        param3.filter.list = ["Polyline"]
        param3.controlCLSID = '{60061247-BCA8-473E-A7AF-A2026DDE1C2D}' # allows line creation

        param4 = arcpy.Parameter(
            displayName="Watershed Size Threshold",
            name="threshold",
            datatype="GPArealUnit",
            parameterType="Optional",
            direction="Input")

        param5 = arcpy.Parameter(
            displayName="Fields to keep",
            name="keep",
            datatype="GPString",
            parameterType="Optional",
            multiValue="True",
            direction="Input")
        param5.filter.type = "ValueList"
        param5.filter.list = []

        param6 = arcpy.Parameter(
            displayName="Include calculated watershed size as attribute",
            name="size_bool",
            datatype="GPBoolean",
            parameterType="Optional",
            direction="Input")
        param6.value = True

        param7 = arcpy.Parameter(
            displayName="Watershed Size Unit",
            name="unit",
            datatype="GPString",
            parameterType="Optional",
            direction="Input")
        param7.filter.list = AREAL_UNITS
        param7.value = "Square US Survey Miles"

        param8 = arcpy.Parameter(
            displayName="Output Features",
            name="out_features",
            datatype="DEFeatureClass",
            parameterType="Required",
            direction="Output")
        param8.parameterDependencies = [param0.name]
        param8.schema.clone = True

        params = [param0, param1, param2, param3, param4, param5, param6, param7, param8]
        return params

    def updateParameters(self, parameters):
        # toggle initiation data source
        if not parameters[2].hasBeenValidated:
            if parameters[2].valueAsText == "Existing Stream Lines":
                parameters[3].enabled = True
                parameters[4].enabled = False
                parameters[4].value = None
            elif parameters[2].valueAsText == "Watershed Size Threshold":
                parameters[3].enabled = False
                parameters[3].value = None
                parameters[4].enabled = True
                parameters[5].enabled = False
                parameters[5].value = None
            else:
                parameters[3].enabled = False
                parameters[3].value = None
                parameters[4].enabled = False
                parameters[4].value = None
                parameters[5].enabled = False
                parameters[5].value = None

        # handle stream layer
        if not parameters[3].hasBeenValidated:
            if parameters[3].value:
                fields = [f.name for f in arcpy.ListFields(parameters[3].value)]
                parameters[5].enabled = True
                parameters[5].filter.list = fields
            else:
                parameters[5].enabled = False
                parameters[5].value = None

        # Default stream threshold value
        if not parameters[4].hasBeenValidated and parameters[4].value is None:
            parameters[4].value = "8 AcresUS"

        # toggle watershed size unit
        if not parameters[6].hasBeenValidated:
            if parameters[6].value:
                parameters[7].enabled = True
            else:
                parameters[7].enabled = False
                parameters[7].value = None

        return

    def isLicensed(self):
        """Set whether the tool is licensed to execute."""
        return license(['Spatial'])

    def updateMessages(self, parameters):
        "Modify the messages created by internal validation for each tool parameter."""
        validate(parameters)

        # toggle existing stream lines
        set_required_parameter(parameters[2].valueAsText == "Existing Stream Lines", parameters[3])

        # toggle watershed threshold
        set_required_parameter(parameters[2].valueAsText == "Watershed Size Threshold", parameters[4])

        # toggle watershed size unit
        set_required_parameter(parameters[6].value, parameters[7])

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
        # parameters[2] is just a toggle for updateParameters to visualize what the user is doing
        stream = parameters[3].value
        threshold_size, threshold_unit = parameters[4].valueAsText.split(" ") if parameters[4].value is not None else None, None
        keep_fields = parameters[5].valueAsText.split(";") if parameters[5].value is not None else None
        # read in areal unit and map it's pretty string to the arcpy representation
        watershed_size_bool = parameters[6].value
        watershed_size_unit = AREAL_UNITS_MAP[parameters[7].valueAsText]
        output_file = parameters[8].valueAsText

        # set analysis extent
        if extent:
            arcpy.env.extent = extent

        # create scratch layers
        log("creating scratch layers")
        scratch_initiations = arcpy.CreateScratchName("initiations", data_type="FeatureClass", workspace=arcpy.env.scratchGDB)
        scratch_end_points = arcpy.CreateScratchName("end_pts", data_type="FeatureClass", workspace=arcpy.env.scratchGDB)
        scratch_feature = arcpy.CreateScratchName("feature", data_type="FeatureClass", workspace=arcpy.env.scratchGDB)
        scratch_output = arcpy.CreateScratchName("output", data_type="FeatureClass", workspace=arcpy.env.scratchGDB)
        scratch_stream = arcpy.CreateScratchName("stream", data_type="FeatureClass", workspace=arcpy.env.scratchGDB)
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
            snap_dist = convert_length("200 Feet", active_map.spatialReference.linearUnitName)

            stream_initiations_raster = arcpy.sa.SnapPourPoint(
                in_pour_point_data=scratch_end_points,
                in_accumulation_raster=flow_accumulation,
                snap_distance=snap_dist, # TODO: choose reasonable distance to look for initiation points
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
                    search_radius="25 Meters", # TODO: consider non-hardcoded alternative
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
            cell_size = float(cell_area(dem, threshold_unit).split(" ")[0])
            watershed_size = flow_accumulation * cell_size

            # con
            log("applying watershed size threshold")
            sql_query = "VALUE > {}".format(threshold_size)
            con_accumulation = arcpy.sa.Con(watershed_size, 1, "", sql_query)

            # stream to feature
            log("creating stream feature")
            arcpy.sa.StreamToFeature(con_accumulation, flow_direction, scratch_feature, "SIMPLIFY")

        # add watershed size information if requested
        if watershed_size_bool:
            # convert flow_accumulation raster to watershed_size_units
            log("calculating output watershed size attribute")
            cell_size = float(cell_area(dem, watershed_size_unit).split(" ")[0])
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
                out_join_layer=scratch_output,
            )

            # copy scratch output to output file
            # necessary because otherwise AlterField gets
            # upset about altering a joined table
            arcpy.management.CopyFeatures(scratch_output, output_file)

            # rename MAX field created by zonal stats
            field_name = "MAX"
            fieldList = arcpy.ListFields(output_file)  # Get a list of fields for each feature class
            for field in fieldList:  # Loop through each field
                if field.aliasName == 'MAX':
                    field_name = field.name
            arcpy.management.AlterField(
                in_table=output_file,
                field=field_name,
                new_field_name="watershed",
                new_field_alias="Watershed Size ({})".format(watershed_size_unit),
            )
        else:
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

        return
