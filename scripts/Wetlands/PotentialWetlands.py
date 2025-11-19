# --------------------------------------------------------------------------------
# Name:        Potential Wetlands
# Purpose:     This tool analyzes soils, hydrology, and land use to calculate
#              potential wetland areas.
#
# Author:      Reya Mertz
#
# Created:     11/2025
# Modified:    11/2025
# License:     GNU Affero General Public License v3.
#              Full license in LICENSE file, or at <https://www.gnu.org/licenses/>
# --------------------------------------------------------------------------------

import arcpy

from arcpy import env
from math import atan2, pi, exp

# setup helpers
import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), "../helpers"))
from print_messages import print_messages as log
from setup_environment import setup_environment as setup
from validate_spatial_reference import validate_spatial_reference as validate
from license import license as license

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
            parameterType="Required",
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
            displayName="Maximum Slope (percent)",
            name="max_slope",
            datatype="GPDouble",
            parameterType="Optional",
            direction="Output")

        param4 = arcpy.Parameter(
            displayName="Soils Shapefile",
            name="soils",
            datatype="GPFeatureLayer",
            parameterType="Required",
            direction="Input")
        param4.filter.list = ["Polygon"]
        
        param5 = arcpy.Parameter(
            displayName="HSG Field",
            name="hsg_field",
            datatype="GPString",
            parameterType="Required",
            direction="Input")
        param5.filter.type = "ValueList"
        param5.filter.list = []

        param6 = arcpy.Parameter(
            displayName="Valid HSGs",
            name="hsg_values",
            multiValue = True,
            datatype="GPString",
            parameterType="Required",
            direction="Input")
        param6.filter.type = "ValueList"
        param6.filter.list = []

        param7 = arcpy.Parameter(
            displayName="Land Use Data",
            name="land_use",
            datatype="GPRasterLayer",
            parameterType="Required",
            direction="Input")

        param8 = arcpy.Parameter(
            displayName="Land Use Field",
            name="land_use_field",
            datatype="GPString",
            parameterType="Required",
            direction="Input")
        param8.filter.type = "ValueList"
        param8.filter.list = []

        param9 = arcpy.Parameter(
            displayName="Land Uses to Include",
            name="land_use_field_values",
            datatype="GPString",
            multiValue=True,
            parameterType="Required",
            direction="Input")
        param9.filter.type = "ValueList"
        param9.filter.list = []

        param10 = arcpy.Parameter(
            displayName="Exclude Mapped Wetlands?",
            name="exclude_wetlands",
            datatype="GPBoolean",
            parameterType="Optional",
           direction="Input")

        param11 = arcpy.Parameter(
            displayName="Wetland Layers",
            name="wetland_layers",
            datatype="GPFeatureLayer",
            multiValue=True,
            parameterType="Optional",
           direction="Input")
        param11.filter.list = ["Polygon"]
        
        params = [param0, param1, param2, param3, param4, param5, param6, param7, param8, param9, param10, param11]
        return params

    def isLicensed(self):
        """Set whether the tool is licensed to execute."""
        return license(['Spatial'])
    
    def updateParameters(self, parameters):
        # get soils field
        if parameters[4].value:
            parameters[5].enabled = True
            fields = [f.name for f in arcpy.ListFields(parameters[4].value)]
            parameters[5].filter.list = fields
        if not parameters[4].value:
            parameters[5].enabled = False
            parameters[5].value = None
            
        # toggle which soil hsg values to use
        if parameters[5].value:
            parameters[6].enabled = True
            values = set()
            with arcpy.da.SearchCursor(parameters[4].value, parameters[5].value) as cursor:
                for row in cursor:
                    if row[0] != None:
                        values.add(row[0])
            values = sorted(list(values))
