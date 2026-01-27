# --------------------------------------------------------------------------------------------------
# Name:        Image Differencing
# Purpose:     This tool finds agricultural areas where short-wave infrared radiation reflectance
#              in dry and post-storm conditions are similar, indicating potential drainage tile.
#
# License:     GNU Affero General Public License v3.
#              Full license in LICENSE file, or at <https://www.gnu.org/licenses/>
# --------------------------------------------------------------------------------------------------

import arcpy

from ..helpers import license, reload_module, log, toggle_required_parameter, empty_workspace
from ..helpers import setup_environment as setup
from ..helpers import validate_spatial_reference as validate

# Landsat 8-9 qa_pixel bands have a 16bit binary raster of values describing
# the cloud coverage in a give 3x3 cell window.
# Here we map their integer values to their descriptions
#
# For more info see Landsat 8-9 Operational Land Imager (OLI) - Thermal Infrared
# Sensor (TIRS) Collection 2 (C2) Level 2 (L2) Data Format Control Book (DFCB), page 8
landsat_qa_map = {
    1:     "Fill - invalid data",
    21762: "Cloud buffer",
    21824: "Valid land",
    21890: "Cloud buffer over water",
    21952: "Water",
    22018: "Cloud buffer over land",
    22080: "Valid land - low confidence",
    22146: "Cloud buffer over water",
    22208: "Water",
    22280: "Cloud",
    23826: "Cloud buffer or shadow",
    23888: "Shadow",
    24082: "Cloud buffer or shadow",
    24144: "Shadow",
    54534: "Cloud buffer or cirrus cloud",
    54596: "Cirrus cloud",
    54790: "Cloud buffer or cirrus cloud",
    54852: "Cirrus cloud",
    55052: "Cirrus cloud or other",
    56598: "Cloud buffer or cirrus or shadow",
    56660: "Cirrus cloud or shadow",
    56854: "Cloud buffer or cirrus or shadow",
    56916: "Cirrus cloud or shadow",
}

