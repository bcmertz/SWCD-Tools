import arcpy

def validate_spatial_reference(parameters):
    """Validate Spatial Reference
    This is used to make sure any parameters passed in
    which need a spatial reference have a spatial refernence.
    """
    
    warning_message = "Input has an unknown coordinate system. This may cause errors in running this tool. Please define a coordinate system for the input using 'define projection'"
    
    for param in parameters:
        if param.value and param.direction == "Input":
            try:
                desc = arcpy.Describe(param)
                if hasattr(desc, "spatialReference"):
                    spatial_ref = desc.spatialReference
                    param.setWarningMessage(warning_message)

                    # If the spatial reference is unknown
                    if spatial_ref.name == "Unknown":
                        param.setWarningMessage(warning_message)
                    else:
                        if param.hasWarning:
                            param.clearMessage()
            except:
                pass
            
    return
