import arcpy

# only needed for spatial analyst, but potential image analyst, ddd or others if
# we end up using them
# https://pro.arcgis.com/en/pro-app/3.3/arcpy/functions/checkextension.htm

def license(licenses):
    """verify the required licenses are installed"""
    try:
        for l in licenses:
            status = arcpy.CheckExtension(l)
            if status != "Available":
                return False
        return True
    except:
        return False
