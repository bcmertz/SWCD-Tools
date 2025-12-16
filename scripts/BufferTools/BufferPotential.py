# --------------------------------------------------------------------------------
# Name:        Buffer Potential
# Purpose:     This tool finds potential riparian forest buffer planting areas.
#
# License:     GNU Affero General Public License v3.
#              Full license in LICENSE file, or at <https://www.gnu.org/licenses/>
# --------------------------------------------------------------------------------

import math
import arcpy

from helpers import license
from helpers import print_messages as log
from helpers import setup_environment as setup
from helpers import validate_spatial_reference as validate

class BufferPotential:
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Riparian Forest Buffer Potential"
        self.description = "Find RFB Potential"
        self.category = "Buffer tools"
        self.canRunInBackground = False

    def getParameterInfo(self):
        """Define the tool parameters."""
        param0 = arcpy.Parameter(
            displayName="Stream Centerline",
            name="centerline",
            datatype="GPFeatureLayer",
            parameterType="Required",
            direction="Input")
        param0.filter.list = ["Polyline"]
        param0.controlCLSID = '{60061247-BCA8-473E-A7AF-A2026DDE1C2D}' # allows line creation
        
        param1 = arcpy.Parameter(
            displayName="Buffer Width (ft)",
            name="width",
            datatype="GPDouble",
            parameterType="Required",
            direction="Input")

        param2 = arcpy.Parameter(
            displayName="Minimum planting size (acres)",
            name="size",
            datatype="GPDouble",
            parameterType="Required",
            direction="Input")

        param3 = arcpy.Parameter(
            displayName="Analysis Area",
            name="analysis_area",
            datatype="GPExtent",
            parameterType="Required",
            direction="Input")
        param3.controlCLSID = '{15F0D1C1-F783-49BC-8D16-619B8E92F668}'

        param4 = arcpy.Parameter(
            displayName="Output Features",
            name="out_features",
            datatype="DEFeatureClass",
            parameterType="Required",
            direction="Output")
        param4.parameterDependencies = [param0.name]

        param5 = arcpy.Parameter(
            displayName="Land Use Data",
            name="land_use",
            datatype="GPRasterLayer",
            parameterType="Required",
            direction="Input")

        param6 = arcpy.Parameter(
            displayName="Land Use Field",
            name="land_use_field",
            datatype="GPString",
            parameterType="Required",
            direction="Input")
        param6.filter.type = "ValueList"
        param6.filter.list = []

        param7 = arcpy.Parameter(
            displayName="Land Uses to Include",
            name="land_use_field_values",
            datatype="GPString",
            multiValue=True,
            parameterType="Required",
            direction="Input")
        param7.filter.type = "ValueList"
        param7.filter.list = []

        param8 = arcpy.Parameter(
            displayName="Exclude Mapped Wetlands, Floodplains, etc?",
            name="exclude_wetlands",
            datatype="GPBoolean",
            parameterType="Optional",
           direction="Input")

        param9 = arcpy.Parameter(
            displayName="Excluded Areas",
            name="wetland_layers",
            datatype="GPFeatureLayer",
            multiValue=True,
            parameterType="Optional",
           direction="Input")
        param8.filter.list = ["Polygon"]

        params = [param0, param1, param2, param3, param4, param5, param6, param7, param8, param9]
        return params

    def isLicensed(self):
        """Set whether the tool is licensed to execute."""
        return license(['Spatial'])

    def updateParameters(self, parameters):
        # default buffer width
        if parameters[1].value == None:
            parameters[1].value = 100

        # set default minimum planting size
        if parameters[2].value == None:
            parameters[2].value = .25

        # get land use field
        if not parameters[5].hasBeenValidated:
            if parameters[5].value:
                parameters[6].enabled = True
                fields2 = [f2.name for f2 in arcpy.ListFields(parameters[5].value)]
                parameters[6].filter.list = fields2
            else:
                parameters[6].enabled = False

        # toggle which land use values to use
        if not parameters[6].hasBeenValidated:
            if parameters[6].value:
                parameters[7].enabled = True
                values2 = []
                with arcpy.da.SearchCursor(parameters[5].value, parameters[6].value) as cursor2:
                        values2 = sorted({row2[0] for row2 in cursor2})
                parameters[7].filter.list = values2
            else:
                parameters[7].enabled = False

        # toggle asking for exclusion layers
        if not parameters[8].hasBeenValidated:
            if parameters[8].value == True:
                parameters[9].enabled = True
            else:
                parameters[9].enabled = False

        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool parameter."""
        validate(parameters)
        return

    def execute(self, parameters, messages):
        """The source code of the tool."""
        # Setup
        log("setting up project")
        project, active_map = setup()

        log("reading in parameters")
        stream = parameters[0].value
        min_width = parameters[1].value
        min_acres = parameters[2].value
        extent = parameters[3].value.polygon
        output_file = parameters[4].valueAsText
        land_use_raster = parameters[5].value
        land_use_field = parameters[6].value
        land_use_values = parameters[7].valueAsText.replace("'","").split(";")
        calculate_wetlands = parameters[8].value
        wetland_layers = parameters[9].valueAsText.replace("'","").split(";") if calculate_wetlands else [] 
        scratch_land_use_polygon = arcpy.CreateScratchName("land_use", data_type="FeatureClass", workspace=arcpy.env.scratchFolder)
        scratch_erase = arcpy.CreateScratchName("erase", data_type="FeatureClass", workspace=arcpy.env.scratchFolder)
        scratch_dissolve = arcpy.CreateScratchName("dissolve", data_type="FeatureClass", workspace=arcpy.env.scratchFolder)

        # create scratch layers
        log("creating scratch layers")
        scratch_stream_layer = arcpy.CreateScratchName("stream", data_type="FeatureClass", workspace=arcpy.env.scratchFolder)
        scratch_stream_buffer = arcpy.CreateScratchName("stream_buffer", data_type="FeatureClass", workspace=arcpy.env.scratchFolder)
        land_use_raster_clip = "{}\\land_use_raster_clip".format(arcpy.env.workspace)

        # clip streams to analysis area
        log("clipping stream centerline to analysis area")
        arcpy.analysis.Clip(stream, extent, scratch_stream_layer)

        # pairwise buffer stream
        log("creating buffer polygon around stream")
        arcpy.analysis.PairwiseBuffer(scratch_stream_layer, scratch_stream_buffer, "{} Feet".format(min_width), "ALL", "", "GEODESIC", "")

        # clip land uses to buffer
        log("extracting land use data inside buffer area")
        out_land_use = arcpy.sa.ExtractByMask(land_use_raster, scratch_stream_buffer, "INSIDE", "MINOF")
        out_land_use.save(land_use_raster_clip)

        # select viable land uses from land use raster
        log("extracting desired land uses")
        scratch_land_use = None
        land_use_sql_query = ""
        existing_values = []
        with arcpy.da.SearchCursor(land_use_raster_clip, land_use_field) as cursor:
            existing_values = sorted({row[0] for row in cursor})
        land_use_values = [ i for i in land_use_values if i in existing_values ]
        if len(land_use_values) != 0:
            for value in land_use_values:
                if land_use_sql_query == "":
                    land_use_sql_query = "{} = '{}'".format(land_use_field, value)
                else:
                    land_use_sql_query += " Or {} = '{}'".format(land_use_field, value)
            scratch_land_use = arcpy.sa.ExtractByAttributes(land_use_raster_clip, land_use_sql_query)
        else:
            log("no valid land uses found in area, please try again with land uses found in analysis area")
            return

        # convert land usage output to polygon
        log("converting land use areas to polygon")
        arcpy.conversion.RasterToPolygon(scratch_land_use, scratch_land_use_polygon, "NO_SIMPLIFY", "VALUE")

        # iterate through exclusion lauyers and remove
        if calculate_wetlands:
            log("erasing excluded areas from output")
            for wetland_layer in wetland_layers:
                try:
                    arcpy.analysis.Erase(scratch_land_use_polygon, wetland_layer, scratch_erase)
                except arcpy.ExecuteError:
                    log("failed to erase excluded areas, please see error below:")
                    log(arcpy.GetMessages())
                    sys.exit()
        else:
            scratch_erase = scratch_land_use_polygon

        # dissolve polygon boundaries
        log("dissolving output polygon boundaries")
        arcpy.analysis.PairwiseDissolve(
            scratch_erase,
            scratch_dissolve,
            dissolve_field=None,
            statistics_fields=None,
            multi_part="SINGLE_PART",
        )

        # calculate acreage
        log("calculating acreage of planting areas")
        arcpy.management.AddField(scratch_dissolve, "Acres", "FLOAT", 2, 2)
        arcpy.management.CalculateGeometryAttributes(scratch_dissolve, geometry_property=[["Acres", "AREA_GEODESIC"]], area_unit="ACRES_US")

        # drop acreage < threshold
        sql_query = "Acres >= {}".format(min_acres)
        arcpy.analysis.Select(scratch_dissolve, output_file, sql_query)

        # add output to map
        log("adding output to map")
        lyr = active_map.addDataFromPath(output_file)

        # cleanup
        log("deleting unneeded data")
        arcpy.management.Delete([scratch_stream_layer,scratch_stream_buffer])

        # save
        log("saving project")
        project.save()

        return
