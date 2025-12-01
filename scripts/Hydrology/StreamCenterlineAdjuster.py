# --------------------------------------------------------------------------------
# Name:        Stream Centerline Adjuster
# Purpose:     This tool corrects a streamline to a DEM by minimizing elevation.
#
# License:     GNU Affero General Public License v3.
#              Full license in LICENSE file, or at <https://www.gnu.org/licenses/>
# --------------------------------------------------------------------------------

import math
import arcpy

from helpers import *
from print_messages import print_messages as log
from setup_environment import setup_environment as setup
from validate_spatial_reference import validate_spatial_reference as validate
from license import license as license

class LeastAction(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Stream Centerline Adjuster"
        self.description = "Stream Centerline Adjuster"
        self.category = "Hydrology"
        self.canRunInBackground = False
   
    def getParameterInfo(self):
        """Define parameter definitions"""
        param0 = arcpy.Parameter(
            displayName="DEM",
            name="dem",
            datatype="GPRasterLayer",
            parameterType="Required",
            direction="Input")

        # TODO: remove, not needed?
        param1 = arcpy.Parameter(
            displayName="Analysis Area",
            name="analysis_area",
            datatype="GPExtent",
            parameterType="Required",
            direction="Input")        
        param1.controlCLSID = '{15F0D1C1-F783-49BC-8D16-619B8E92F668}'
       
        param2 = arcpy.Parameter(
            displayName="Stream Feature Class",
            name="streams",
            datatype="GPFeatureLayer",
            parameterType="Required",
            direction="Input")
        param2.filter.list = ["Polyline"]

        param3 = arcpy.Parameter(
            displayName="Output Features",
            name="out_features",
            datatype="DEFeatureClass",
            parameterType="Required",
            direction="Output")
        param3.parameterDependencies = [param0.name]
        param3.schema.clone = True
        
        param4 = arcpy.Parameter(
            displayName="Search Distance (m)",
            name="search_distance",
            datatype="GPDouble",
            parameterType="Required",
            direction="Input")
        
        params = [param0, param1, param2, param3, param4]
        return params

    def transectLine(self, stream_line, stream_vertex, transect_length):
        '''returns a transect to stream_line of length transect_length at stream_vertex point
        stream_line - arcpy.PolyLine() object
        stream_vertex - arcpy.Point() object
        transect_length - distance in meters of transect
        '''        
        # epsilon
        e = 1e-5
        
        # get stream vertex
        stream_vertex = stream_line.queryPointAndDistance(stream_vertex, False)
        geom = stream_vertex[0]
        distance = stream_vertex[1]
        spatial_reference = stream_line.spatialReference

        # get points immediately before and after midpoint
        before = stream_line.positionAlongLine(distance-e, False)
        after = stream_line.positionAlongLine(distance+e, False)

        dX = after[0].X - before[0].X
        dY = after[0].Y - before[0].Y

        # angle of the midpoint segment
        angle = math.atan2(dX,dY) * 180 / math.pi

        first_tran_point = geom.pointFromAngleAndDistance(angle - 90, transect_length/2)
        last_tran_point = geom.pointFromAngleAndDistance(angle + 90, transect_length/2)
        dX = first_tran_point.firstPoint.X - last_tran_point.firstPoint.X
        dY = first_tran_point.firstPoint.Y - last_tran_point.firstPoint.Y

        transect = arcpy.Polyline(arcpy.Array((first_tran_point.firstPoint, last_tran_point.firstPoint)), spatial_reference)
        return transect
    
    def lowestTransectPoint(self, transect, dem_raster):
        '''return lowest point along transect
        transect - arcpy.PolyLine() object
        dem_raster - elevation raster
        existing_elev - existing elevation of stream line at point
        '''
        # get points via densify
        vertex_spacing = 1
        densified_transect = transect.densify("DISTANCE", vertex_spacing)

        # get existing stream elevation
        num_vertices = len(densified_transect[0])
        mid_index = int((num_vertices - 1)/2) # always round number because user supplies search distance: transect width = 2x search distance
        mid_vertex = densified_transect[0][mid_index]
        stream_coord = "{} {}".format(mid_vertex.X, mid_vertex.Y)
        stream_elev_result = arcpy.management.GetCellValue(dem_raster, stream_coord)
        stream_elev = float(stream_elev_result.getOutput(0))

        # average max distance of adjustment = transect_width / 2
        transect_width = vertex_spacing * (num_vertices - 1)
        ave_dist = transect_width / 2

        # set up helpers
        current_adjustment_weight = 0
        vertex_distance = 0
        point_tmp = ""
    
        for vertex in densified_transect[0]:       
            coord = "{} {}".format(vertex.X, vertex.Y)
            elev_result = arcpy.management.GetCellValue(dem_raster, coord)
            elev = float(elev_result.getOutput(0))
            delta_elev = stream_elev - elev # positive number is a good adjustment
            distance = abs(vertex_distance - ave_dist)
            # weighted adjustment weights the reduction in elevation with a weight from 0 - 1
            # based off of a normal distribution for the supplied serach distance
            weighted_adjustment = delta_elev * math.exp(-math.pow(distance,2)/(math.pow(ave_dist,2)))
            if weighted_adjustment >= current_adjustment_weight and delta_elev > 0.2:
                point_tmp = arcpy.Point(vertex.X, vertex.Y)
                current_adjustment_weight = weighted_adjustment
            vertex_distance += vertex_spacing
            
        if point_tmp == "":
            point_tmp = arcpy.Point(mid_vertex.X, mid_vertex.Y)
            
        return point_tmp

    def updateParameters(self, parameters):
        return
    
    def isLicensed(self):
        """Set whether the tool is licensed to execute."""
        return license([])

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool parameter."""
        validate(parameters)
        return
    
    def execute(self, parameters, messages):
        """The source code of the tool."""
        # Setup
        log("setting up project")
        project, active_map = setup()
        arcpy.env.parallelProcessingFactor = "75%"
               
        # read in parameters
        dem_raster = parameters[0].value       
        extent = parameters[1].value
        stream_layer = parameters[2].value
        output_file = parameters[3].valueAsText
        transect_length = 2*parameters[4].value

        # spatial reference
        dem_desc = arcpy.Describe(dem_raster)
        spatial_reference = dem_desc.spatialReference.name
        arcpy.env.outputCoordinateSystem = arcpy.SpatialReference(spatial_reference)

        # create area to process from extent
        log("creating area from extent")
        XMin = extent.XMin
        YMin = extent.YMin
        XMax = extent.XMax
        YMax = extent.YMax        
        pnt1 = arcpy.Point(XMin, YMin)
        pnt2 = arcpy.Point(XMin, YMax)
        pnt3 = arcpy.Point(XMax, YMax)
        pnt4 = arcpy.Point(XMax, YMin)
        array = arcpy.Array()
        array.add(pnt1)
        array.add(pnt2)
        array.add(pnt3)
        array.add(pnt4)
        array.add(pnt1)
        polygon = arcpy.Polygon(array)

        # clip streams to analysis area
        log("clipping stream centerline to analysis area")
        env_path = r"{}".format(arcpy.env.workspace)
        new_stream_line_path = output_file
        new_stream_line_name = new_stream_line_path.split("\\")[-1]
        new_stream_line = arcpy.management.CreateFeatureclass(env_path, new_stream_line_name, "POLYLINE", spatial_reference=spatial_reference)
        arcpy.analysis.Clip(stream_layer, polygon, new_stream_line)

        ## Debugging
        ## create temporary classes for debugging
        #lowpoints_fc = arcpy.management.CreateFeatureclass(env_path, "lowpoints", "POINT", spatial_reference=spatial_reference)
        #transects_fc = arcpy.management.CreateFeatureclass(env_path, "transects", "POLYLINE", spatial_reference=spatial_reference, has_m="ENABLED", has_z="ENABLED")
        #transects = []
        #lowpoints = []
        
        # iterate through each stream line polyline
        log("optimizing stream line")
        i = 1
        n = len([row[0] for row in arcpy.da.SearchCursor(new_stream_line, ["SHAPE@"])])
        with arcpy.da.UpdateCursor(new_stream_line, ["SHAPE@"]) as cursor:
            for stream_line in cursor:
                # set progress per reach
                record_count = len(stream_line[0][0]) # number of vertices in a given reach, not the best way but it works on a per-reach basis
                arcpy.SetProgressor("step", "iterating through vertices in stream reach to find lowest points", 0, record_count, 1)
                
                # construct line for stream reach
                new_stream_line_arr = arcpy.Array()

                # iterate through each vertex of the given stream polyline
                for vertex in stream_line[0][0]:
                    #create transect at point
                    transect = self.transectLine(stream_line[0], vertex, transect_length)
                    #transects.append(transect)

                    # find lowest point in transect
                    new_point = self.lowestTransectPoint(transect, dem_raster)
                    new_stream_line_arr.add(new_point)
                    #lowpoints.append(new_point)

                    # update progress bar
                    arcpy.SetProgressorPosition()

                # add optimized reach to output
                log("adding optimized reach {} of {} to output".format(i, n))
                new_stream_line = arcpy.Polyline(new_stream_line_arr)
                cursor.updateRow([new_stream_line])

                # get progress bar ready for next reach
                arcpy.SetProgressorPosition(record_count)
                i+=1
        arcpy.ResetProgressor()

        ## Debugging
        ## output transects
        #log("adding transects")
        #with arcpy.da.InsertCursor(transects_fc, ["SHAPE@"]) as transect_cursor:
        #    for transect in transects:
        #        transect_cursor.insertRow([transect])

        ## Debugging            
        ## output low points
        #log("adding lowpoints")
        #with arcpy.da.InsertCursor(lowpoints_fc, ["SHAPE@"]) as lowpoints_cursor:
        #    for lowpoint in lowpoints:
        #        lowpoints_cursor.insertRow([lowpoint])


        # repair self intersections
        log("repairing self intersections")
        arcpy.topographic.RepairSelfIntersection(new_stream_line, "DELETE")              

        # add data
        log("adding data")
        active_map.addDataFromPath(new_stream_line_path)

        # save project
        log("saving project")
        project.save()

        return
