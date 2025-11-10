import arcpy

from arcpy import env
from math import atan2, pi, exp

# import log tool
import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), "../helpers"))
from printmessages import printMessages as log

# TODO: calculate storage tool to be used with dam removal or dam creation, basically just diffs the existing and removed dems
# TODO: burn in channel width at channel depth via buffer of channel width into dem

class BermAnalysis(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Berm Analysis"
        self.description = "Model backwatered area from berm"
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
            displayName="Z-Unit",
            name="z_unit",
            datatype="GPString",
            parameterType="Optional",
            direction="Input")
        param2.filter.list = ["METER", "FOOT"]

        param3 = arcpy.Parameter(
            displayName="Output Features",
            name="out_features",
            datatype="DEFeatureClass",
            direction="Output")
        param3.parameterDependencies = [param0.name]
        param3.schema.clone = True

        param4 = arcpy.Parameter(
            displayName="Line",
            name="line",
            datatype="GPFeatureLayer",
            parameterType="Required",
            direction="Input")
        param4.filter.list = ["Polyline"]
        param4.controlCLSID = '{60061247-BCA8-473E-A7AF-A2026DDE1C2D}' # allows line creation
        
        param5 = arcpy.Parameter(
            displayName="Specify berm height?",
            name="supply_berm_height",
            datatype="GPBoolean",
            parameterType="Optional",
            direction="Input")
               
        param6 = arcpy.Parameter(
            displayName="Max Berm Height (ft)",
            name="berm_height",
            datatype="GPDouble",
            parameterType="Optional",
            direction="Input")
        
        param7 = arcpy.Parameter(
            displayName="Add depth contours?",
            name="contours",
            datatype="GPBoolean",
            parameterType="Optional",
            direction="Input")
        
        param8 = arcpy.Parameter(
            displayName="Contour interval (ft)",
            name="contour_interval",
            datatype="GPDouble",
            parameterType="Optional",
            direction="Input")
        
        param9 = arcpy.Parameter(
            displayName="Output Contour Feature",
            name="contour_output",
            parameterType="Required",            
            datatype="DEFeatureClass",
            direction="Output")
        param9.parameterDependencies = [param0.name]
        param9.schema.clone = True
        
        params = [param0, param1, param2, param3, param4, param5, param6, param7, param8, param9]
        return params

    def updateParameters(self, parameters):
        # update parameters before execution if needed
        # toggle asking for berm height
        if parameters[0].value != None:
            desc = arcpy.Describe(parameters[0].value)
            parameters[2].value = desc.spatialReference.linearUnitName
        
        if parameters[5].value == True:
            parameters[6].enabled = True
        else:
            parameters[6].enabled = False

        # default berm height
        if parameters[6].value == None:
            parameters[6].value = 5
        
        # default contour interval
        if parameters[8].value == None:
            parameters[8].value = 1
            
        # toggle asking for default contour interval and output
        if parameters[7].value == True:
            parameters[8].enabled = True
            parameters[9].enabled = True
            if parameters[3].value:            
                parameters[9].value = str(parameters[3].value) + "_contours_" + str(int(parameters[8].value)) + "ft"
        else:
            parameters[8].enabled = False
            parameters[9].enabled = False
    
            
        return
    
    def execute(self, parameters, messages):
        """The source code of the tool."""
        # Setup
        arcpy.env.overwriteOutput = True

        log("reading in parameters")
        dem_raster = parameters[0].value       
        extent = arcpy.Extent(XMin = parameters[1].value.XMin,
                              YMin = parameters[1].value.YMin,
                              XMax = parameters[1].value.XMax,
                              YMax = parameters[1].value.YMax)
        extent.spatialReference = parameters[1].value.spatialReference
        vertical_unit = parameters[2].value
        z_unit = 3.2808 if "meter" in vertical_unit.lower() else 1
        output_file = parameters[3].valueAsText
        berms = parameters[4].value
        supply_berm_height_bool = parameters[5].value
        berm_height = parameters[6].value / z_unit
        contour_bool = parameters[7].value
        contour_interval = parameters[8].value
        contour_output = parameters[9].valueAsText

        # project setup
        project = arcpy.mp.ArcGISProject("Current")
        active_map = project.activeMap

        # setup scratch variables
        log("creating scratch variables")
        scratch_dem = arcpy.CreateUniqueName("scratch_dem")
        scratch_dem_min = arcpy.CreateUniqueName("scratch_dem_min")
        scratch_zonal_statistics = arcpy.CreateUniqueName("scratch_zonal_statistics")
        scratch_dem_mask = arcpy.CreateUniqueName("scratch_dem_mask")
        scratch_mosaic_raster = arcpy.CreateUniqueName("scratch_mosaic_raster")
        scratch_fill_mosaic = arcpy.CreateUniqueName("scratch_fill_mosaic")
        scratch_fill_dem = arcpy.CreateUniqueName("scratch_fill_dem")
        scratch_raster_calculator = arcpy.CreateUniqueName("scratch_raster_calculator")
        scratch_con = arcpy.CreateUniqueName("scratch_con")
        scratch_contour = arcpy.CreateUniqueName("scratch_contour")
        scratch_effective_berm = arcpy.CreateUniqueName("scratch_effective_berm")
        scratch_output = arcpy.CreateUniqueName("scratch_output")
        scratch_berm = arcpy.CreateUniqueName("scratch_berm")

        # get spatial reference
        log("finding spatial reference")
        spatial_reference_name = active_map.spatialReference.name
        spatial_reference = arcpy.SpatialReference(spatial_reference_name)

        log("creating output feature classes")
        # create flooded area output
        if not arcpy.Exists(output_file):
            out_name = output_file.split("\\")[-1]
            arcpy.management.CreateFeatureclass(
                out_path=arcpy.env.workspace,
                out_name=out_name,
                geometry_type="POLYGON",
                spatial_reference=spatial_reference
            )

        # create contour output
        if contour_bool and not arcpy.Exists(contour_output):
            out_name = contour_output.split("\\")[-1]
            arcpy.management.CreateFeatureclass(
                out_path=arcpy.env.workspace,
                out_name=out_name,
                geometry_type="POLYLINE",
                spatial_reference=spatial_reference
            )
            # add contour field
            arcpy.management.AddField(contour_output, "Contour", "DOUBLE")         
        
        # setup DEM area
        log("clipping DEM")      
        rectangle = "{} {} {} {}".format(extent.XMin, extent.YMin, extent.XMax, extent.YMax)
        arcpy.management.Clip(dem_raster, rectangle, scratch_dem)

        # add berm height field to berm fc
        if "berm_height" not in [f.name for f in arcpy.ListFields(berms)]:
            arcpy.management.AddField(berms, "berm_height", "FLOAT", field_precision=255, field_scale=2)         

        # get OID field name for berm fc
        oidfield = arcpy.Describe(berms).OIDFieldName

        # get selected features in layer
        selection_set = berms.getSelectionSet()
        expression = "*"
        if selection_set:
            selection_tuple = tuple(selection_set)
            selection = "("+",".join([str(i) for i in selection_tuple])+")"
            expression = "{0} IN{1}".format(arcpy.AddFieldDelimiters(berms,oidfield),selection)

        # iterate through berms
        with arcpy.da.UpdateCursor(berms, [oidfield, "berm_height"], expression) as cursor:
            for berm in cursor:               
                # make a temporary feature layer to store the berm for zonal analysis
                log("creating temporary berm feature for analysis")
                oid_value = berm[0]
                where_clause = "\"OBJECTID\" = " + str(oid_value)
                arcpy.analysis.Select(berms, scratch_berm, where_clause)
                
                # ensure berm is in rectangle, if not skip
                desc = arcpy.Describe(scratch_berm)
                if not extent.contains(desc.extent):
                    log("drawn berm not in analysis area, skipping")
                    continue
                
                # if berm height is supplied, add it to the lowest elevation to get the flat berm elevation
                if supply_berm_height_bool:
                    # find minimum berm elevation
                    log("setting berm elevation")
                    out_raster = arcpy.sa.ZonalStatistics(
                        in_zone_data=scratch_berm,
                        zone_field=oidfield,
                        in_value_raster=scratch_dem,
                        statistics_type="MINIMUM",
                    )
                    out_raster.save(scratch_dem_mask)
                    berm_elevation = out_raster.minimum + berm_height

                    # clip original dem to berm area
                    log("clipping dem to berm")
                    out_raster = arcpy.sa.ExtractByMask(
                        in_raster=scratch_dem,
                        in_mask_data=scratch_berm,
                        extraction_area="INSIDE",
                    )
                    out_raster.save(scratch_dem_mask)

                    # adjust elevations under berm to berm elevation, leave alone higher ones
                    # if DEM > berm elev, keep, else use berm elev
                    log("adjusting dem to berm elevations")
                    output_raster = arcpy.sa.Con(
                        in_conditional_raster=scratch_dem_mask,
                        in_true_raster_or_constant=scratch_dem_mask,
                        in_false_raster_or_constant=berm_elevation,
                        where_clause="VALUE > {}".format(berm_elevation)
                    )
                    output_raster.save(scratch_zonal_statistics)
                else:
                    # zonal statistics
                    log("creating max berm height raster")

                    out_raster = arcpy.sa.ZonalStatistics(
                        in_zone_data=scratch_berm,
                        zone_field=oidfield,
                        in_value_raster=scratch_dem,
                        statistics_type="MAXIMUM",
                    )
                    out_raster.save(scratch_zonal_statistics)
            
                # mosaic to new raster
                log("mosaic to new raster")
                arcpy.management.MosaicToNewRaster(
                    input_rasters=[scratch_dem, scratch_zonal_statistics],
                    output_location=arcpy.env.workspace,
                    raster_dataset_name_with_extension=scratch_mosaic_raster.split("\\")[-1],
                    pixel_type="32_BIT_FLOAT",
                    number_of_bands=1,
                    mosaic_method="LAST",
                    mosaic_colormap_mode="FIRST"
                )

                # fill mosaic and clipped dem
                log("fill mosaic")
                out_mosaic_fill_raster = arcpy.sa.Fill(
                    in_surface_raster=scratch_mosaic_raster,
                    z_limit=None
                )
                out_mosaic_fill_raster.save(scratch_fill_mosaic)

                log("fill DEM")
                out_dem_fill_raster = arcpy.sa.Fill(
                    in_surface_raster=scratch_dem,
                    z_limit=None
                )
                out_dem_fill_raster.save(scratch_fill_dem)

                # raster calculator
                log("calculate elevation differences")
                output_raster_calculator = arcpy.sa.RasterCalculator(
                    rasters = [scratch_fill_mosaic, scratch_fill_dem],
                    input_names = ["mosaic", "dem"],
                    expression="mosaic - dem"
                )
                output_raster_calculator.save(scratch_raster_calculator)

                if contour_bool:
                    log("calculating contours")
                    arcpy.sa.Contour(
                        in_raster=scratch_raster_calculator,
                        out_polyline_features=scratch_contour,
                        contour_interval=1,
                        base_contour=0,
                        z_factor=z_unit,
                    )

                    # append contour outputs contour_output
                    log("appending contour output to feature class")
                    arcpy.management.Append(scratch_contour, contour_output, "NO_TEST")

                # con
                log("find all positive values")
                out_con = arcpy.sa.Con(
                    in_conditional_raster=scratch_raster_calculator,
                    in_true_raster_or_constant=1,
                    in_false_raster_or_constant=None,
                    where_clause="VALUE <> 0"
                )
                out_con.save(scratch_con)        

                # raster to polygon
                log("raster to polygon")
                arcpy.conversion.RasterToPolygon(
                    in_raster=scratch_con,
                    out_polygon_features=scratch_output,
                    simplify="SIMPLIFY",
                    raster_field="Value",
                    create_multipart_features="SINGLE_OUTER_PART",
                    max_vertices_per_feature=None
                )

                # append output polygon to output_file
                log("appending output to output feature class")
                arcpy.management.Append(scratch_output, output_file, "NO_TEST")

                # get berm height if not supplied
                if not supply_berm_height_bool:
                    log("calculating berm height")
                    arcpy.analysis.Clip(
                        in_features=scratch_berm,
                        clip_features=scratch_output,
                        out_feature_class=scratch_effective_berm,
                        cluster_tolerance=None
                    )
                    berm_raster = arcpy.sa.ZonalStatistics(
                        in_zone_data=scratch_effective_berm,
                        zone_field="OBJECTID",
                        in_value_raster=scratch_dem,
                        statistics_type="RANGE",
                    )
                    berm_height = berm_raster.maximum * z_unit
                    log("berm height: ", berm_height, "ft")           

                # add height to berm
                log("adding berm height to berm feature attribute table")
                berm[1] = berm_height
                cursor.updateRow(berm)
        
        # delete not needed scratch layers
        log("delete unused layers")
        arcpy.management.Delete([scratch_contour, scratch_berm, scratch_output, scratch_dem, scratch_dem_min, scratch_zonal_statistics, scratch_dem_mask, scratch_mosaic_raster, scratch_fill_mosaic, scratch_fill_dem, scratch_raster_calculator, scratch_con, scratch_effective_berm])
        
        
        # finish up
        log("finishing up")
        active_map.addDataFromPath(output_file)
        if contour_bool:
            active_map.addDataFromPath(contour_output)

        # save project
        log("saving project")
        project.save()

        return


