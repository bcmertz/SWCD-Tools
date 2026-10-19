# --------------------------------------------------------------------------------------------------
# Name:        StreamStats
# Purpose:     Calculate peak flow and bankfull statistics
#
# License:     Contextual Copyleft AI (CCAI) License v1.0.
#              Full license in LICENSE file.
# --------------------------------------------------------------------------------------------------

import os

import arcpy

from helpers.logging import log
from helpers.parameter import validate_spatial_reference as validate
from helpers.tool import EXTENSIONS, license, reload_module
from helpers.tool import setup_environment as setup
from helpers.units import AREAL_UNITS, Area

STREAM_STATS_FIELD_MAPPING = {
    "Bankfull Discharge (cfs)": "bankfull_discharge",
    "Bankfull Width (ft)": "bankfull_width",
    "Bankfull Depth (ft)": "bankfull_depth",
    "Bankfull Area (ft^2)": "bankfull_area",
    "Q 1.25 (cfs)": "q1_25",
    "Q 1.5 (cfs)": "q1_5",
    "Q 2 (cfs)": "q2",
    "Q 5 (cfs)": "q5",
    "Q 10 (cfs)": "q10",
    "Q 25 (cfs)": "q25",
    "Q 50 (cfs)": "q50",
    "Q 100 (cfs)": "q100",
    "Q 200 (cfs)": "q200",
    "Q 500 (cfs)": "q500",
}

def calculate_statistics(region91: str, region06: str, field: str, drainage_area: Area):
    da = drainage_area.to_unit(AREAL_UNITS.SquareMilesUS).area
    if field == "bankfull_discharge":
        match region91:
            case "1":
                return 49.6*da**0.849
            case "2":
                return 49.6*da**0.849
            case "3":
                return 83.8*da**0.679
            case "4":
                return 117.2*da**0.780
            case "4A":
                return 30.3*da**0.980
            case "5":
                return 45.3*da**0.856
            case "6":
                return 48.0*da**0.842
            case "7":
                return 37.1*da**0.756
    elif field == "bankfull_width":
        match region91:
            case "1":
                return 21.5*da**0.362
            case "2":
                return 21.5*da**0.362
            case "3":
                return 24.0*da**0.292
            case "4":
                return 17.1*da**0.460
            case "4A":
                return 9.1*da**0.545
            case "5":
                return 13.5*da**0.449
            case "6":
                return 16.9*da**0.419
            case "7":
                return 10.8*da**0.458
    elif field == "bankfull_depth":
        match region91:
            case "1":
                return 1.06*da**0.329
            case "2":
                return 1.06*da**0.329
            case "3":
                return 1.66*da**0.210
            case "4":
                return 1.07*da**0.314
            case "4A":
                return 0.79*da**0.350
            case "5":
                return 0.82*da**0.373
            case "6":
                return 1.04*da**0.244
            case "7":
                return 1.47*da**0.199
    elif field == "bankfull_area":
        match region91:
            case "1":
                return 22.3*da**0.694
            case "2":
                return 22.3*da**0.694
            case "3":
                return 39.8*da**0.503
            case "4":
                return 17.9*da**0.777
            case "4A":
                return 7.2*da**0.894
            case "5":
                return 10.8*da**0.823
            case "6":
                return 17.6*da**0.662
            case "7":
                return 15.9*da**0.656
    elif field == "q1_25":
        match region06:
            case "1":
                return 31.7*da**0.857
            case "2":
                return 43.4*da**0.772
            case "3":
                return 57.4*da**0.861
            case "4":
                return 39.1*da**0.833
            case "5":
                return 54.8*da**0.800
            case "6":
                return 31.1*da**0.783
    elif field == "q1_5":
        match region06:
            case "1":
                return 38.5*da**0.848
            case "2":
                return 56.1*da**0.758
            case "3":
                return 71.8*da**0.857
            case "4":
                return 48.7*da**0.823
            case "5":
                return 71.5*da**0.785
            case "6":
                return 37.2*da**0.782
    elif field == "q2":
        match region06:
            case "1":
                return 47.6*da**0.839
            case "2":
                return 74.7*da**0.743
            case "3":
                return 90.8*da**0.853
            case "4":
                return 61.3*da**0.812
            case "5":
                return 95.4*da**0.770
            case "6":
                return 44.5*da**0.782
    elif field == "q5":
        match region06:
            case "1":
                return 73.0*da**0.822
            case "2":
                return 139.0*da**0.712
            case "3":
                return 144.0*da**0.850
            case "4":
                return 97.4*da**0.788
            case "5":
                return 172*da**38
            case "6":
                return 62.7*da**0.788
    elif field == "q10":
        match region06:
            case "1":
                return 92.1*da**0.813
            case "2":
                return 197*da**0.695
            case "3":
                return 185*da**0.848
            case "4":
                return 124*da**0.775
            case "5":
                return 237*da**0.722
            case "6":
                return 74.2*da**0.794
    elif field == "q25":
        match region06:
            case "1":
                return 119*da**0.802
            case "2":
                return 291*da**0.677
            case "3":
                return 249*da**0.843
            case "4":
                return 161*da**0.761
            case "5":
                return 332*da**0.706
            case "6":
                return 88.4*da**0.801
    elif field == "q50":
        match region06:
            case "1":
                return 140*da**0.796
            case "2":
                return 378*da**0.666
            case "3":
                return 304*da**0.840
            case "4":
                return 191*da**0.751
            case "5":
                return 412*da**0.695
            case "6":
                return 98.5*da**0.807
    elif field == "q100":
        match region06:
            case "1":
                return 162*da**0.790
            case "2":
                return 480*da**0.656
            case "3":
                return 367*da**0.836
            case "4":
                return 221*da**0.743
            case "5":
                return 502*da**0.687
            case "6":
                return 108*da**0.813
    elif field == "q200":
        match region06:
            case "1":
                return 186*da**0.785
            case "2":
                return 598*da**0.648
            case "3":
                return 436*da**0.832
            case "4":
                return 253*da**0.735
            case "5":
                return 600*da**0.679
            case "6":
                return 117*da**0.818
    elif field == "q500":
        match region06:
            case "1":
                return 219*da**0.779
            case "2":
                return 782*da**0.638
            case "3":
                return 539*da**0.827
            case "4":
                return 298*da**0.727
            case "5":
                return 745*da**0.670
            case "6":
                return 129*da**0.826

