# --------------------------------------------------------------------------------------------------
# Name:        Landscape Position
# Purpose:     TODO
#
# License:     Contextual Copyleft AI (CCAI) License v1.0.
#              Full license in LICENSE file.
# --------------------------------------------------------------------------------------------------

import arcpy

from .TopographicPositionIndex import topographic_position_index
from ..helpers import license, reload_module, log, convert_length, cell_length, convert_length, Z_UNITS, get_z_unit
from ..helpers import setup_environment as setup
from ..helpers import validate_spatial_reference as validate

class LandscapePosition(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Landscape Position"
        self.description = "TODO"
        self.category = "Terrain Analysis"
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
        param1.filter.list = Z_UNITS

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
            parameterType="Required",
            direction="Output")
        param3.parameterDependencies = [param0.name]
        param3.schema.clone = True

        params = [param0, param1, param2, param3]
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

        # read in parameters
        log("reading in parameters")
        dem_layer = parameters[0].value
        dem = arcpy.Raster(dem_layer.name)
        z_unit = parameters[1].value
        extent = parameters[2].value
        output_file = parameters[3].valueAsText

        # set analysis extent
        if extent:
            arcpy.env.extent = extent

        # create neighborhoods
        map_unit = active_map.mapUnits
        width_300 = 300 * arcpy.LinearUnitConversionFactor("Meters", map_unit)
        height_300 = width_300
        width_2000 = 2000 * arcpy.LinearUnitConversionFactor("Meters", map_unit)
        height_2000 = width_2000
        neighborhood_300 = arcpy.sa.NbrRectangle(width_300, height_300, "MAP")
        neighborhood_2000 = arcpy.sa.NbrRectangle(width_2000, height_2000, "MAP")

        # calculate TPI's at 300m and 2000m scale
        log("calculating topographic position index at 300m and 2000m scale")
        tpi_300 = topographic_position_index(dem, neighborhood_300)
        tpi_2000 = topographic_position_index(dem, neighborhood_2000)

        # slope
        log("calculating slope")
        slope = arcpy.sa.Slope(dem, "DEGREE", "", "GEODESIC", z_unit)

        # reclassify rasters to combine them
        # ABC
        # A (300) -   100 = < -100
        #             200 = -100 < raster < 100
        #             300 = > 100
        # B (2000) -  10 = < -100
        #             20 = -100 < raster < 100
        #             30 = > 100
        # C (slope) - 1 = <  5
        #             2 = > 5
        #
        # 111 - V-shaped valley or deep narrow canyon
        # 112 - V-shaped valley or deep narrow canyon
        # 121 - Lateral midslope incised drainages or local valleys in plains
        # 122 - Lateral midslope incised drainages or local valleys in plains
        # 131 - Upland incised drainages or stream headwaters
        # 132 - Upland incised drainages or stream headwaters
        # 211 - U-shaped valley
        # 212 - U-shaped valley
        # 221 - Broad flat area
        # 222 - Broad open slope
        # 231 - Flat ridge top
        # 232 - Flat ridge top
        # 311 - Local ridge / hilltop within broad valley
        # 312 - Local ridge / hilltop within broad valley
        # 321 - Lateral midslope drainage divises and local ridges in plains
        # 322 - Lateral midslope drainage divises and local ridges in plains
        # 331 - Mountain tops and high narrow ridges
        # 332 - Mountain tops and high narrow ridges

        log("remap 300m TPI")
        remap_300 = arcpy.sa.RemapRange([[-100000, -100, 100], [-100, 100, 200], [100, 100000, 300]])
        tpi_300_remap = arcpy.sa.Reclassify(tpi_300, "VALUE", remap_300)

        log("remap 2000m TPI")
        remap_2000 = arcpy.sa.RemapRange([[-100000, -100, 10], [-100, 100, 20], [100, 100000, 30]])
        tpi_2000_remap = arcpy.sa.Reclassify(tpi_2000, "VALUE", remap_2000)

        log("remap slope")
        remap_slope = arcpy.sa.RemapRange([[0, 5, 1], [5, 90, 2]])
        slope_remap = arcpy.sa.Reclassify(slope, "VALUE", remap_slope, "NODATA")

        # add rasters together
        log("combining rasters")
        combined = tpi_300_remap + tpi_2000_remap + slope_remap
        combined.save(output_file)

        # add description field
        description_field = "description"
        if description_field not in [f.name for f in arcpy.ListFields(output_file)]:
            log("add descriptive land position field")
            arcpy.management.AddField(
                in_table=output_file,
                field_name=description_field,
                field_type="TEXT",
            )

        # classify output values into corresponding landforms
        log("classify output into landforms")
        arcpy.management.CalculateField(
            in_table=output_file,
            field=description_field,
            expression="calculate_value(!Value!)",
            expression_type="PYTHON3",
            code_block="""def calculate_value(id):
                if id == 111:
                    return "V-shaped valley or deep narrow canyon"
                elif id == 112:
                    return "V-shaped valley or deep narrow canyon"
                elif id == 121:
                    return "Lateral midslope incised ids or local valleys in plains"
                elif id == 122:
                    return "Lateral midslope incised drainages or local valleys in plains"
                elif id == 131:
                    return "Upland incised drainages or stream headwaters"
                elif id == 132:
                    return "Upland incised drainages or stream headwaters"
                elif id == 211:
                    return "U-shaped valley"
                elif id == 212:
                    return "U-shaped valley"
                elif id == 221:
                    return "Broad flat area"
                elif id == 222:
                    return "Broad open slope"
                elif id == 231:
                    return "Flat ridge top"
                elif id == 232:
                    return "Flat ridge top"
                elif id == 311:
                    return "Local ridge / hilltop within broad valley"
                elif id == 312:
                    return "Local ridge / hilltop within broad valley"
                elif id == 321:
                    return "Lateral midslope drainage divises and local ridges in plains"
                elif id == 322:
                    return "Lateral midslope drainage divises and local ridges in plains"
                elif id == 331:
                    return "Mountain tops and high narrow ridges"
                elif id == 332:
                    return "Mountain tops and high narrow ridges"
            """,
            field_type="TEXT",
            enforce_domains="NO_ENFORCE_DOMAINS"
        )

        # add results to map
        log("adding results to map")
        active_map.addDataFromPath(output_file)

        # save project
        log("saving project")
        project.save()

        return
