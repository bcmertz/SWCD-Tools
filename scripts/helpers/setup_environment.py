import arcpy

def setup_environment():
    """Setup environment for analysis"""
    # setup project and active map
    project = arcpy.mp.ArcGISProject("Current")
    active_map = project.activeMap

    # setup arcpy environmental variables
    # TODO: consider setting output coordinate system to map coordinate system
    arcpy.env.overwriteOutput = True
    if arcpy.env.outputCoordinateSystem == None:
        arcpy.env.outputCoordinateSystem = arcpy.SpatialReference("WGS 1984 UTM Zone 18N")

    return project, active_map