class StreamStats:
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "StreamStats"
        self.description = "Calculate peak flow and bankfull statistics"
        self.category = "Hydrology"

    def getParameterInfo(self):
        """Define parameter definitions"""
        param0 = arcpy.Parameter(
            displayName="Stream Line Mask",
            name="stream",
            datatype="GPFeatureLayer",
            parameterType="Optional",
            direction="Input")
        param0.filter.list = ["Polyline"]

        param1 = arcpy.Parameter(
            displayName="Drainage Area Field",
            name="drainage_area_field",
            datatype="GPString",
            parameterType="Required",
            direction="Input",
        )
        param1.filter.type = "ValueList"
        param1.filter.list = []

        param2 = arcpy.Parameter(
            displayName="Drainage Area Unit",
            name="unit",
            datatype="GPString",
            parameterType="Required",
            direction="Input")
        param2.filter.list = list(AREAL_UNITS)

        param3 = arcpy.Parameter(
            displayName="Analysis Area",
            name="analysis_area",
            datatype="GPExtent",
            parameterType="Optional",
            direction="Input")
        param3.controlCLSID = '{15F0D1C1-F783-49BC-8D16-619B8E92F668}'

        param4 = arcpy.Parameter(
            displayName="Statistics to calculate",
            name="fields",
            datatype="GPString",
            parameterType="Required",
            multiValue=True,
            direction="Input")
        param4.filter.list = list(STREAM_STATS_FIELD_MAPPING.keys())

        param5 = arcpy.Parameter(
            displayName="Output Features",
            name="out_features",
            datatype="DEFeatureClass",
            parameterType="Required",
            direction="Output")
        param5.parameterDependencies = [param0.name]
        param5.schema.clone = True

        params = [param0, param1, param2, param3, param4, param5]
        return params

    def isLicensed(self):
        """Set whether the tool is licensed to execute."""
        return license([EXTENSIONS.Spatial])

    def updateParameters(self, parameters):
        # get drainage area
        if not parameters[0].hasBeenValidated:
            if parameters[0].value:
                parameters[1].enabled = True
                fields = [field.name for field in arcpy.ListFields(parameters[0].value)]
                parameters[1].filter.list = fields
            else:
                parameters[1].enabled = False

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool parameter."""
        validate(parameters)

    @reload_module(__name__)
    def execute(self, parameters, _messages):
        """The source code of the tool."""
        # Setup
        log("setting up project")
        project, active_map = setup()

        # read in parameters
        log("reading in parameters")
        streams = parameters[0].value
        drainage_area_field = parameters[1].value
        areal_unit = AREAL_UNITS(parameters[2].valueAsText)
        extent = parameters[3].value
        fields = parameters[4].valueAsText.replace("'","").split(";")
        output_file = parameters[5].valueAsText

        # set analysis extent
        if extent:
            arcpy.env.extent = extent

        # create scratch layers
        scratch_streams = arcpy.CreateScratchName("streams", data_type="FeatureClass", workspace=arcpy.env.scratchGDB)

        # hydrologic information
        hydrologic_regions_91 = os.path.join(os.path.dirname(__file__), os.pardir, os.pardir, 'assets', 'NY Hydrologic Regions', 'NY_Hydrologic_Regions_91.shp')
        hydrologic_regions_06 = os.path.join(os.path.dirname(__file__), os.pardir, os.pardir, 'assets', 'NY Hydrologic Regions', 'NY_Hydrologic_Regions_06.shp')

        # intersect streams and hydrologic regions to get Region ID
        log("intersect stream lines with hydrologic regions info")
        arcpy.analysis.PairwiseIntersect(
            in_features=[streams, hydrologic_regions_91],
            out_feature_class=scratch_streams,
            join_attributes="ALL",
            cluster_tolerance=None,
            output_type="LINE"
        )
        arcpy.analysis.PairwiseIntersect(
            in_features=[scratch_streams, hydrologic_regions_06],
            out_feature_class=output_file,
            join_attributes="ALL",
            cluster_tolerance=None,
            output_type="LINE"
        )

        # add required fields
        fields_ex = [f.name for f in arcpy.ListFields(output_file)]
        for field in fields:
            field_name = STREAM_STATS_FIELD_MAPPING[field]
            field_alias = field

            if field not in fields_ex:
                log(f"adding and calculating field: {field_alias}")
                arcpy.management.AddField(
                    in_table=output_file,
                    field_name=field_name,
                    field_type="FLOAT",
                    field_alias=field_alias,
                )
            else:
                log(f"calculating field: {field_alias}")

            # calculate values from regression equations
            # for update cursor
            with arcpy.da.UpdateCursor(output_file, [drainage_area_field, "RegionID91", "RegionID06", field_name]) as cursor:
                for line in cursor:
                    da, region91, region06 = line[0], line[1], line[2]
                    da = Area(da, areal_unit)
                    line[3] = calculate_statistics(region91, region06, field_name, da)
                    cursor.updateRow(line)

        # add results to map
        log("adding results to map")
        active_map.addDataFromPath(output_file)

        # save project
        log("saving project")
        project.save()
