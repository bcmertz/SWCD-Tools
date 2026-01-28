# --------------------------------------------------------------------------------
# Name:        Potential Wetlands
# Purpose:     This tool analyzes soils, hydrology, and land use to calculate
#              potential wetland areas.
#
# License:     GNU Affero General Public License v3.
#              Full license in LICENSE file, or at <https://www.gnu.org/licenses/>
# --------------------------------------------------------------------------------

import arcpy

from ..helpers import license, get_oid, get_z_unit, z_units, empty_workspace, toggle_required_parameter, reload_module, log
from ..helpers import setup_environment as setup
from ..helpers import validate_spatial_reference as validate

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
            displayName="Maximum Slope (%)",
            name="max_slope",
            datatype="GPDouble",
            parameterType="Optional",
            direction="Output")

        param5 = arcpy.Parameter(
            displayName="Topographic Wetness Index (TWI) Raster",
            name="twi",
            datatype="GPRasterLayer",
            parameterType="Optional",
            direction="Input")

        param6 = arcpy.Parameter(
            displayName="Minimum TWI Value",
            name="min_twi",
            datatype="GPDouble",
            parameterType="Optional",
            direction="Output")

        param7 = arcpy.Parameter(
            displayName="Soils Shapefile",
            name="soils",
            datatype="GPFeatureLayer",
            parameterType="Required",
            direction="Input")
        param7.filter.list = ["Polygon"]

        param8 = arcpy.Parameter(
            displayName="HSG Field",
            name="hsg_field",
            datatype="GPString",
            parameterType="Required",
            direction="Input")
        param8.filter.type = "ValueList"
        param8.filter.list = []

        param9 = arcpy.Parameter(
            displayName="Valid HSGs",
            name="hsg_values",
            multiValue = True,
            datatype="GPString",
            parameterType="Required",
            direction="Input")
        param9.filter.type = "ValueList"
        param9.filter.list = []

        param10 = arcpy.Parameter(
            displayName="Land Use Data",
            name="land_use",
            datatype="GPRasterLayer",
            parameterType="Required",
            direction="Input")

        param11 = arcpy.Parameter(
            displayName="Land Use Field",
            name="land_use_field",
            datatype="GPString",
            parameterType="Required",
            direction="Input")
        param11.filter.type = "ValueList"
        param11.filter.list = []

        param12 = arcpy.Parameter(
            displayName="Land Uses to Include",
            name="land_use_field_values",
            datatype="GPString",
            multiValue=True,
            parameterType="Required",
            direction="Input")
        param12.filter.type = "ValueList"
        param12.filter.list = []

        param13 = arcpy.Parameter(
            displayName="Exclude Mapped Wetlands, Floodplains, etc?",
            name="exclude_wetlands",
            datatype="GPBoolean",
            parameterType="Optional",
           direction="Input")

        param14 = arcpy.Parameter(
            displayName="Excluded Areas",
            name="wetland_layers",
            datatype="GPFeatureLayer",
            multiValue=True,
            parameterType="Optional",
           direction="Input")
        param14.filter.list = ["Polygon"]

        params = [param0, param1, param2, param3, param4, param5, param6, param7, param8, param9, param10, param11, param12, param13, param14]
        return params

    def isLicensed(self):
        """Set whether the tool is licensed to execute."""
        return license(['Spatial'])

    def updateParameters(self, parameters):
        # default maximum slope value
        if parameters[4].value is None:
            parameters[4].value = 5

        # enable minimum twi if there is a twi raster
        if not parameters[5].hasBeenValidated:
            if parameters[5].value:
                parameters[6].enabled = True
                if not parameters[6].value:
                    parameters[6].value = 5
            else:
                parameters[6].enabled = False

        # get soils field
        if not parameters[7].hasBeenValidated:
            if parameters[7].value:
                parameters[8].enabled = True
                fields = [f.name for f in arcpy.ListFields(parameters[7].value)]
                parameters[8].filter.list = fields
                if "hydgrpdcd" in fields:
                    parameters[8].value = "hydgrpdcd"
            else:
                parameters[8].enabled = False
                parameters[8].value = None

        # toggle which soil hsg values to use
        if not parameters[8].hasBeenValidated:
            if parameters[8].value:
                parameters[9].enabled = True
                values = set()
                with arcpy.da.SearchCursor(parameters[7].value, parameters[8].value) as cursor:
                    for row in cursor:
                        if row[0] is not None:
                            values.add(row[0])
                values = sorted(list(values))
                parameters[9].filter.list = values
            else:
                parameters[9].enabled = False

        # get land use field
        if not parameters[10].hasBeenValidated:
            if parameters[10].value:
                parameters[11].enabled = True
                fields2 = [f2.name for f2 in arcpy.ListFields(parameters[10].value)]
                parameters[11].filter.list = fields2
                if "GeneralLU" in fields2:
                    parameters[11].value = "GeneralLU"
            else:
                parameters[11].enabled = False

        # toggle which land use values to use
        if not parameters[11].hasBeenValidated:
            if parameters[11].value:
                parameters[12].enabled = True
                values2 = []
                with arcpy.da.SearchCursor(parameters[10].value, parameters[11].value) as cursor2:
                        values2 = sorted({row2[0] for row2 in cursor2})
                parameters[12].filter.list = values2
            else:
                parameters[12].enabled = False

        # toggle asking for wetland layers
        if not parameters[13].hasBeenValidated:
            if parameters[13].value:
                parameters[14].enabled = True
            else:
                parameters[14].enabled = False

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

        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool parameter."""
        # make optional parameters[5] required based off of parameters[6]
        toggle_required_parameter(parameters[5], parameters[6])

        validate(parameters)
        return

    @reload_module(__name__)
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
        max_slope = parameters[4].value
        twi_raster = parameters[5].value
        min_twi = parameters[6].value
        soils_shapefile = parameters[7].value
        soils_hsg_field = parameters[8].value
        hsg_values = parameters[9].valueAsText.split(";")
        land_use_raster = parameters[10].value
        land_use_field = parameters[11].value
        land_use_values = parameters[12].valueAsText.replace("'","").split(";")
        calculate_wetlands = parameters[13].value
        wetland_layers = parameters[14].valueAsText.replace("'","").split(";") if calculate_wetlands else []

        # set analysis extent
        if extent:
            arcpy.env.extent = extent

        # create scratch layers
        scratch_slope_polygon = arcpy.CreateScratchName("slope_poly", data_type="FeatureClass", workspace=arcpy.env.scratchGDB)
        scratch_slope_dissolve_polygon  = arcpy.CreateScratchName("dissolve_poly", data_type="FeatureClass", workspace=arcpy.env.scratchGDB)
        scratch_soils_area = arcpy.CreateScratchName("soils", data_type="FeatureClass", workspace=arcpy.env.scratchGDB)
        scratch_hsg_soils = arcpy.CreateScratchName("hsg", data_type="FeatureClass", workspace=arcpy.env.scratchGDB)
        scratch_land_use_polygon = arcpy.CreateScratchName("land_use", data_type="FeatureClass", workspace=arcpy.env.scratchGDB)
        scratch_erase = arcpy.CreateScratchName("erase", data_type="FeatureClass", workspace=arcpy.env.scratchGDB)
        scratch_union = arcpy.CreateScratchName("union", data_type="FeatureClass", workspace=arcpy.env.scratchGDB)
        scratch_dissolve = arcpy.CreateScratchName("dissolve", data_type="FeatureClass", workspace=arcpy.env.scratchGDB)
        land_use_raster_clip = arcpy.CreateScratchName("lu_clip", data_type="RasterDataset", workspace=arcpy.env.scratchGDB)
        scratch_zonal_stats = arcpy.CreateUniqueName("zonal_stats")

        # slope raster
        log("creating slope raster from DEM")
        scratch_slope = arcpy.sa.Slope(dem, "PERCENT_RISE", "", "GEODESIC", z_unit)

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
            # combine mask layers into one layer
            arcpy.analysis.Union(wetland_layers, scratch_union)

            # erase combined mask layer from output
            arcpy.analysis.Erase(scratch_land_use_polygon, scratch_union, scratch_erase)
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

        # cleanup
        log("deleting unneeded data")
        empty_workspace(arcpy.env.scratchGDB, keep=[])
        arcpy.management.Delete([scratch_zonal_stats])

        # save project
        log("saving project")
        project.save()

        return
