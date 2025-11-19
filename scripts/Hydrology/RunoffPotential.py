# --------------------------------------------------------------------------------
# Name:        Runoff Potential
# Purpose:     This tool calculates runoff curve numbers (RCNs) for a given study
#              area.
#
# Author:      Reya Mertz
#
# Created:     11/2025
# Modified:    11/2025
# License:     GNU Affero General Public License v3.
#              Full license in LICENSE file, or at <https://www.gnu.org/licenses/>
# --------------------------------------------------------------------------------

import arcpy
import pathlib
import openpyxl
import datetime
import math

from pprint import pprint

# setup helpers
import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), "../helpers"))
from print_messages import print_messages as log
from setup_environment import setup_environment as setup
from validate_spatial_reference import validate_spatial_reference as validate
from license import license as license

class RunoffPotential:
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
            displayName="Land Use Data",
            name="land_use",
            datatype="GPRasterLayer",
            parameterType="Required",
            direction="Input")

        params = [param0, param1, param2, param3]
        return params

    def isLicensed(self):
        """Set whether the tool is licensed to execute."""
        return license(['Spatial'])
    
    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool parameter."""
        validate(parameters)
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
        land_use_raster = parameters[3].value
       
        #colorramps = project.listColorRamps()
        #for i in colorramps:
        #    log(i.name)
        #return

        # scratch layers
        log("creating scratch layers")
        soils_scratch = arcpy.CreateScratchName("soils_scratch", data_type="FeatureClass", workspace=arcpy.env.scratchFolder)
        land_use_raster_clip = "{}\\land_use_raster_clip".format(arcpy.env.workspace)
        scratch_land_use_polygon = arcpy.CreateScratchName("scratch_land_use_polygon", data_type="FeatureClass", workspace=arcpy.env.scratchFolder)
        scratch_joined_land_use_polygon = arcpy.CreateScratchName("scratch_joined_land_use_polygon", data_type="FeatureClass", workspace=arcpy.env.scratchFolder)
        scratch_pairwise_intersection = arcpy.CreateScratchName("scratch_pairwise_intersection", data_type="FeatureClass", workspace=arcpy.env.scratchFolder)

        # clip soils
        log("clipping soils to watershed")
        arcpy.analysis.Clip(soils, watershed, soils_scratch)

        # clip land use raster
        log("clipping land use raster to watershed")
        out_land_use_raster_clip = arcpy.sa.ExtractByMask(land_use_raster, watershed, "INSIDE")
        out_land_use_raster_clip.save(land_use_raster_clip)
        
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
            out_feature_class=scratch_pairwise_intersection,
            join_attributes="ALL",
            cluster_tolerance=None,
            output_type="INPUT"
        )

        # calculate RCN from HSG
        log("calculate RCN from HSG")
        arcpy.management.CalculateField(
            in_table=scratch_pairwise_intersection,
            field="RCN",
            expression="calculate_value(!hydgrpdcd!, !RCNA!,!RCNB!,!RCNC!,!RCND!)",
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

        # dissolve RCN boundaries
        log("dissolve RCN boundaries")
        arcpy.analysis.PairwiseDissolve(
            in_features=scratch_pairwise_intersection,
            out_feature_class=output_fc,
            dissolve_field="RCN",
            statistics_fields=None,
            multi_part="MULTI_PART",
            concatenation_separator=""
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

        # delete not needed scratch layers
        log("delete unused layers")
        arcpy.management.Delete([soils_scratch, land_use_raster_clip, scratch_land_use_polygon, scratch_joined_land_use_polygon, scratch_pairwise_intersection])
        
        # save project
        log("saving project")
        project.save()    

        return
