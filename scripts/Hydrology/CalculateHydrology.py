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
            displayName="DEM",
            name="dem",
            datatype="GPRasterLayer",
            parameterType="Required",
            direction="Input")

        param1 = arcpy.Parameter(
            displayName="Watershed Boundary Layer",
            name="watershed",
            datatype="GPFeatureLayer",
            parameterType="Required",
            direction="Input")

        param2 = arcpy.Parameter(
            displayName="Runoff Curve Number Layer",
            name="rcns",
            datatype="GPFeatureLayer",
            parameterType="Required",
            direction="Input")

        param3 = arcpy.Parameter(
            displayName="Output Folder",
            name="output_location",
            datatype="DEFolder",
            parameterType="Required",
            direction="Input")

        params = [param0, param1, param2, param3]
        return params

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
        raster_layer = parameters[0].value
        watershed_layer = parameters[1].value
        rcn_layer = parameters[2].value
        output_folder_path = parameters[3].valueAsText

        # add watershed layer to the map if needed
        if not arcpy.Exists(watershed_layer):
            # need to add the layer to the map and make it a geodatabase
            watershed_layer = active_map.addDataFromPath(watershed_layer)
            watershed_layer_path = "{}\\{}".format(arcpy.env.workspace, watershed_layer.name)
            arcpy.conversion.ExportFeatures(watershed_layer, watershed_layer_path)
            watershed_layer = active_map.addDataFromPath(watershed_layer_path)
            watershed_layer = active_map.listLayers(watershed_layer)[0]
        else:
            watershed_layer = active_map.listLayers(watershed_layer)[0]

        # utils
        watershed_layer_id = arcpy.ValidateTableName(watershed_layer.name)

        # calculate runoff curve number acreage
        log("calculating runoff curve number acreage")
        if "Acres" not in [f.name for f in arcpy.ListFields(rcn_layer)]:
            arcpy.management.AddField(rcn_layer, "Acres", "FLOAT", field_precision=255, field_scale=2)
        arcpy.management.CalculateGeometryAttributes(in_features=rcn_layer, geometry_property=[["Acres", "AREA_GEODESIC"]], area_unit="ACRES_US")

        # add acres field and calculate for watershed
        log("calculating watershed size")
        if "Acres" not in [f.name for f in arcpy.ListFields(watershed_layer.dataSource)]:
            arcpy.management.AddField(watershed_layer, "Acres", "FLOAT", field_precision=255, field_scale=2)
        arcpy.management.CalculateGeometryAttributes(in_features=watershed_layer, geometry_property=[["Acres", "AREA_GEODESIC"]], area_unit="ACRES_US")
        acres = round(float([row[0] for row in arcpy.da.SearchCursor(watershed_layer, "Acres")][0]),2)

        # clip DEM raster
        log("clipping elevation data to watershed")
        clip_1m_dem = raster_layer
        out_dem_path = "{}\\{}_{}".format(arcpy.env.workspace, "DEM_1m_clip", watershed_layer_id)
        clip_1m_dem = arcpy.management.Clip(clip_1m_dem, "", out_dem_path, watershed_layer, "#", "ClippingGeometry")

        # slope map
        log("creating slope map")
        out_slope_path = "{}\\w_slope".format(arcpy.env.workspace)
        slope_raster = arcpy.sa.Slope(clip_1m_dem, "PERCENT_RISE", "", "GEODESIC", "METER")
        slope_raster.save(out_slope_path)

        # zonal statistics
        log("finding average slope")
        out_table_name = "zonalstatistics_{}".format(watershed_layer_id)
        out_table_path = "{}\\{}".format(arcpy.env.workspace, out_table_name)
        field_name = arcpy.Describe(watershed_layer).OIDFieldName
        arcpy.sa.ZonalStatisticsAsTable(watershed_layer, field_name, slope_raster, out_table_name, "", "MEAN")
        mean_slope = round(float([row[0] for row in arcpy.da.SearchCursor(out_table_path, "MEAN")][0]),2)

        # fill DEM to eventually find flow length of watershed
        log("filling DEM for flow direction calculation")
        out_fill_path = "{}_{}".format(out_dem_path, "fill")
        filled_dem = arcpy.sa.Fill(clip_1m_dem)
        filled_dem.save(out_fill_path)

        # calculate flow directions
        log("calculating flow direction")
        out_flowdir_path = "{}\\flow_direction_{}".format(arcpy.env.workspace, watershed_layer_id)
        flow_direction_raster = arcpy.sa.FlowDirection(filled_dem)
        flow_direction_raster.save(out_flowdir_path)

        # find flow lengths of watershed
        log("creating flow length raster")
        out_flow_length_path = "{}\\flow_length_{}".format(arcpy.env.workspace, watershed_layer_id)
        flow_length_raster = arcpy.sa.FlowLength(flow_direction_raster, "DOWNSTREAM")
        flow_length_raster.save(out_flow_length_path)

        # find maximum flow length
        log("finding max flow length")
        flow_length_maximum = int(float(arcpy.management.GetRasterProperties(flow_length_raster, "MAXIMUM").getOutput(0))*3.2808)

        ## create max flow length raster
        #log("creating max flow length raster")
        #outZonalStats_path = "{}\\zonal_stats_{}".format(arcpy.env.workspace, watershed_layer_id)
        #oidFieldName = arcpy.Describe(watershed_layer).oidFieldName
        #outZonalStats = arcpy.sa.ZonalStatistics(watershed_layer, oidFieldName, flow_length_raster, "MAXIMUM")
        #outZonalStats.save(outZonalStats_path)

        ## raster calculator con to get max flow length and raster to point
        #log("creating point at max flow length location")
        #max_flow_point_raster_path = "{}\\max_flow_point_{}".format(arcpy.env.workspace, watershed_layer_id)
        #log(outZonalStats.name,flow_length_raster.name)
        #max_flow_raster = arcpy.sa.RasterCalculator([outZonalStats.name,flow_length_raster.name], ["max_length", "flow_length"], r' Con(Raster("max_length") == Raster("flow_length"), Raster("flow_length"))')
        #max_flow_raster.save(max_flow_point_raster_path)
        #max_flow_length_point_path = "{}\\max_flow_length_point_{}".format(arcpy.env.workspace, watershed_layer_id)
        #max_flow_length_point = arcpy.conversion.RasterToPoint(max_flow_raster, max_flow_length_point_path,"Value")

        ## optimal path as raster
        #log("creating optimal flow path raster")
        #optimal_path_raster_path = "{}\\optimal_path_raster_{}".format(arcpy.env.workspace, watershed_layer_id)
        #out_path_accumulation_raster = arcpy.sa.OptimalPathAsRaster(max_flow_length_point, flow_length_raster, flow_direction_raster)
        #out_path_accumulation_raster.save(optimal_path_raster_path)

        ## raster to polyline
        #log("converting optimal flow path raster to polyline")
        #optimal_line_path = "{}\\optimal_line_{}".format(arcpy.env.workspace, watershed_layer_id)
        #arcpy.conversion.RasterToPolyline(out_path_accumulation_raster, optimal_line_path)
        #active_map.addDataFromPath(optimal_line_path)

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
        ws_calculations['H2'] = watershed_layer.name
        ws_calculations['G4'] = acres
        ws_calculations['G6'] = flow_length_maximum
        ws_calculations['G7'] = mean_slope

        with arcpy.da.SearchCursor(rcn_layer, ["RCN", "Acres"]) as cursor:
            idx = 1
            for row in cursor:
                rcn = row[0]
                acres = row[1]
                #land_use = row[2]
                #hsg = row[3]
                ws_data["C"+str(idx)] = rcn
                ws_data["D"+str(idx)] = acres
                #ws_data["A"+str(idx)] = land_use
                #ws_data["B"+str(idx)] = hsg
                idx += 1

        hydrology_worksheet.save(output_worksheet_path)

        # save program successfully
        log("saving project")
        project.save()

        # open hydrology worksheet
        log("opening hydrology worksheet folder")
        os.startfile(output_folder_path)

        return
