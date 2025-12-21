# --------------------------------------------------------------------------------
# Name:        Potential Wetlands
# Purpose:     This tool analyzes soils, hydrology, and land use to calculate
#              potential wetland areas.
#
# License:     GNU Affero General Public License v3.
#              Full license in LICENSE file, or at <https://www.gnu.org/licenses/>
# --------------------------------------------------------------------------------

import sys
import arcpy

from helpers import license, get_oid
from helpers import print_messages as log
from helpers import setup_environment as setup
from helpers import validate_spatial_reference as validate

class PotentialWetlands(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Model Potential Wetlands"
        self.description = "Model potential wetlands from DEM"
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
            direction="Output")

        param2.parameterDependencies = [param0.name]
        param2.schema.clone = True

        param3 = arcpy.Parameter(
            displayName="Maximum Slope (%)",
            name="max_slope",
            datatype="GPDouble",
            parameterType="Optional",
            direction="Output")

        param4 = arcpy.Parameter(
            displayName="Topographic Wetness Index (TWI) Raster",
            name="twi",
            datatype="GPRasterLayer",
            parameterType="Optional",
            direction="Input")

        param5 = arcpy.Parameter(
            displayName="Minimum TWI Value",
            name="min_twi",
            datatype="GPDouble",
            parameterType="Required",
            direction="Output")

        param6 = arcpy.Parameter(
            displayName="Soils Shapefile",
            name="soils",
            datatype="GPFeatureLayer",
            parameterType="Required",
            direction="Input")
        param6.filter.list = ["Polygon"]

        param7 = arcpy.Parameter(
            displayName="HSG Field",
            name="hsg_field",
            datatype="GPString",
            parameterType="Required",
            direction="Input")
        param7.filter.type = "ValueList"
        param7.filter.list = []

        param8 = arcpy.Parameter(
            displayName="Valid HSGs",
            name="hsg_values",
            multiValue = True,
            datatype="GPString",
            parameterType="Required",
            direction="Input")
        param8.filter.type = "ValueList"
        param8.filter.list = []

        param9 = arcpy.Parameter(
            displayName="Land Use Data",
            name="land_use",
            datatype="GPRasterLayer",
            parameterType="Required",
            direction="Input")

        param10 = arcpy.Parameter(
            displayName="Land Use Field",
            name="land_use_field",
            datatype="GPString",
            parameterType="Required",
            direction="Input")
        param10.filter.type = "ValueList"
        param10.filter.list = []

        param11 = arcpy.Parameter(
            displayName="Land Uses to Include",
            name="land_use_field_values",
            datatype="GPString",
            multiValue=True,
            parameterType="Required",
            direction="Input")
        param11.filter.type = "ValueList"
        param11.filter.list = []

        param12 = arcpy.Parameter(
            displayName="Exclude Mapped Wetlands, Floodplains, etc?",
            name="exclude_wetlands",
            datatype="GPBoolean",
            parameterType="Optional",
           direction="Input")

        param13 = arcpy.Parameter(
            displayName="Excluded Areas",
            name="wetland_layers",
            datatype="GPFeatureLayer",
            multiValue=True,
            parameterType="Optional",
           direction="Input")
        param11.filter.list = ["Polygon"]

        params = [param0, param1, param2, param3, param4, param5, param6, param7, param8, param9, param10, param11, param12, param13]
        return params

    def isLicensed(self):
        """Set whether the tool is licensed to execute."""
        return license(['Spatial'])

    def updateParameters(self, parameters):
        # default maximum slope value
        if parameters[3].value == None:
            parameters[3].value = 5

        # enable minimum twi value if there is a twi raster
        if not parameters[4].hasBeenValidated:
            if parameters[4].value:
                parameters[5].enabled = True
            else:
                parameters[5].enabled = False

        # set default minimum twi value
        if parameters[5].value == None:
            parameters[5].value = 5

        # get soils field
        if not parameters[6].hasBeenValidated:
            if parameters[6].value:
                parameters[7].enabled = True
                fields = [f.name for f in arcpy.ListFields(parameters[6].value)]
                parameters[7].filter.list = fields
                if "hydgrpdcd" in fields:
                    parameters[7].value = "hydgrpdcd"
            else:
                parameters[7].enabled = False
                parameters[7].value = None

        # toggle which soil hsg values to use
        if not parameters[7].hasBeenValidated:
            if parameters[7].value:
                parameters[8].enabled = True
                values = set()
                with arcpy.da.SearchCursor(parameters[6].value, parameters[7].value) as cursor:
                    for row in cursor:
                        if row[0] != None:
                            values.add(row[0])
                values = sorted(list(values))
                parameters[8].filter.list = values
            else:
                parameters[8].enabled = False

        # get land use field
        if not parameters[9].hasBeenValidated:
            if parameters[9].value:
                parameters[10].enabled = True
                fields2 = [f2.name for f2 in arcpy.ListFields(parameters[9].value)]
                parameters[10].filter.list = fields2
                if "GeneralLU" in fields2:
                    parameters[10].value = "GeneralLU"
            else:
                parameters[10].enabled = False

        # toggle which land use values to use
        if not parameters[10].hasBeenValidated:
            if parameters[10].value:
                parameters[11].enabled = True
                values2 = []
                with arcpy.da.SearchCursor(parameters[9].value, parameters[10].value) as cursor2:
                        values2 = sorted({row2[0] for row2 in cursor2})
                parameters[11].filter.list = values2
            else:
                parameters[11].enabled = False

        # toggle asking for wetland layers
        if not parameters[12].hasBeenValidated:
            if parameters[12].value == True:
                parameters[13].enabled = True
            else:
                parameters[13].enabled = False

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
        extent = parameters[1].value
        output_file = parameters[2].valueAsText
        max_slope = parameters[3].value
        twi_raster = parameters[4].value
        min_twi = parameters[5].value
        soils_shapefile = parameters[6].value
        soils_hsg_field = parameters[7].value
        hsg_values = parameters[8].valueAsText.split(";")
        land_use_raster = parameters[9].value
        land_use_field = parameters[10].value
        land_use_values = parameters[11].valueAsText.replace("'","").split(";")
        calculate_wetlands = parameters[12].value
        wetland_layers = parameters[13].valueAsText.replace("'","").split(";") if calculate_wetlands else []

        # set analysis extent
        if extent:
            arcpy.env.extent = extent

        # create scratch layers
        scratch_slope_polygon = arcpy.CreateScratchName("slope_poly", data_type="FeatureClass", workspace=arcpy.env.scratchFolder)
        scratch_slope_dissolve_polygon  = arcpy.CreateScratchName("dissolve_poly", data_type="FeatureClass", workspace=arcpy.env.scratchFolder)
        scratch_soils_area = arcpy.CreateScratchName("soils", data_type="FeatureClass", workspace=arcpy.env.scratchFolder)
        scratch_hsg_soils = arcpy.CreateScratchName("hsg", data_type="FeatureClass", workspace=arcpy.env.scratchFolder)
        land_use_raster_clip = "{}\\land_use_raster_clip".format(arcpy.env.workspace)
        scratch_land_use_polygon = arcpy.CreateScratchName("land_use", data_type="FeatureClass", workspace=arcpy.env.scratchFolder)
        scratch_reduced_potential_wetland = arcpy.CreateScratchName("reduced_pot", data_type="FeatureClass", workspace=arcpy.env.scratchFolder)
        scratch_zonal_stats = arcpy.CreateUniqueName("zonal_stats")
        scratch_erase = arcpy.CreateScratchName("erase", data_type="FeatureClass", workspace=arcpy.env.scratchFolder)
        scratch_output = arcpy.CreateScratchName("output", data_type="FeatureClass", workspace=arcpy.env.scratchFolder)
        scratch_dissolve = arcpy.CreateScratchName("dissolve", data_type="FeatureClass", workspace=arcpy.env.scratchFolder)

        # slope raster
        log("creating slope raster from DEM")
        scratch_slope = arcpy.sa.Slope(dem, "PERCENT_RISE", "", "GEODESIC", "METER")

        # slopes < max_slope percent
        log("selecting slopes less than or equal to {}%".format(max_slope))
        slope_sql_query = "VALUE <= {}".format(max_slope)
        scratch_low_slope = arcpy.sa.Con(scratch_slope, scratch_slope, "", slope_sql_query)

        # convert con output to int
        log("converting slope raster to int")
        scratch_int_slope = arcpy.sa.Int(scratch_low_slope)

        # slope raster to polygon
        log("converting slope raster to polygon")
        arcpy.conversion.RasterToPolygon(scratch_int_slope, scratch_slope_polygon, "NO_SIMPLIFY")

        # dissolve raster polygon features
        log("dissolving slope polygon boundaries")
        arcpy.management.Dissolve(scratch_slope_polygon, scratch_slope_dissolve_polygon)

        # clip soils layer to low slope areas
        log("clipping soils to low slope areas")
        arcpy.analysis.Clip(soils_shapefile, scratch_slope_dissolve_polygon, scratch_soils_area)

        # select HSG: A/D, B/D, C/D, C, or D from soils
        log("selecting hydric soils")
        hsg_sql_query = ""
        for hsg in hsg_values:
            hsg = hsg.replace("'", "")
            if hsg_sql_query == "":
                hsg_sql_query = "{} = '{}'".format(soils_hsg_field, hsg)
            else:
                hsg_sql_query += " Or {} = '{}'".format(soils_hsg_field, hsg)
        arcpy.analysis.Select(scratch_soils_area, scratch_hsg_soils, hsg_sql_query)

        # clip land use raster
        log("clipping land use raster to valid soils area and slope less than or equal to {}%".format(max_slope))
        out_land_use = arcpy.sa.ExtractByMask(land_use_raster, scratch_hsg_soils, "INSIDE", "MINOF")
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

        # erase NWI / DEC wetlands if selected
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

        # exclude polygons with TWI max less than min_twi
        if twi_raster:
            # zonal stats as table
            log("finding max TWI in each polygon")
            dissolve_oid = get_oid(scratch_dissolve)
            arcpy.sa.ZonalStatisticsAsTable(
                in_zone_data=scratch_dissolve,
                zone_field=dissolve_oid,
                in_value_raster=twi_raster,
                out_table=scratch_zonal_stats,
                ignore_nodata="DATA",
                statistics_type="MEAN",
                out_join_layer=scratch_dissolve
            )

            # drop < min_twi
            twi_sql_query = "MEAN >= {}".format(min_twi)
            arcpy.analysis.Select(scratch_dissolve, output_file, twi_sql_query)
        else:
            log("copying potential wetland features to output feature class")
            arcpy.management.CopyFeatures(scratch_dissolve, output_file)

        # add output to map
        log("adding output to map")
        lyr = active_map.addDataFromPath(output_file)

        # set symbology based off of average TWI
        if twi_raster and lyr.isFeatureLayer:
            log("setting output layer symbology")
            sym = lyr.symbology
            try:
              if sym.renderer.type == 'SimpleRenderer':
                sym.updateRenderer('GraduatedColorsRenderer')
                sym.renderer.breakCount = 3
                sym.renderer.classificationMethod = 'NaturalBreaks'

                # get non-aliased MEAN field name
                fields = arcpy.ListFields(lyr)
                field_name = ""
                for field in fields:
                    if field.aliasName == "MEAN":
                        field_name = field.baseName
                        break
                sym.renderer.classificationField = field_name
                sym.renderer.colorRamp = project.listColorRamps('Blues (3 Classes)')[0]
                lyr.symbology = sym
            except:
                log("could not set output symbology properly")

        # delete not needed scratch layers
        log("deleting unused layers")
        arcpy.management.Delete([scratch_slope_polygon,scratch_slope_dissolve_polygon,scratch_soils_area,scratch_hsg_soils,land_use_raster_clip,scratch_land_use_polygon,scratch_reduced_potential_wetland,scratch_zonal_stats,scratch_erase,scratch_output,scratch_dissolve])

        # save project
        log("saving project")
        project.save()

        return
