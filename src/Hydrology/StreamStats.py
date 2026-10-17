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
from helpers.units import AREAL_UNITS


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
        param4.filter.list = ["bankfull_discharge", "bankfull_width", "bankfull_depth", "bankfull_area", "q1_25", "q1_5", "q2", "q5", "q10", "q25", "q50", "q100", "q200", "q500"]

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
        # get drainage area sdffield
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
        conv_factor = arcpy.ArealUnitConversionFactor(str(areal_unit), str(AREAL_UNITS.SquareMilesUS))
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
            if field not in fields_ex:
                log(f"adding and calculating field: {field}")
                arcpy.management.AddField(
                    in_table=output_file,
                    field_name=field,
                    field_type="FLOAT",
                )
            else:
                log(f"calculating field: {field}")

            # calculate values from regression equations
            if field == "bankfull_discharge":
                arcpy.management.CalculateField(
                    in_table=output_file,
                    field=field,
                    expression=f"calculate_value(!RegionID91!, !{drainage_area_field}!, {conv_factor})",
                    expression_type="PYTHON3",
                    code_block="""def calculate_value(id, da, cf):
                        if id == "1":
                            return 49.6*(da*cf)**0.849
                        elif id == "2":
                            return 49.6*(da*cf)**0.849
                        elif id == "3":
                            return 83.8*(da*cf)**0.679
                        elif id == "4":
                            return 117.2*(da*cf)**0.780
                        elif id == "4A":
                            return 30.3*(da*cf)**0.980
                        elif id == "5":
                            return 45.3*(da*cf)**0.856
                        elif id == "6":
                            return 48.0*(da*cf)**0.842
                        elif id == "7":
                            return 37.1*(da*cf)**0.756
                    """,
                    field_type="FLOAT",
                    enforce_domains="NO_ENFORCE_DOMAINS"
                )
            elif field == "bankfull_width":
                arcpy.management.CalculateField(
                    in_table=output_file,
                    field=field,
                    expression=f"calculate_value(!RegionID91!, !{drainage_area_field}!, {conv_factor})",
                    expression_type="PYTHON3",
                    code_block="""def calculate_value(id, da, cf):
                        if id == "1":
                            return 21.5*(da*cf)**0.362
                        elif id == "2":
                            return 21.5*(da*cf)**0.362
                        elif id == "3":
                            return 24.0*(da*cf)**0.292
                        elif id == "4":
                            return 17.1*(da*cf)**0.460
                        elif id == "4A":
                            return 9.1*(da*cf)**0.545
                        elif id == "5":
                            return 13.5*(da*cf)**0.449
                        elif id == "6":
                            return 16.9*(da*cf)**0.419
                        elif id == "7":
                            return 10.8*(da*cf)**0.458
                    """,
                    field_type="FLOAT",
                    enforce_domains="NO_ENFORCE_DOMAINS"
                )
            elif field == "bankfull_depth":
                arcpy.management.CalculateField(
                    in_table=output_file,
                    field=field,
                    expression=f"calculate_value(!RegionID91!, !{drainage_area_field}!, {conv_factor})",
                    expression_type="PYTHON3",
                    code_block="""def calculate_value(id, da, cf):
                        if id == "1":
                            return 1.06*(da*cf)**0.329
                        elif id == "2":
                            return 1.06*(da*cf)**0.329
                        elif id == "3":
                            return 1.66*(da*cf)**0.210
                        elif id == "4":
                            return 1.07*(da*cf)**0.314
                        elif id == "4A":
                            return 0.79*(da*cf)**0.350
                        elif id == "5":
                            return 0.82*(da*cf)**0.373
                        elif id == "6":
                            return 1.04*(da*cf)**0.244
                        elif id == "7":
                            return 1.47*(da*cf)**0.199
                    """,
                    field_type="FLOAT",
                    enforce_domains="NO_ENFORCE_DOMAINS"
                )
            elif field == "bankfull_area":
                arcpy.management.CalculateField(
                    in_table=output_file,
                    field=field,
                    expression=f"calculate_value(!RegionID91!, !{drainage_area_field}!, {conv_factor})",
                    expression_type="PYTHON3",
                    code_block="""def calculate_value(id, da, cf):
                        if id == "1":
                            return 22.3*(da*cf)**0.694
                        elif id == "2":
                            return 22.3*(da*cf)**0.694
                        elif id == "3":
                            return 39.8*(da*cf)**0.503
                        elif id == "4":
                            return 17.9*(da*cf)**0.777
                        elif id == "4A":
                            return 7.2*(da*cf)**0.894
                        elif id == "5":
                            return 10.8*(da*cf)**0.823
                        elif id == "6":
                            return 17.6*(da*cf)**0.662
                        elif id == "7":
                            return 15.9*(da*cf)**0.656
                    """,
                    field_type="FLOAT",
                    enforce_domains="NO_ENFORCE_DOMAINS"
                )
            elif field == "q1_25":
                arcpy.management.CalculateField(
                    in_table=output_file,
                    field=field,
                    expression=f"calculate_value(!RegionID06!, !{drainage_area_field}!, {conv_factor})",
                    expression_type="PYTHON3",
                    code_block="""def calculate_value(id, da, cf):
                        if id == "1":
                            return 31.7*(da*cf)**0.857
                        elif id == "2":
                            return 43.4*(da*cf)**0.772
                        elif id == "3":
                            return 57.4*(da*cf)**0.861
                        elif id == "4":
                            return 39.1*(da*cf)**0.833
                        elif id == "5":
                            return 54.8*(da*cf)**0.800
                        elif id == "6":
                            return 31.1*(da*cf)**0.783
                    """,
                    field_type="FLOAT",
                    enforce_domains="NO_ENFORCE_DOMAINS"
                )
            elif field == "q1_5":
                arcpy.management.CalculateField(
                    in_table=output_file,
                    field=field,
                    expression=f"calculate_value(!RegionID06!, !{drainage_area_field}!, {conv_factor})",
                    expression_type="PYTHON3",
                    code_block="""def calculate_value(id, da, cf):
                        if id == "1":
                            return 38.5*(da*cf)**0.848
                        elif id == "2":
                            return 56.1*(da*cf)**0.758
                        elif id == "3":
                            return 71.8*(da*cf)**0.857
                        elif id == "4":
                            return 48.7*(da*cf)**0.823
                        elif id == "5":
                            return 71.5*(da*cf)**0.785
                        elif id == "6":
                            return 37.2*(da*cf)**0.782
                    """,
                    field_type="FLOAT",
                    enforce_domains="NO_ENFORCE_DOMAINS"
                )
            # "q10", "q25", "q50", "q100", "q200", "q500"
            elif field == "q2":
                arcpy.management.CalculateField(
                    in_table=output_file,
                    field=field,
                    expression=f"calculate_value(!RegionID06!, !{drainage_area_field}!, {conv_factor})",
                    expression_type="PYTHON3",
                    code_block="""def calculate_value(id, da, cf):
                        if id == "1":
                            return 47.6*(da*cf)**0.839
                        elif id == "2":
                            return 74.7*(da*cf)**0.743
                        elif id == "3":
                            return 90.8*(da*cf)**0.853
                        elif id == "4":
                            return 61.3*(da*cf)**0.812
                        elif id == "5":
                            return 95.4*(da*cf)**0.770
                        elif id == "6":
                            return 44.5*(da*cf)**0.782
                    """,
                    field_type="FLOAT",
                    enforce_domains="NO_ENFORCE_DOMAINS"
                )
            # q10", "q25", "q50", "q100", "q200", "q500"
            elif field == "q5":
                arcpy.management.CalculateField(
                    in_table=output_file,
                    field=field,
                    expression=f"calculate_value(!RegionID06!, !{drainage_area_field}!, {conv_factor})",
                    expression_type="PYTHON3",
                    code_block="""def calculate_value(id, da, cf):
                        if id == "1":
                            return 73.0*(da*cf)**0.822
                        elif id == "2":
                            return 139.0*(da*cf)**0.712
                        elif id == "3":
                            return 144.0*(da*cf)**0.850
                        elif id == "4":
                            return 97.4*(da*cf)**0.788
                        elif id == "5":
                            return 172*(da*cf)**38
                        elif id == "6":
                            return 62.7*(da*cf)**0.788
                    """,
                    field_type="FLOAT",
                    enforce_domains="NO_ENFORCE_DOMAINS"
                )
            # "q25", "q50", "q100", "q200", "q500"
            elif field == "q10":
                arcpy.management.CalculateField(
                    in_table=output_file,
                    field=field,
                    expression=f"calculate_value(!RegionID06!, !{drainage_area_field}!, {conv_factor})",
                    expression_type="PYTHON3",
                    code_block="""def calculate_value(id, da, cf):
                        if id == "1":
                            return 92.1*(da*cf)**0.813
                        elif id == "2":
                            return 197*(da*cf)**0.695
                        elif id == "3":
                            return 185*(da*cf)**0.848
                        elif id == "4":
                            return 124*(da*cf)**0.775
                        elif id == "5":
                            return 237*(da*cf)**0.722
                        elif id == "6":
                            return 74.2*(da*cf)**0.794
                    """,
                    field_type="FLOAT",
                    enforce_domains="NO_ENFORCE_DOMAINS"
                )
            elif field == "q25":
                arcpy.management.CalculateField(
                    in_table=output_file,
                    field=field,
                    expression=f"calculate_value(!RegionID06!, !{drainage_area_field}!, {conv_factor})",
                    expression_type="PYTHON3",
                    code_block="""def calculate_value(id, da, cf):
                        if id == "1":
                            return 119*(da*cf)**0.802
                        elif id == "2":
                            return 291*(da*cf)**0.677
                        elif id == "3":
                            return 249*(da*cf)**0.843
                        elif id == "4":
                            return 161*(da*cf)**0.761
                        elif id == "5":
                            return 332*(da*cf)**0.706
                        elif id == "6":
                            return 88.4*(da*cf)**0.801
                    """,
                    field_type="FLOAT",
                    enforce_domains="NO_ENFORCE_DOMAINS"
                )
            elif field == "q50":
                arcpy.management.CalculateField(
                    in_table=output_file,
                    field=field,
                    expression=f"calculate_value(!RegionID06!, !{drainage_area_field}!, {conv_factor})",
                    expression_type="PYTHON3",
                    code_block="""def calculate_value(id, da, cf):
                        if id == "1":
                            return 140*(da*cf)**0.796
                        elif id == "2":
                            return 378*(da*cf)**0.666
                        elif id == "3":
                            return 304*(da*cf)**0.840
                        elif id == "4":
                            return 191*(da*cf)**0.751
                        elif id == "5":
                            return 412*(da*cf)**0.695
                        elif id == "6":
                            return 98.5*(da*cf)**0.807
                    """,
                    field_type="FLOAT",
                    enforce_domains="NO_ENFORCE_DOMAINS"
                )
            elif field == "q100":
                arcpy.management.CalculateField(
                    in_table=output_file,
                    field=field,
                    expression=f"calculate_value(!RegionID06!, !{drainage_area_field}!, {conv_factor})",
                    expression_type="PYTHON3",
                    code_block="""def calculate_value(id, da, cf):
                        if id == "1":
                            return 162*(da*cf)**0.790
                        elif id == "2":
                            return 480*(da*cf)**0.656
                        elif id == "3":
                            return 367*(da*cf)**0.836
                        elif id == "4":
                            return 221*(da*cf)**0.743
                        elif id == "5":
                            return 502*(da*cf)**0.687
                        elif id == "6":
                            return 108*(da*cf)**0.813
                    """,
                    field_type="FLOAT",
                    enforce_domains="NO_ENFORCE_DOMAINS"
                )
            elif field == "q200":
                arcpy.management.CalculateField(
                    in_table=output_file,
                    field=field,
                    expression=f"calculate_value(!RegionID06!, !{drainage_area_field}!, {conv_factor})",
                    expression_type="PYTHON3",
                    code_block="""def calculate_value(id, da, cf):
                        if id == "1":
                            return 186*(da*cf)**0.785
                        elif id == "2":
                            return 598*(da*cf)**0.648
                        elif id == "3":
                            return 436*(da*cf)**0.832
                        elif id == "4":
                            return 253*(da*cf)**0.735
                        elif id == "5":
                            return 600*(da*cf)**0.679
                        elif id == "6":
                            return 117*(da*cf)**0.818
                    """,
                    field_type="FLOAT",
                    enforce_domains="NO_ENFORCE_DOMAINS"
                )
            elif field == "q500":
                arcpy.management.CalculateField(
                    in_table=output_file,
                    field=field,
                    expression=f"calculate_value(!RegionID06!, !{drainage_area_field}!, {conv_factor})",
                    expression_type="PYTHON3",
                    code_block="""def calculate_value(id, da, cf):
                        if id == "1":
                            return 219*(da*cf)**0.779
                        elif id == "2":
                            return 782*(da*cf)**0.638
                        elif id == "3":
                            return 539*(da*cf)**0.827
                        elif id == "4":
                            return 298*(da*cf)**0.727
                        elif id == "5":
                            return 745*(da*cf)**0.670
                        elif id == "6":
                            return 129*(da*cf)**0.826
                    """,
                    field_type="FLOAT",
                    enforce_domains="NO_ENFORCE_DOMAINS"
                )


        # add results to map
        log("adding results to map")
        active_map.addDataFromPath(output_file)

        # save project
        log("saving project")
        project.save()
