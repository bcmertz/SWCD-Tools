import arcpy

def setup_environment(*args):
    """provide a list of messages to this method"""
    arcpy.env.overwriteOutput = True
    if arcpy.env.outputCoordinateSystem == None:
        arcpy.env.outputCoordinateSystem = arcpy.SpatialReference("WGS 1984 UTM Zone 18N")