##            for f in arcpy.ListFields(parameters[4].value):
##                if f.aliasName == parameters[5].value:
##                    with arcpy.da.SearchCursor(parameters[4].value, f.name) as cursor:
##                        for row in cursor:
##                            if row[0] != None:
##                                values.add(row[0])
##                    values = sorted(list(values))
            parameters[6].filter.list = values
        if not parameters[5].value:
            parameters[6].enabled = False

        # get land use field
        if parameters[7].value:
            parameters[8].enabled = True
            fields2 = [f2.name for f2 in arcpy.ListFields(parameters[7].value)]
            parameters[8].filter.list = fields2
        if not parameters[7].value:
            parameters[8].enabled = False

        # toggle which land use values to use
        if parameters[8].value:
            parameters[9].enabled = True
            values2 = []
            with arcpy.da.SearchCursor(parameters[7].value, parameters[8].value) as cursor2:
                    values2 = sorted({row2[0] for row2 in cursor2})
            parameters[9].filter.list = values2
        if not parameters[7].value:
            parameters[9].enabled = False
            
        # default maximum slope value
        if parameters[3].value == None:
            parameters[3].value = 5

        # toggle asking for wetland layers
        if parameters[10].value == True:
            parameters[11].enabled = True
        else:
            parameters[11].enabled = False
            
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

        dem_raster = parameters[0].value
        extent = arcpy.Extent(XMin = parameters[1].value.XMin,
                              YMin = parameters[1].value.YMin,
                              XMax = parameters[1].value.XMax,
                              YMax = parameters[1].value.YMax)
        extent.spatialReference = parameters[1].value.spatialReference
        output_file = parameters[2].valueAsText
        max_slope = parameters[3].value if parameters[3].value else 8
        soils_shapefile = parameters[4].value
        soils_hsg_field = parameters[5].value
        hsg_values = parameters[6].valueAsText.split(";")
        land_use_raster = parameters[7].value
        land_use_field = parameters[8].value
        land_use_values = parameters[9].valueAsText.replace("'","").split(";")
        calculate_wetlands = parameters[10].value
        wetland_layers = parameters[11].valueAsText.replace("'","").split(";") if calculate_wetlands else []

        # setup DEM area
        log("clipping DEM")
        scratch_dem = arcpy.CreateScratchName("temp",
                                               data_type="RasterDataset",
                                               workspace=arcpy.env.scratchFolder)       
        rectangle = "{} {} {} {}".format(extent.XMin, extent.YMin, extent.XMax, extent.YMax)
        arcpy.management.Clip(dem_raster, rectangle, scratch_dem)

        #dem_raster_clip = "{}\\dem_raster_clip".format(arcpy.env.workspace)
        #out_raster_clip = arcpy.sa.ExtractByMask(dem_raster, scratch_stream_buffer, "INSIDE", "MINOF")
        #out_raster_clip.save(dem_raster_clip)
        
        # slope raster
        log("creating slope raster from DEM")
        scratch_slope = arcpy.CreateScratchName("temp",
                                               data_type="RasterDataset",
                                               workspace=arcpy.env.scratchFolder)
        out_slope = arcpy.sa.Slope(scratch_dem, "PERCENT_RISE", "", "GEODESIC", "METER")
        out_slope.save(scratch_slope)

        # slopes < 5 percent
        log("selecting slopes less than or equal to {}%".format(max_slope))
        scratch_low_slope = arcpy.CreateScratchName("temp",
                                               data_type="RasterDataset",
                                               workspace=arcpy.env.scratchFolder)
        slope_sql_query = "VALUE <= {}".format(max_slope)
        outCon = arcpy.sa.Con(scratch_slope, scratch_slope, "", slope_sql_query)
        outCon.save(scratch_low_slope)
            
        # convert con output to int
        log("converting slope raster to int")
        scratch_int_slope = arcpy.CreateScratchName("temp",
                                               data_type="RasterDataset",
                                               workspace=arcpy.env.scratchFolder)        
        scratch_int_slope = arcpy.sa.Int(scratch_low_slope)

        # slope raster to polygon
        log("converting slope raster to polygon")
        scratch_slope_polygon = arcpy.CreateScratchName("temp",
                                               data_type="FeatureClass",
                                               workspace=arcpy.env.scratchFolder)
        arcpy.conversion.RasterToPolygon(scratch_int_slope, scratch_slope_polygon, "NO_SIMPLIFY")

        # dissolve raster polygon features
        log("dissolving slope polygon boundaries")
        scratch_slope_dissolve_polygon = arcpy.CreateScratchName("temp",
                                               data_type="FeatureClass",
                                               workspace=arcpy.env.scratchFolder)        
        arcpy.management.Dissolve(scratch_slope_polygon, scratch_slope_dissolve_polygon)
        

        # clip soils layer to low slope area
        log("clipping soils to low slope areas")
        scratch_soils_area = arcpy.CreateScratchName("temp",
                                               data_type="FeatureClass",
                                               workspace=arcpy.env.scratchFolder)
        arcpy.analysis.Clip(soils_shapefile, scratch_slope_dissolve_polygon, scratch_soils_area)

        # select HSG: A/D, B/D, C/D, C, or D from soils
        log("selecting hydric soils")
        scratch_hsg_soils = arcpy.CreateScratchName("temp",
                                               data_type="FeatureClass",
                                               workspace=arcpy.env.scratchFolder)
        hsg_sql_query = ""
        for hsg in hsg_values:
            hsg = hsg.replace("'", "")
            if hsg_sql_query == "":
                hsg_sql_query = "{} = '{}'".format(soils_hsg_field, hsg)
            else:
                hsg_sql_query += " Or {} = '{}'".format(soils_hsg_field, hsg)
        arcpy.analysis.Select(scratch_soils_area, scratch_hsg_soils, hsg_sql_query)

        # clip land use raster
        log("clipping land use raster to valid soils area and slopes less than or equal to {}%".format(max_slope))
        land_use_raster_clip = "{}\\land_use_raster_clip".format(arcpy.env.workspace)
        out_land_use_raster_clip = arcpy.sa.ExtractByMask(land_use_raster, scratch_hsg_soils, "INSIDE", "MINOF")
        out_land_use_raster_clip.save(land_use_raster_clip)

        # select viable land uses from land use raster
        log("extracting desired land uses")
        scratch_land_use = "{}\\scratch_land_use".format(arcpy.env.workspace)
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
            outLandUse = arcpy.sa.ExtractByAttributes(land_use_raster_clip, land_use_sql_query)
            outLandUse.save(scratch_land_use)
        else:
            log("no valid land uses found in area, please try again with land uses found in analysis area")
            return
     
        # convert land usage output to polygon
        log("converting land use areas to polygon")
        scratch_land_use_polygon = arcpy.CreateScratchName("temp",
                                               data_type="FeatureClass",
                                               workspace=arcpy.env.scratchFolder)
        arcpy.conversion.RasterToPolygon(scratch_land_use, scratch_land_use_polygon, "NO_SIMPLIFY", "VALUE")

        # copy potential wetlands to new layer
        log("copying potential wetlands to new layer")
        potential_wetland_locations = arcpy.CreateUniqueName("potential_wetland_locations", arcpy.env.workspace)
        arcpy.management.CopyFeatures(scratch_land_use_polygon, potential_wetland_locations)

        # setup temporary potential wetland layer helper
        scratch_reduced_potential_wetland = arcpy.CreateScratchName("temp",
                                               data_type="FeatureClass",
                                               workspace=arcpy.env.scratchFolder) 

        # erase NWI / DEC wetlands if selected
        if calculate_wetlands:
            log("erasing mapped wetlands from output") 
            for wetland_layer in wetland_layers:
                # erase wetlands
                try:
                    arcpy.analysis.Erase(potential_wetland_locations, wetland_layer, scratch_reduced_potential_wetland)
                except arcpy.ExecuteError:
                    log("failed to erase existing wetlands, please see error below:")
                    log(arcpy.GetMessages())
                    sys.exit()
                # copy reduced wetland area to potential wetland locations
                arcpy.management.CopyFeatures(scratch_reduced_potential_wetland, potential_wetland_locations)

        # delete not needed scratch layers
        log("delete unused layers")
        arcpy.management.Delete(land_use_raster_clip)
        arcpy.management.Delete(scratch_land_use)
        arcpy.management.Delete([scratch_dem, scratch_slope,scratch_low_slope,scratch_int_slope,scratch_slope_polygon,scratch_slope_dissolve_polygon,scratch_hsg_soils,scratch_soils_area,scratch_land_use_polygon,scratch_reduced_potential_wetland])

        # finish up
        log("finishing up")
        active_map.addDataFromPath(potential_wetland_locations)

        # save project
        log("saving project")
        project.save()

        return



