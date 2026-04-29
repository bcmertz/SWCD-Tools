# --------------------------------------------------------------------------------------------------
# Name:        Valley Bottom Extraction Tool
# Purpose:     Extract valley bottom geometry
#
# License:     Contextual Copyleft AI (CCAI) License v1.0.
#              Full license in LICENSE file.
# --------------------------------------------------------------------------------------------------

# TODO: documentation, lit review, attribution

import arcpy

from ..helpers import license, reload_module, log, empty_workspace, convert_length, cell_length, convert_length, get_z_unit, Z_UNITS, AREAL_UNITS, AREAL_UNITS_MAP
from ..helpers import setup_environment as setup
from ..helpers import validate_spatial_reference as validate

class VBET(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Valley Bottom Extraction Tool (VBET)"
        self.description = "Extract valley bottom geometry"
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
            displayName="REM",
            name="rem",
            datatype="GPRasterLayer",
            parameterType="Optional",
            direction="Input")

        param4 = arcpy.Parameter(
            displayName="Stream Lines",
            name="stream",
            datatype="GPFeatureLayer",
            parameterType="Required",
            direction="Input")
        param4.filter.list = ["Polyline"]

        param5 = arcpy.Parameter(
            displayName="Watershed Size Field",
            name="watershed_size_field",
            datatype="GPString",
            parameterType="Required",
            direction="Input")
        param5.filter.type = "ValueList"
        param5.filter.list = []

        param6 = arcpy.Parameter(
            displayName="Watershed Area Unit",
            name="unit",
            datatype="GPString",
            parameterType="Required",
            direction="Input")
        param6.filter.list = AREAL_UNITS

        param7 = arcpy.Parameter(
            displayName="Buffer Radius",
            name="buffer_radius",
            datatype="GPLinearUnit",
            parameterType="Required",
            direction="Input")

        param8 = arcpy.Parameter(
            displayName="Minimum watershed size",
            name="min_watershed",
            datatype="GPArealUnit",
            parameterType="Optional",
            direction="Input")
        param8.value = "1 SquareKilometers"

        param9 = arcpy.Parameter(
            displayName="Valley Bottom Output Feature",
            name="valley_bottom",
            datatype="DEFeatureClass",
            parameterType="Required",
            direction="Output")
        param9.parameterDependencies = [param0.name]
        param9.schema.clone = True

        param10 = arcpy.Parameter(
            displayName="Low-Lying Valley Output Feature",
            name="low_lying",
            datatype="DEFeatureClass",
            parameterType="Required",
            direction="Output")
        param10.parameterDependencies = [param0.name]
        param10.schema.clone = True

        params = [param0, param1, param2, param3, param4, param5, param6, param7, param8, param9, param10]
        return params

    def isLicensed(self):
        """Set whether the tool is licensed to execute."""
        return license(['Spatial', 'ImageAnalyst'], version_required="v3.3") # 3.3 of greater required for python match case

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

        # get watershed size field
        if not parameters[4].hasBeenValidated:
            if parameters[4].value:
                parameters[5].enabled = True
                fields2 = [f2.name for f2 in arcpy.ListFields(parameters[4].value)]
                parameters[5].filter.list = fields2
                parameters[6].enabled = True
            else:
                parameters[5].enabled = False
                parameters[6].enabled = False

        # default buffer radius
        if parameters[7].value is None:
            parameters[7].value = "1000 Meters"

        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool parameter."""
        validate(parameters)

        return

    @reload_module(__name__)
    def execute(self, parameters, _):
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
        rem_layer = parameters[3].value
        rem = arcpy.Raster(rem_layer.name)
        streams = parameters[4].value
        watershed_size_field = parameters[5].valueAsText
        watershed_area_unit = AREAL_UNITS_MAP[parameters[6].valueAsText]
        buffer_radius = parameters[7].valueAsText
        min_watershed_size, min_watershed_unit =  parameters[8].valueAsText.split(" ") if parameters[8].value is not None else (None, None)
        full_valley_file = parameters[9].valueAsText
        low_lying_file = parameters[10].valueAsText

        # set analysis extent
        if extent:
            log("setting analysis extent")
            arcpy.env.extent = extent

        # create scratch layers
        log("creating scratch layers")
        scratch_buffer = arcpy.CreateScratchName("buffer", data_type="FeatureClass", workspace=arcpy.env.scratchGDB)
        scratch_area = arcpy.CreateScratchName("area", data_type="FeatureClass", workspace=arcpy.env.scratchGDB)

        # buffer streams, each stream segment a separate buffer segment
        log("creating buffer around stream lines")
        arcpy.analysis.PairwiseBuffer(
            in_features=streams,
            out_feature_class=scratch_buffer,
            buffer_distance_or_field=buffer_radius,
            dissolve_option="NONE",
            dissolve_field=None,
            method="GEODESIC",
        )

        # set analysis mask to buffered area
        arcpy.env.mask = scratch_buffer

        # create slope inside buffer area
        #
        # Difference from VBET 2.0 - we don't IDW slope evidence...
        # the HAND raster is already IDW'd so this isn't necessary
        # in order to exclude effects of far away streams processing
        log("calculating slope")
        slope = arcpy.sa.Slope(dem, "DEGREE", "", "GEODESIC", z_unit)

        # TODO: optionally create REM

        # get threshold watershed sizes in km^2
        log("creating watershed size thresholds")
        threshold_low = 25 * arcpy.ArealUnitConversionFactor("SquareKilometers", watershed_area_unit)
        threshold_high = 250 * arcpy.ArealUnitConversionFactor("SquareKilometers", watershed_area_unit)
        if min_watershed_size is not None:
            min_watershed_size = float(min_watershed_size) * arcpy.ArealUnitConversionFactor(min_watershed_unit, watershed_area_unit)

        # TODO: check the min_watershed_size check is working
        queries = [
            "{} > {} and {} < {}".format(watershed_size_field, min_watershed_size, watershed_size_field,threshold_low)\
            if min_watershed_size is not None else "{} < {}".format(watershed_size_field,threshold_low),
            "{} > {} And {} < {}".format(watershed_size_field,threshold_low,watershed_size_field,threshold_high),
            "{} > {}".format(watershed_size_field,threshold_high)
        ]

        # iterate through each buffer size (<25km^2, 25-250km^2, >250km^2)
        evidence_low = None
        evidence_med = None
        evidence_high = None
        i = 0
        for sql_query in queries:
            # create new buffer in the relevant watershed size
            arcpy.conversion.ExportFeatures(
                in_features=scratch_buffer,
                out_features=scratch_area,
                where_clause=sql_query,
            )

            # calculate rem + slope evidence based off of watershed size
            rem_tmp = rem
            slope_tmp = slope
            match i:
                case 0: # small watershed
                    log("finding small watershed valley bottom probability")
                    slope_tmp = arcpy.sa.Exp(-0.12 * slope_tmp)
                    rem_tmp = 1 / (1 + arcpy.sa.Exp(-3.653 + 1.04 * rem_tmp))
                    evidence_low = 0.65 * rem_tmp + 0.35 * slope_tmp
                case 1: # medium watershed
                    log("finding medium watershed valley bottom probability")
                    slope_tmp = arcpy.sa.Exp(-0.2 * slope_tmp)
                    rem_tmp = 1 / (1 + arcpy.sa.Exp(-3.86 + 0.717 * rem_tmp))
                    evidence_med = 0.65 * rem_tmp + 0.35 * slope_tmp
                case 2: # large watershed
                    log("finding large watershed valley bottom probability")
                    slope_tmp = arcpy.sa.Exp(-0.3 * slope_tmp)
                    rem_tmp = 1 / (1 + arcpy.sa.Exp(-3.652 + 0.432 * rem_tmp))
                    evidence_high = 0.65 * rem_tmp + 0.35 * slope_tmp

            # iterate to keep track of watershed size
            i += 1

        # combine 3 probability rasters into 1, taking highest probability value as actual
        log("combining probabilities into output")
        rc = arcpy.ia.RasterCollection([evidence_low, evidence_med, evidence_high])
        max_raster = arcpy.ia.Max(
            rasters=rc,
            extent_type = "UnionOf",
            cellsize_type = "MinOf",
	    ignore_nodata = True,
        )

        # threshold to full valley bottom and low-lying valley bottom
        #
        # full valley bottom = 0.65, low lying valley bottom = 0.85
        log("thresholding output probability to find full valley bottom and low-lying valley bottom areas")
        full_valley = arcpy.sa.Con(max_raster, 1, where_clause="VALUE >= 0.65")
        low_lying = arcpy.sa.Con(max_raster, 1, where_clause="VALUE >= 0.85")

        # polygonize outputs
        log("converting outputs to polygons")
        arcpy.conversion.RasterToPolygon(full_valley, full_valley_file)
        arcpy.conversion.RasterToPolygon(low_lying, low_lying_file)

        # remove self intersections
        log("cleaning up geometry")
        arcpy.topographic.RepairSelfIntersection(
            in_features=full_valley_file,
            repair_type="DELETE",
            max_length=None,
            repair_at_end_point="REPAIR_ENDS"
        )
        arcpy.topographic.RepairSelfIntersection(
            in_features=low_lying_file,
            repair_type="DELETE",
            max_length=None,
            repair_at_end_point="REPAIR_ENDS"
        )

        # TODO: generate valley bottom centerline using least cost path

        # add results to map
        log("adding results to map")
        active_map.addDataFromPath(low_lying_file)
        active_map.addDataFromPath(full_valley_file)

        # save project
        log("saving project")
        project.save()

        # cleanup
        log("deleting unneeded data")
        empty_workspace(arcpy.env.scratchGDB, keep=[])

        return
