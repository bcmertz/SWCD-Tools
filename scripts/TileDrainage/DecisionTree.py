# --------------------------------------------------------------------------------------------------
# Name:        Decision Tree Classification (DTC)
# Purpose:     This tool analyzes soils, hydrology, and land use to find likely tile drained fields.
#
# License:     GNU Affero General Public License v3.
#              Full license in LICENSE file, or at <https://www.gnu.org/licenses/>
# --------------------------------------------------------------------------------------------------

import sys
import arcpy

from helpers import license, get_oid, get_z_unit, z_units, empty_workspace, toggle_required_parameter
from helpers import print_messages as log
from helpers import setup_environment as setup
from helpers import validate_spatial_reference as validate

class DecisionTree(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Decision Tree Calculation"
        self.description = "Model potential tile drainage areas"
        self.category = "Hydrology\\Drainage Tile"
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
            displayName="Z Unit",
            name="z_unit",
            datatype="GPString",
            parameterType="Required",
            direction="Input")
        param1.filter.list = z_units

        param2 = arcpy.Parameter(
            displayName="Analysis Area",
            name="analysis_area",
            datatype="GPExtent",
            parameterType="Optional",
            direction="Input")
        param2.controlCLSID = '{15F0D1C1-F783-49BC-8D16-619B8E92F668}'

        param3 = arcpy.Parameter(
            displayName="Output Features",
            name="out_features",
            datatype="DEFeatureClass",
            direction="Output")
        param3.parameterDependencies = [param0.name]
        param3.schema.clone = True

        param4 = arcpy.Parameter(
            displayName="Soils Shapefile",
            name="soils",
            datatype="GPFeatureLayer",
            parameterType="Required",
            direction="Input")
        param4.filter.list = ["Polygon"]

        param5 = arcpy.Parameter(
            displayName="Drainage Field",
            name="hsg_field",
            datatype="GPString",
            parameterType="Required",
            direction="Input")
        param5.filter.type = "ValueList"
        param5.filter.list = []

        param6 = arcpy.Parameter(
            displayName="Land Use Data",
            name="land_use",
            datatype="GPRasterLayer",
            parameterType="Required",
            direction="Input")

        param7 = arcpy.Parameter(
            displayName="Land Use Field",
            name="land_use_field",
            datatype="GPString",
            parameterType="Required",
            direction="Input")
        param7.filter.type = "ValueList"
        param7.filter.list = []

        param8 = arcpy.Parameter(
            displayName="Agricultural Land Use(s)",
            name="land_use_field_values",
            datatype="GPString",
            multiValue=True,
            parameterType="Required",
            direction="Input")
        param8.filter.type = "ValueList"
        param8.filter.list = []

        param9 = arcpy.Parameter(
            displayName="Number of tile acres in analysis area",
            name="num_acres",
            datatype="GPDouble",
            parameterType="Optional",
            direction="Input")

        params = [param0, param1, param2, param3, param4, param5, param6, param7, param8, param9]
        return params

    def isLicensed(self):
        """Set whether the tool is licensed to execute."""
        return license(['Spatial'])

    def updateParameters(self, parameters):
        # find z unit of raster based on vertical coordinate system
        #  - if there is none, let the user define it
        #  - if it exists, set the value and hide the parameter
        #  - if it doesn't exist show the parameter and set the value to None
        if not parameters[0].hasBeenValidated:
            if parameters[0].value:
                z_unit = get_z_unit(parameters[0].value)
                if z_unit:
                    parameters[1].enabled = False
                    parameters[1].value = z_unit
                else:
                    parameters[1].enabled = True
                    parameters[1].value = None
            else:
                parameters[1].enabled = False
                parameters[1].value = None

        # get soils field
        if not parameters[4].hasBeenValidated:
            if parameters[4].value:
                parameters[5].enabled = True
                fields = [f.name for f in arcpy.ListFields(parameters[4].value)]
                parameters[5].filter.list = fields
                if "drclassdcd" in fields:
                    parameters[5].value = "drclassdcd"
            else:
                parameters[5].enabled = False
                parameters[5].value = None

        # get land use field
        if not parameters[6].hasBeenValidated:
            if parameters[6].value:
                parameters[7].enabled = True
                fields2 = [f2.name for f2 in arcpy.ListFields(parameters[6].value)]
                parameters[7].filter.list = fields2
                if "GeneralLU" in fields2:
                    parameters[7].value = "GeneralLU"
            else:
                parameters[7].enabled = False

        # toggle which land use values to use
        if not parameters[7].hasBeenValidated:
            if parameters[7].value:
                parameters[8].enabled = True
                values2 = []
                with arcpy.da.SearchCursor(parameters[6].value, parameters[7].value) as cursor2:
                        values2 = sorted({row2[0] for row2 in cursor2})
                parameters[8].filter.list = values2
            else:
                parameters[8].enabled = False

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

        dem_layer = parameters[0].value
        dem = arcpy.Raster(dem_layer.name)
        z_unit = parameters[1].value
        extent = parameters[2].value
        output_file = parameters[3].valueAsText
        soils = parameters[4].value
        soils_drainage_field = parameters[5].value
        land_use_raster = parameters[6].value
        land_use_field = parameters[7].value
        land_use_values = parameters[8].valueAsText.replace("'","").split(";")
        num_acres = parameters[9].value

        # set analysis extent
        if extent:
            arcpy.env.extent = extent

        # create scratch layers
        scratch_land_use_polygon = arcpy.CreateScratchName("lu_poly", data_type="FeatureClass", workspace=arcpy.env.scratchGDB)
        scratch_soils_area = arcpy.CreateScratchName("soils", data_type="FeatureClass", workspace=arcpy.env.scratchGDB)
        scratch_intersect = arcpy.CreateScratchName("intersect", data_type="FeatureClass", workspace=arcpy.env.scratchGDB)
        scratch_output = arcpy.CreateScratchName("scratch_output", data_type="FeatureClass", workspace=arcpy.env.scratchGDB)
        scratch_joined = arcpy.CreateScratchName("scratch_joined", data_type="FeatureClass", workspace=arcpy.env.scratchGDB)
        zonal_stats = arcpy.CreateScratchName("zonal_stats", data_type="RasterDataset", workspace=arcpy.env.scratchGDB)
        zonal_stats_poly = arcpy.CreateScratchName("zonal_poly", data_type="FeatureClass", workspace=arcpy.env.scratchGDB)

        # select viable land uses from land use raster
        log("extracting desired land uses")
        scratch_land_use = None
        land_use_sql_query = ""
        existing_values = []
        with arcpy.da.SearchCursor(land_use_raster, land_use_field) as cursor:
            existing_values = sorted({row[0] for row in cursor})
        land_use_values = [ i for i in land_use_values if i in existing_values ]
        if len(land_use_values) != 0:
            for value in land_use_values:
                if land_use_sql_query == "":
                    land_use_sql_query = "{} = '{}'".format(land_use_field, value)
                else:
                    land_use_sql_query += " Or {} = '{}'".format(land_use_field, value)
            scratch_land_use = arcpy.sa.ExtractByAttributes(land_use_raster, land_use_sql_query)
        else:
            log("no valid land uses found in area, please try again with land uses found in analysis area")
            return

        # convert land usage output to polygon
        log("converting land use areas to polygon")
        arcpy.conversion.RasterToPolygon(scratch_land_use, scratch_land_use_polygon, "SIMPLIFY", land_use_field)

        # clip soils layer to ag fields
        log("clipping soils to ag fields")
        arcpy.analysis.PairwiseIntersect([scratch_land_use_polygon, soils], scratch_intersect, join_attributes="ALL")

        # add acres field and calculate
        log("calculating acreage")
        if "Acres" not in [f.name for f in arcpy.ListFields(scratch_intersect)]:
            arcpy.management.AddField(scratch_intersect, "Acres", "FLOAT", 2, 2)
        arcpy.management.CalculateGeometryAttributes(scratch_intersect, geometry_property=[["Acres", "AREA_GEODESIC"]], area_unit="ACRES_US")

        # remove small features
        sql_query = "Acres >= 1.0"
        arcpy.analysis.Select(scratch_intersect, scratch_soils_area, sql_query)

        # calculate drainage class
        log("calculating drainage classes")
        output_drainage_field = "drainage"        
        arcpy.management.CalculateField(
            in_table=scratch_soils_area,
            field=output_drainage_field,
            expression="calculate_value(!{}!)".format(soils_drainage_field),
            expression_type="PYTHON3",
            code_block="""def calculate_value(drainage):
                if drainage == "Very poorly drained":
                    return 1
                elif drainage == "Poorly Drained":
                    return 2
                elif drainage == "Somewhat poorly drained":
                    return 3
                elif drainage == "Moderately well drained":
                    return 4
                elif drainage == "Well drained":
                    return 5
                elif drainage == "Somewhat excessively drained":
                    return 6
                elif drainage == "Excessively drained":
                    return 7
                else:
                    return 8""",
            field_type="DOUBLE",
            enforce_domains="NO_ENFORCE_DOMAINS"
        )

        # slope raster
        log("creating slope raster from DEM")
        scratch_slope = arcpy.sa.Slope(dem, "PERCENT_RISE", "", "GEODESIC", z_unit)

        # slope zonal statistics
        outZonalStats = arcpy.sa.ZonalStatistics(scratch_soils_area, get_oid(scratch_soils_area), scratch_slope, "MEAN")
        outZonalStats = arcpy.sa.Int(outZonalStats)
        outZonalStats.save(zonal_stats) # output field - Value
        arcpy.conversion.RasterToPolygon(zonal_stats, zonal_stats_poly, "SIMPLIFY", "Value") # output field - gridcode

        # rename slope value field from 'gridcode' to 'slope'
        output_slope_field = "slope"
        grid_field = ""
        arcpy.management.CalculateField(
            in_table=zonal_stats_poly,
            field=output_slope_field,
            expression="$feature.gridcode",
            expression_type="ARCADE",
            field_type="FLOAT"
        )

        ## join average slope to ag field polygons
        log("join slope and soil drainage into polygon")
        arcpy.analysis.SpatialJoin(scratch_soils_area, zonal_stats_poly, scratch_joined, "JOIN_ONE_TO_ONE", "KEEP_ALL", match_option="INTERSECT")

        drainage = 1
        slope = 0
        output_acres = 0
        if num_acres:
            # if we know the number of tiled acres in the analysis area then iterate to find the combination
            # of slope and drainge that produces the output
            while output_acres < num_acres:
                # select output features
                sql_query = "{} <= {} And {} <= {}".format(output_slope_field, slope, output_drainage_field, drainage)
                arcpy.analysis.Select(scratch_joined, scratch_output, where_clause=sql_query)

                # find sum of acreage
                sum_acres = round(sum([float(row[0]) for row in arcpy.da.SearchCursor(scratch_output, "Acres")]),2)
                output_acres = sum_acres

                slope += 1
                drainage += 1
                log(sum_acres, drainage, slope)
        else:
            # default to 2 and poorly - somewhat poorly drained
            drainage = 2
            slope = 2

            # select output features
            log("create output")
            sql_query = "{} <= {} And {} <= {}".format(output_slope_field, slope, output_drainage_field, drainage)
            arcpy.analysis.Select(scratch_joined, scratch_output, where_clause=sql_query)

        # create output feature class
        log("creating output feature class")
        arcpy.management.CopyFeatures(scratch_output, output_file)

        # add output to map
        log("adding output to map")
        active_map.addDataFromPath(output_file)

        # cleanup
        log("deleting unneeded data")
        #empty_workspace(arcpy.env.scratchGDB, keep=[])

        # save project
        log("saving project")
        project.save()

        return
