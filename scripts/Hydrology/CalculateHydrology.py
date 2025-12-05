# --------------------------------------------------------------------------------
# Name:        Calculate Hydrology
# Purpose:     This tool takes a watershed and RCNs, and calculates slopes,
#              longest flow path, and other parameters needed to run EFH-2 analysis
#
# License:     GNU Affero General Public License v3.
#              Full license in LICENSE file, or at <https://www.gnu.org/licenses/>
# --------------------------------------------------------------------------------
import os
import arcpy
import pathlib
import openpyxl
import datetime

from helpers import license
from helpers import print_messages as log
from helpers import setup_environment as setup
from helpers import validate_spatial_reference as validate

class CalculateHydrology:
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "EFH-2 Calculation"
        self.category = "Hydrology"
        self.description = "Calculate the hydrology of the given watershed"

    def getParameterInfo(self):
        """Define parameter definitions"""
        param0 = arcpy.Parameter(
            displayName="Runoff Curve Number Layer",
            name="rcns",
            datatype="GPFeatureLayer",
            parameterType="Required",
            direction="Input")

        param1 = arcpy.Parameter(
            displayName="DEM",
            name="dem",
            datatype="GPRasterLayer",
            parameterType="Required",
            direction="Input")

        param2 = arcpy.Parameter(
            displayName="Output Folder",
            name="output_location",
            datatype="DEFolder",
            parameterType="Required",
            direction="Input")

        param3 = arcpy.Parameter(
            displayName="HSG Field",
            name="hsg_field",
            datatype="GPString",
            parameterType="Required",
            direction="Input")
        param3.filter.type = "ValueList"
        param3.filter.list = []

        param4 = arcpy.Parameter(
            displayName="RCN Field",
            name="rcn_field",
            datatype="GPString",
            parameterType="Required",
            direction="Input")
        param4.filter.type = "ValueList"
        param4.filter.list = []

        param5 = arcpy.Parameter(
            displayName="Acres Field",
            name="acres_field",
            datatype="GPString",
            parameterType="Required",
            direction="Input")
        param5.filter.type = "ValueList"
        param5.filter.list = []

        param6 = arcpy.Parameter(
            displayName="Land Use Field",
            name="land_use_field",
            datatype="GPString",
            parameterType="Required",
            direction="Input")
        param6.filter.type = "ValueList"
        param6.filter.list = []

        params = [param0, param1, param2, param3, param4, param5, param6]
        return params

    def updateParameters(self, parameters):
        # get RCN fields
        if not parameters[0].hasBeenValidated:
            if parameters[0].value:
                parameters[3].enabled = True
                parameters[4].enabled = True
                parameters[5].enabled = True
                parameters[6].enabled = True
                fields = [f.name for f in arcpy.ListFields(parameters[0].value)]
                parameters[3].filter.list = fields
                parameters[4].filter.list = fields
                parameters[5].filter.list = fields
                parameters[6].filter.list = fields
                if "hydgrpdcd" in fields:
                    parameters[3].value = "hydgrpdcd"
                if "RCN" in fields:
                    parameters[4].value = "RCN"
                if "Acres" in fields:
                    parameters[5].value = "Acres"
                if "LandUse" in fields:
                    parameters[6].value = "LandUse"
            else:
                parameters[3].enabled = False
                parameters[4].enabled = False
                parameters[5].enabled = False
                parameters[6].enabled = False

        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool parameter."""
        validate(parameters)
        return

    def isLicensed(self):
        """Set whether the tool is licensed to execute."""
        return license(['Spatial'])

    def execute(self, parameters, messages):
        """The source code of the tool."""
        # Setup
        log("setting up project")
        project, active_map = setup()

        # read in parameters
        log("reading in parameters")
        rcn_layer = parameters[0].value
        raster_layer = parameters[1].value
        output_folder_path = parameters[2].valueAsText
        hsg_field = parameters[3].value
        rcn_field = parameters[4].value
        acres_field = parameters[5].value
        land_use_field = parameters[6].value

        # utils
        watershed_layer_id = arcpy.ValidateTableName(rcn_layer.name)

        # TODO: create scratch layers
        log("creating scratch layers")
        scratch_watershed = arcpy.CreateScratchName("scratch_watershed", data_type="DEFeatureClass", workspace=arcpy.env.scratchFolder)

        # dissolve RCN boundaries to find watershed boundary
        log("dissolve RCN boundaries")
        arcpy.analysis.PairwiseDissolve(rcn_layer, scratch_watershed)

        # add acres field and calculate for watershed
        log("calculating watershed size")
        if acres_field not in [f.name for f in arcpy.ListFields(scratch_watershed)]:
            arcpy.management.AddField(scratch_watershed, acres_field, "FLOAT", field_precision=255, field_scale=2)
        arcpy.management.CalculateGeometryAttributes(scratch_watershed, geometry_property=[[acres_field, "AREA_GEODESIC"]], area_unit="ACRES_US")
        acres = round(sum([float(row[0]) for row in arcpy.da.SearchCursor(scratch_watershed, acres_field)]),2)

        # clip DEM raster to watershed
        log("clipping elevation data to watershed boundary")
        out_dem_watershed_clip = arcpy.sa.ExtractByMask(raster_layer, scratch_watershed, "INSIDE")

        # slope map
        log("creating slope map")
        slope_raster = arcpy.sa.Slope(out_dem_watershed_clip, "PERCENT_RISE", "", "GEODESIC", "METER")

        # TODO: zonal statistics
        log("finding average slope")
        out_table_name = "zonalstatistics_{}".format(watershed_layer_id)
        out_table_path = "{}\\{}".format(arcpy.env.workspace, out_table_name)
        field_name = arcpy.Describe(scratch_watershed).OIDFieldName
        arcpy.sa.ZonalStatisticsAsTable(scratch_watershed, field_name, slope_raster, out_table_name, "", "MEAN")
        mean_slope = round(float([row[0] for row in arcpy.da.SearchCursor(out_table_path, "MEAN")][0]),2)

        # fill DEM to eventually find flow length of watershed
        log("filling DEM for flow direction calculation")
        filled_dem = arcpy.sa.Fill(out_dem_watershed_clip)

        # calculate flow directions
        log("calculating flow direction")
        flow_direction_raster = arcpy.sa.FlowDirection(filled_dem)

        # find flow lengths of watershed
        log("creating flow length raster")
        flow_length_raster = arcpy.sa.FlowLength(flow_direction_raster, "DOWNSTREAM")

        # find maximum flow length
        log("finding max flow length")
        flow_length_maximum = int(float(arcpy.management.GetRasterProperties(flow_length_raster, "MAXIMUM").getOutput(0))*3.2808)

        # setup hydrology worksheet locations
        log("creating hydrology worksheet")
        hydrology_worksheet = os.path.join(os.path.dirname(__file__), os.pardir, os.pardir, 'assets', 'Hydrology Data Form.xlsx')
        output_worksheet_path = '{}\{}_hydrology.xlsx'.format(output_folder_path, watershed_layer_id)
        output_worksheet_path = pathlib.PureWindowsPath(output_worksheet_path).as_posix()

        # fill out hydrology worksheet
        log("filling out hydrology worksheet")
        hydrology_worksheet = openpyxl.load_workbook(hydrology_worksheet)
        ws_calculations = hydrology_worksheet['Calculations']
        ws_data = hydrology_worksheet['Data']
        ws_calculations["E1"] = project.filePath.split("\\")[-1][:-5]
        ws_calculations['F2'] = datetime.date.today().isoformat()
        ws_calculations['G2'] = datetime.datetime.now().strftime("%H:%M:%S")
        ws_calculations['H2'] = watershed_layer_id
        ws_calculations['G4'] = acres
        ws_calculations['G6'] = flow_length_maximum
        ws_calculations['G7'] = mean_slope

        with arcpy.da.SearchCursor(rcn_layer, [rcn_field, acres_field, land_use_field, hsg_field]) as cursor:
            idx = 2
            for row in cursor:
                rcn = row[0]
                acres = row[1]
                land_use = row[2]
                hsg = row[3]
                ws_data["C"+str(idx)] = rcn
                ws_data["D"+str(idx)] = acres
                ws_data["A"+str(idx)] = land_use
                ws_data["B"+str(idx)] = hsg
                idx += 1

        hydrology_worksheet.save(output_worksheet_path)
        hydrology_worksheet.close()

        # save program successfully
        log("saving project")
        project.save()

        # open hydrology worksheet
        log("opening hydrology worksheet folder")
        os.startfile(output_folder_path)

        return
