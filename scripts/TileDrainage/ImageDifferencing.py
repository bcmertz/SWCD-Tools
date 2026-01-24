# --------------------------------------------------------------------------------------------------
# Name:        Image Differencing
# Purpose:     This tool finds agricultural areas where short-wave infrared radiation reflectance
#              in dry and post-storm conditions are similar, indicating potential drainage tile.
#
# License:     GNU Affero General Public License v3.
#              Full license in LICENSE file, or at <https://www.gnu.org/licenses/>
# --------------------------------------------------------------------------------------------------

import arcpy

from ..helpers import license, reload_module, log
from ..helpers import setup_environment as setup
from ..helpers import validate_spatial_reference as validate

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
            displayName="Wet Raster",
            name="date_field",
            datatype="GPRasterLayer",
            parameterType="Required",
            direction="Input")

        param1 = arcpy.Parameter(
            displayName="Dry Raster",
            name="dry",
            datatype="GPRasterLayer",
            parameterType="Required",
            direction="Input")

        param2 = arcpy.Parameter(
            displayName="Land Use Data",
            name="land_use",
            datatype="GPRasterLayer",
            parameterType="Required",
            direction="Input")

        param3 = arcpy.Parameter(
            displayName="Land Use Field",
            name="land_use_field",
            datatype="GPString",
            parameterType="Required",
            direction="Input")
        param3.filter.type = "ValueList"
        param3.filter.list = []

        param4 = arcpy.Parameter(
            displayName="Agricultural Land Use(s)",
            name="land_use_field_values",
            datatype="GPString",
            multiValue=True,
            parameterType="Required",
            direction="Input")
        param4.filter.type = "ValueList"
        param4.filter.list = []

        param5 = arcpy.Parameter(
            displayName="Output Features",
            name="out_features",
            datatype="DEFeatureClass",
            direction="Output")
        param5.parameterDependencies = [param0.name]
        param5.schema.clone = True

        params = [param0, param1, param2, param3, param4, param5]
        return params

    def isLicensed(self):
        """Set whether the tool is licensed to execute."""
        return license(['Spatial'])

    def updateParameters(self, parameters):
        # get land use field
        if not parameters[2].hasBeenValidated:
            if parameters[2].value:
                parameters[3].enabled = True
                fields2 = [f2.name for f2 in arcpy.ListFields(parameters[2].value)]
                parameters[3].filter.list = fields2
                if "GeneralLU" in fields2:
                    parameters[3].value = "GeneralLU"
            else:
                parameters[3].enabled = False

        # toggle which land use values to use
        if not parameters[3].hasBeenValidated:
            if parameters[3].value:
                parameters[4].enabled = True
                values2 = []
                with arcpy.da.SearchCursor(parameters[2].value, parameters[3].value) as cursor2:
                        values2 = sorted({row2[0] for row2 in cursor2})
                parameters[4].filter.list = values2
            else:
                parameters[4].enabled = False

        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool parameter."""
        validate(parameters)
        return

    @reload_module(__name__)
    def execute(self, parameters, messages):
        """The source code of the tool."""
        # Setup
        log("setting up project")
        project, active_map = setup()

        wet_raster = arcpy.Raster(parameters[0].valueAsText)
        dry_raster = arcpy.Raster(parameters[1].valueAsText)
        land_use_raster = parameters[2].value
        land_use_field = parameters[3].value
        land_use_values = parameters[4].valueAsText.replace("'","").split(";")
        output_file = parameters[5].valueAsText

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

        # add output to map
        log("adding output to map")
        active_map.addDataFromPath(output_file)

        # save project
        log("saving project")
        project.save()

        return
