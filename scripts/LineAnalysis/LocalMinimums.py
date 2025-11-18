# -*- coding: utf-8 -*-

import arcpy

# setup helpers
import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), "../helpers"))
from print_messages import print_messages as log
from setup_environment import setup_environment as setup
from validate_spatial_reference import validate_spatial_reference as validate
from license import license as license

class LocalMinimums:
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Local Minimums"
        self.description = "Find local minimums along line for a given raster"
        self.category = "Linear Analysis"
        self.canRunInBackground = False

    def isLicensed(self):
        """Set whether the tool is licensed to execute."""
        return license([])
    
    def getParameterInfo(self):
        """Define the tool parameters."""
        param0 = arcpy.Parameter(
            displayName="Line",
            name="line",
            datatype="GPFeatureLayer",
            parameterType="Required",
            direction="Input")
        param0.filter.list = ["Polyline"]
        param0.controlCLSID = '{60061247-BCA8-473E-A7AF-A2026DDE1C2D}' # allows line creation

        param1 = arcpy.Parameter(
            displayName="DEM",
            name="dem",
            datatype="GPRasterLayer",
            parameterType="Required",
            direction="Input")

        param2 = arcpy.Parameter(
            displayName="Analysis Area",
            name="analysis_area",
            datatype="GPExtent",
            parameterType="Optional",
            direction="Input")        
        param2.controlCLSID = '{15F0D1C1-F783-49BC-8D16-619B8E92F668}'

        param3 = arcpy.Parameter(
            displayName="Search Interval (m)",
            name="search_distance",
            datatype="GPDouble",
            parameterType="Required",
            direction="Input")

        param4 = arcpy.Parameter(
            displayName="Minimum Elevation Difference Threshold (in)",
            name="threshold",
            datatype="GPDouble",
            parameterType="Required",
            direction="Input")

        #param5 = arcpy.Parameter(
        #    displayName="Include endpoints?",
        #    name="endpoints",
        #    datatype="GPBoolean",
        #    parameterType="Optional",
        #    direction="Input")

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
        return True

    def updateParameters(self, parameters):
        # default search interval
        if parameters[3].value == None:
            parameters[3].value = 1

        # default threshold value
        if parameters[4].value == None:
            parameters[4].value = 2
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
        spatial_reference_name = active_map.spatialReference.name
        spatial_reference = arcpy.SpatialReference(spatial_reference_name)

        log("reading in parameters")
        line = parameters[0].value
        dem_raster = parameters[1].value
        XMin = parameters[2].value.XMin if parameters[2].value else 0
        YMin = parameters[2].value.YMin if parameters[2].value else 0
        XMax = parameters[2].value.XMax if parameters[2].value else 0
        YMax = parameters[2].value.YMax if parameters[2].value else 0
        extent = arcpy.Extent(XMin, YMin, XMax, YMax)
        if parameters[2].value:
                extent.spatialReference = parameters[2].value.spatialReference
        search_interval = parameters[3].value
        threshold = parameters[4].value / (3.2808 * 12)
        # endpoints_bool = parameters[5].value
        output_file = parameters[5].valueAsText

        # create scratch layers
        log("creating scratch layers")
        scratch_dem = arcpy.CreateScratchName("temp",
                                               data_type="RasterDataset",
                                               workspace=arcpy.env.scratchFolder)
        scratch_line = arcpy.CreateScratchName("temp",
                                               data_type="DEFeatureClass",
                                               workspace=arcpy.env.scratchFolder)

        # clip to analysis area
        if parameters[2].value:
            # clip line to analysis area
            log("clipping line to analysis area")
            arcpy.analysis.Clip(line, extent.polygon, scratch_line)
        else:
            scratch_line = line

        # generate points along line
        log("generate points along line")
        arcpy.edit.Densify(scratch_line, "DISTANCE", search_interval)

        # iterate through lines and points
        log("finding local minimums")
        with arcpy.da.SearchCursor(scratch_line, ["SHAPE@"]) as cursor:
            # keep track of local minimums
            local_minimums = []

            for sub_line in cursor:
                # helper variables to find local minimums
                elev_prev = -9999
                lowpoint = None
                lowpoint_elev = -9999
                prev_local_maximum_elev = -9999

                # iterate through each vertex of the given stream polyline
                num_vertices = len(sub_line[0][0])
                for i in range(num_vertices):
                    # get current vertex and elevation
                    vertex = sub_line[0][0][i]
                    coord = "{} {}".format(vertex.X, vertex.Y)
                    elev_cur = arcpy.management.GetCellValue(dem_raster, coord)
                    elev_cur = float(elev_cur.getOutput(0))

                    # first point
                    if i == 0:
                        lowpoint = vertex
                        lowpoint_elev = elev_cur

                    if i == num_vertices - 1:
                        if elev_cur < lowpoint_elev:
                            lowpoint = vertex
                            lowpoint_elev = elev_cur
                        delta_1 = threshold if prev_local_maximum_elev == -9999 else prev_local_maximum_elev - lowpoint_elev
                        if delta_1 >= threshold:
                            local_minimums.append(arcpy.PointGeometry(lowpoint))                        
                            
                    # downhill
                    elif elev_prev > elev_cur:
                        delta_1 = threshold if prev_local_maximum_elev == -9999 else prev_local_maximum_elev - lowpoint_elev
                        delta_2 = elev_prev - lowpoint_elev

                        # both pass
                        if delta_1 >= threshold and delta_2 >= threshold:
                            local_minimums.append(arcpy.PointGeometry(lowpoint))
                            prev_local_maximum_elev = elev_prev
                            lowpoint = vertex
                            lowpoint_elev = elev_cur

                        # 1st threshold passes
                        elif delta_1 >= threshold and delta_2 < threshold:
                            if prev_local_maximum_elev == -9999:
                                if elev_cur < lowpoint_elev:
                                    lowpoint = vertex
                                    lowpoint_elev = elev_cur                                
                            elif elev_cur < lowpoint_elev:
                                lowpoint = vertex
                                lowpoint_elev = elev_cur
                            else:
                                pass

                        # 2nd passes
                        elif delta_1 < threshold and delta_2 >= threshold:
                            prev_local_maximum_elev = elev_prev
                            lowpoint = vertex
                            lowpoint_elev = elev_cur
                            
                        # neither passes 
                        else:
                            if elev_cur < lowpoint_elev:
                                lowpoint = vertex
                                lowpoint_elev = elev_cur

                    # uphill
                    else:
                        pass

                    
                    # setup for next iteration
                    elev_prev = elev_cur
                    
            # add points to map
            if len(local_minimums) > 0:
                log("copying points to feature class")
                arcpy.management.CopyFeatures(local_minimums, output_file)
                log("defining spatial reference of feature")
                arcpy.management.DefineProjection(output_file,spatial_reference)
                log("adding minimums to map")
                active_map.addDataFromPath(output_file)                
            else:
                log("no local minimums found")

        # cleanup
        log("deleting unneeded data")
        arcpy.management.Delete([scratch_dem])

        # save
        log("saving project")
        project.save()
            
        return