class ImageDifferencing(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Image Differencing"
        self.description = "This tool finds agricultural areas where short-wave infrared radiation reflectance in dry and post-storm conditions are similar, indicating potential drainage tile."
        self.category = "Hydrology\\Drainage Tile"
        self.canRunInBackground = False

    def getParameterInfo(self):
        """Define parameter definitions"""
        param0 = arcpy.Parameter(
            displayName="Analysis Area",
            name="analysis_area",
            datatype="GPExtent",
            parameterType="Optional",
            direction="Input")
        param0.controlCLSID = '{15F0D1C1-F783-49BC-8D16-619B8E92F668}'

        param1 = arcpy.Parameter(
            displayName="Wet Raster",
            name="date_field",
            datatype="GPRasterLayer",
            parameterType="Required",
            direction="Input")

        param2 = arcpy.Parameter(
            displayName="Dry Raster",
            name="dry",
            datatype="GPRasterLayer",
            parameterType="Required",
            direction="Input")

        param3 = arcpy.Parameter(
            displayName="Land Use Data",
            name="land_use",
            datatype="GPRasterLayer",
            parameterType="Required",
            direction="Input")

        param4 = arcpy.Parameter(
            displayName="Land Use Field",
            name="land_use_field",
            datatype="GPString",
            parameterType="Required",
            direction="Input")
        param4.filter.type = "ValueList"
        param4.filter.list = []

        param5 = arcpy.Parameter(
            displayName="Agricultural Land Use(s)",
            name="land_use_field_values",
            datatype="GPString",
            multiValue=True,
            parameterType="Required",
            direction="Input")
        param5.filter.type = "ValueList"
        param5.filter.list = []

        param6 = arcpy.Parameter(
            displayName="Output Features",
            name="out_features",
            datatype="DEFeatureClass",
            direction="Output")
        param6.parameterDependencies = [param0.name]
        param6.schema.clone = True

        param7 = arcpy.Parameter(
            displayName="Create clouds and shadows layer?",
            name="cloud",
            datatype="GPBoolean",
            parameterType="Optional",
           direction="Input")

        param8 = arcpy.Parameter(
            displayName="Output Cloud/Shadow Feature",
            name="cloud_output",
            parameterType="Optional",
            datatype="DEFeatureClass",
            direction="Output")

        params = [param0, param1, param2, param3, param4, param5, param6, param7, param8]
        return params

    def isLicensed(self):
        """Set whether the tool is licensed to execute."""
        return license(['Spatial'])

    def updateParameters(self, parameters):
        # get land use field
        if not parameters[3].hasBeenValidated:
            if parameters[3].value:
                parameters[4].enabled = True
                fields2 = [f2.name for f2 in arcpy.ListFields(parameters[3].value)]
                parameters[4].filter.list = fields2
                if "GeneralLU" in fields2:
                    parameters[4].value = "GeneralLU"
            else:
                parameters[4].enabled = False

        # toggle which land use values to use
        if not parameters[4].hasBeenValidated:
            if parameters[4].value:
                parameters[5].enabled = True
                values2 = []
                with arcpy.da.SearchCursor(parameters[3].value, parameters[4].value) as cursor2:
                        values2 = sorted({row2[0] for row2 in cursor2})
                parameters[5].filter.list = values2
            else:
                parameters[5].enabled = False

        # toggle asking for default contour interval and output
        if not parameters[7].hasBeenValidated:
            if parameters[7].value:
                parameters[8].enabled = True
                if parameters[6].value:
                    parameters[8].value = parameters[6].valueAsText + "_cloud_shadow_mask"
            else:
                parameters[8].enabled = False
                parameters[8].value = None # clear its value so we don't overwrite existing features while disabled

        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool parameter."""
        # toggle cloud output path
        toggle_required_parameter(parameters[7], parameters[8])

        validate(parameters)
        return

    @reload_module(__name__)
    def execute(self, parameters, messages):
        """The source code of the tool."""
        # Setup
        log("setting up project")
        project, active_map = setup()

        log("reading in parameters")
        extent = parameters[0].value
        wet_raster = arcpy.Raster(parameters[1].valueAsText)
        dry_raster = arcpy.Raster(parameters[2].valueAsText)
        land_use_raster = parameters[3].value
        land_use_field = parameters[4].value
        land_use_values = parameters[5].valueAsText.replace("'","").split(";")
        output_file = parameters[6].valueAsText
        cloud_bool = parameters[7].value
        cloud_output = parameters[8].valueAsText
        wet_cloud_output = cloud_output+"_wet"
        dry_cloud_output = cloud_output+"_dry"

        # set analysis extent
        if extent:
            arcpy.env.extent = extent

        # create scratch layers
        log("creating scratch layers")
        scratch_wet_cloud_output = arcpy.CreateScratchName("wet_cloud", data_type="FeatureClass", workspace=arcpy.env.scratchGDB)
        scratch_dry_cloud_output = arcpy.CreateScratchName("dry_cloud", data_type="FeatureClass", workspace=arcpy.env.scratchGDB)

        # find difference
        log("finding reflectance difference between dry and wet conditions")
        diff = wet_raster - dry_raster

        # find output extent
        log("calculating output extent")
        extent = diff.extent
        arcpy.env.extent = extent

        # finding negative values (?)
        log("selecting areas with reflectance indicative of tile drainage")
        tile = arcpy.sa.Con(diff<=0, 1)

        # create sql query
        log("creating land use sql query")
        sql_query = ""
        if len(land_use_values) != 0:
            for value in land_use_values:
                if sql_query == "":
                    sql_query = "{} = '{}'".format(land_use_field, value)
                else:
                    sql_query += " Or {} = '{}'".format(land_use_field, value)
        else:
            log("no valid land uses, please rerun")
            return

        # find agricultural areas
        log("finding agricultural land use areas")
        ag = arcpy.sa.Con(land_use_raster, 1, None, sql_query)

        # intersect potential tile and ag areas
        log("intersecting ag and potential tile areas")
        out = ag - tile

        # converting output to polygon
        log("converting output to polygon")
        arcpy.conversion.RasterToPolygon(out, output_file, "SIMPLIFY")

        # check if cloud conditional parameter
        if cloud_bool:
            for i in [("wet", wet_raster, scratch_wet_cloud_output, wet_cloud_output), ("dry", dry_raster, scratch_dry_cloud_output, dry_cloud_output)]:
                prefix = i[0]
                raster = i[1]
                scratch = i[2]
                output = i[3]

                # example: LC09_L2SP_014031_20250728_20250730_02_T1_QA_PIXEL.TIF
                #          LC08_L2SP_015030_20250812_20250821_02_T1_SR_B6.TIF
                #
                # get QA rasters for wet and dry
                log("finding {} and dry Landsat QA PIXEL layers".format(prefix))
                qa_raster = arcpy.Raster(raster.catalogPath[:-9]+"QA_PIXEL.tif")

                # TODO: extract both by mask with output polygon

                log("extracting non-land QA attributes")
                qa_query = "Value <> 22080 And Value <> 21824" # from landsat_qa_map for valid land
                extract_qa = arcpy.sa.ExtractByAttributes(qa_raster, qa_query)

                # converting output to polygon
                log("converting {} cloud output to polygon".format(prefix))
                arcpy.conversion.RasterToPolygon(extract_qa, scratch, "SIMPLIFY")

                # add description field
                value_field = 'gridcode'
                log("calculating {} cloud layer descriptions".format(prefix))
                arcpy.management.Dissolve(scratch, output, value_field)
                arcpy.management.CalculateField(
                    in_table=output,
                    field="Description",
                    expression="calculate_value(!{}!,{})".format(value_field, landsat_qa_map),
                    expression_type="PYTHON3",
                    code_block="""def calculate_value(gridcode, landsat_qa_map):
                    desc = landsat_qa_map.get(gridcode)
                    if desc:
                        return landsat_qa_map[gridcode]
                    else:
                        return 'Unknown'""",
                    field_type="TEXT",
                    enforce_domains="NO_ENFORCE_DOMAINS"
                )

                # add to map
                log("adding {} cloud and shadow layer to map and updating symbology".format(prefix))
                output = active_map.addDataFromPath(output)

                # update symbology
                sym = output.symbology
                sym.updateRenderer('UniqueValueRenderer')
                sym.renderer.fields = ['Description']
                output.symbology = sym

        # add output to map
        log("adding output to map")
        active_map.addDataFromPath(output_file)

        # cleanup
        log("deleting unneeded data")
        empty_workspace(arcpy.env.scratchGDB, keep=[])

        # save project
        log("saving project")
        project.save()

        return
