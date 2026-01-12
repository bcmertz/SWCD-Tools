# --------------------------------------------------------------------------------
# Name:        Runoff Curve Number
# Purpose:     This tool calculates runoff curve numbers (RCNs) for a given study
#              area.
#
# License:     GNU Affero General Public License v3.
#              Full license in LICENSE file, or at <https://www.gnu.org/licenses/>
# --------------------------------------------------------------------------------

import arcpy

from helpers import license, empty_workspace
from helpers import print_messages as log
from helpers import setup_environment as setup
from helpers import validate_spatial_reference as validate

class RunoffCurveNumber:
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Calculate Runoff Curve Numbers"
        self.category = "Hydrology"
        self.description = "Calculate the runoff curve numbers of a given watershed"

    def getParameterInfo(self):
        """Define parameter definitions"""
        param0 = arcpy.Parameter(
            displayName="Watershed Boundary Layer",
            name="watershed",
            datatype="GPFeatureLayer",
            parameterType="Required",
            direction="Input")
        param0.filter.list = ["Polygon"]
        param0.controlCLSID = '{60061247-BCA8-473E-A7AF-A2026DDE1C2D}' # allows polygon creation

        param1 = arcpy.Parameter(
            displayName="Output Features",
            name="out_features",
            datatype="DEFeatureClass",
            parameterType="Required",
            direction="Output")
        param1.parameterDependencies = [param0.name]

        param2 = arcpy.Parameter(
            displayName="Soils Feature Class",
            name="soils",
            datatype="GPFeatureLayer",
            parameterType="Required",
            direction="Input")
        param2.filter.list = ["Polygon"]

        param3 = arcpy.Parameter(
            displayName="HSG Field",
            name="hsg_field",
            datatype="GPString",
            parameterType="Required",
            direction="Input")
        param3.filter.type = "ValueList"
        param3.filter.list = []

        param4 = arcpy.Parameter(
            displayName="Land Use Data",
            name="land_use",
            datatype="GPRasterLayer",
            parameterType="Required",
            direction="Input")

        param5 = arcpy.Parameter(
            displayName="RCN Field - HSG A",
            name="rcn_field_a",
            datatype="GPString",
            parameterType="Required",
            direction="Input")
        param5.filter.type = "ValueList"
        param5.filter.list = []

        param6 = arcpy.Parameter(
            displayName="RCN Field - HSG B",
            name="rcn_field_b",
            datatype="GPString",
            parameterType="Required",
            direction="Input")
        param6.filter.type = "ValueList"
        param6.filter.list = []

        param7 = arcpy.Parameter(
            displayName="RCN Field - HSG C",
            name="rcn_field_c",
            datatype="GPString",
            parameterType="Required",
            direction="Input")
        param7.filter.type = "ValueList"
        param7.filter.list = []

        param8 = arcpy.Parameter(
            displayName="RCN Field - HSG D",
            name="rcn_field_d",
            datatype="GPString",
            parameterType="Required",
            direction="Input")
        param8.filter.type = "ValueList"
        param8.filter.list = []

        params = [param0, param1, param2, param3, param4, param5, param6, param7, param8]
        return params

    def isLicensed(self):
        """Set whether the tool is licensed to execute."""
        return license(['Spatial'])

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool parameter."""
        validate(parameters)

        warning_message = "In order to use this tool you must have land use / runoff curve number data. We recommend using Chesapeake Bay Land Use Data and modifying the raster to include fields for runoff curve number values for each hydrologic soil groups A,B,C,D."

        if parameters[4].value and (not parameters[5].value or not parameters[6].value or not parameters[7].value or not parameters[8].value):
            parameters[4].setWarningMessage(warning_message)
        else:
            if parameters[4].message == warning_message:
              parameters[4].clearMessage()

        return

    def updateParameters(self, parameters):
        # get soils field
        if not parameters[2].hasBeenValidated:
            if parameters[2].value:
                parameters[3].enabled = True
                fields = [f.name for f in arcpy.ListFields(parameters[2].value)]
                parameters[3].filter.list = fields
                if "hydgrpdcd" in fields:
                    parameters[3].value = "hydgrpdcd"
            else:
                parameters[3].enabled = False

        # get rcn fields
        if not parameters[4].hasBeenValidated:
            if parameters[4].value:
                parameters[5].enabled = True
                parameters[6].enabled = True
                parameters[7].enabled = True
                parameters[8].enabled = True
                fields2 = [f2.name for f2 in arcpy.ListFields(parameters[4].value)]
                parameters[5].filter.list = fields2
                parameters[6].filter.list = fields2
                parameters[7].filter.list = fields2
                parameters[8].filter.list = fields2
                if "RCNA" in fields2:
                    parameters[5].value = "RCNA"
                if "RCNB" in fields2:
                    parameters[6].value = "RCNB"
                if "RCNC" in fields2:
                    parameters[7].value = "RCNC"
                if "RCND" in fields2:
                    parameters[8].value = "RCND"                
            else:
                parameters[5].enabled = False
                parameters[6].enabled = False
                parameters[7].enabled = False
                parameters[8].enabled = False

        return

    def execute(self, parameters, messages):
        """The source code of the tool."""
        # Setup
        log("setting up project")
        project, active_map = setup()
        arcpy.env.qualifiedFieldNames = False

        # read in parameters
        watershed = parameters[0].value
        output_fc = parameters[1].valueAsText
        soils = parameters[2].value
        hsg_field = parameters[3].value
        land_use_raster = parameters[4].value
        rcn_field_a = parameters[5].value
        rcn_field_b = parameters[6].value
        rcn_field_c = parameters[7].value
        rcn_field_d = parameters[8].value

        # scratch layers
        log("creating scratch layers")
        soils_scratch = arcpy.CreateScratchName("soils_scratch", "FeatureClass", arcpy.env.scratchGDB)
        scratch_land_use_polygon = arcpy.CreateScratchName("scratch_land_use_polygon", "FeatureClass", arcpy.env.scratchGDB)
        scratch_joined_land_use_polygon = arcpy.CreateScratchName("scratch_joined_land_use_polygon", "FeatureClass", arcpy.env.scratchGDB)

        # clip soils
        log("clipping soils to watershed")
        arcpy.analysis.Clip(soils, watershed, soils_scratch)

        # clip land use raster
        log("clipping land use raster to watershed")
        land_use_raster_clip = arcpy.sa.ExtractByMask(land_use_raster, watershed, "INSIDE")

        # convert land usage output to polygon
        log("converting land use areas to polygon")
        arcpy.conversion.RasterToPolygon(land_use_raster_clip, scratch_land_use_polygon, "SIMPLIFY", "LandUse", "SINGLE_OUTER_PART")

        # join land use attributes to land use polygons
        log("join land use RCN fields into polygon")
        joined_land_use_polygon = arcpy.management.AddJoin(scratch_land_use_polygon, "LandUse", land_use_raster_clip, "LandUse", "KEEP_ALL", "INDEX_JOIN_FIELDS")
        arcpy.management.CopyFeatures(joined_land_use_polygon, scratch_joined_land_use_polygon)

        # intersect land use and soils
        log("intersect land uses and soils")
        arcpy.analysis.PairwiseIntersect(
            in_features=[scratch_joined_land_use_polygon, soils_scratch],
            out_feature_class=output_fc,
            join_attributes="ALL",
            cluster_tolerance=None,
            output_type="INPUT"
        )

        # calculate RCN from HSG
        log("calculate RCN from HSG")
        arcpy.management.CalculateField(
            in_table=output_fc,
            field="RCN",
            expression="calculate_value(!{}!, !{}!,!{}!,!{}!,!{}!)".format(hsg_field, rcn_field_a,rcn_field_b,rcn_field_c,rcn_field_d),
            expression_type="PYTHON3",
            code_block="""def calculate_value(hsg, rcna, rcnb, rcnc, rcnd):
                if hsg == "A":
                    return rcna
                elif hsg == "B":
                    return rcnb
                elif hsg == "C":
                    return rcnc
                else:
                    return rcnd""",
            field_type="DOUBLE",
            enforce_domains="NO_ENFORCE_DOMAINS"
        )

        # add runoff layer to map
        log("add runoff layer to map")
        lyr = active_map.addDataFromPath(output_fc)

        # symbology based off of RCN range
        log("setting runoff layer symbology")
        if lyr.isFeatureLayer:
            sym = lyr.symbology
            if hasattr(sym, 'renderer'):
              if sym.renderer.type == 'SimpleRenderer':
                sym.updateRenderer('GraduatedColorsRenderer')
                sym.renderer.breakCount = 5
                sym.renderer.classificationMethod = 'NaturalBreaks'
                sym.renderer.classificationField = 'RCN'
                sym.renderer.colorRamp = project.listColorRamps('Orange-Red (5 Classes)')[0]
                lyr.symbology = sym

        # cleanup
        log("deleting unneeded data")
        empty_workspace(arcpy.env.scratchGDB, keep=[])

        # save project
        log("saving project")
        project.save()

        return
