# --------------------------------------------------------------------------------
# Name:        Validate Spatial Reference
# Purpose:     This helper is used in various other tools to verify that each input
#              that can have a spatial reference has a valid spatial reference
#              defined in order to avoid errors.
#
# Notes:       This tool expects to run in updatemessages to avoid being overwritten
#              by internal validation. This still allows use of param.hasBeenValidated
#              to check for parameter changes. However, for some reason arcgis pro seems
#              to overwrite warning messages that are only set once.
#              Refer to https://pro.arcgis.com/en/pro-app/3.3/arcpy/geoprocessing_and_python/updating-schema-in-a-python-toolbox.htm
#              for documentation of python toolbox lifecycles and validation.
#
# License:     GNU Affero General Public License v3.
#              Full license in LICENSE file, or at <https://www.gnu.org/licenses/>
# --------------------------------------------------------------------------------

import arcpy

warning_message_unknown = "Input has an unknown coordinate system. This may cause errors in running this tool. Please define a coordinate system for the input using 'define projection'"
warning_message_geographic = "Input lacks a spatial reference projection. This may cause errors in running this tool. Please define a projected coordinate system for the input using 'define projection'"

def validate_spatial_reference(parameters):
    """Validate Spatial Reference
    This is used to make sure any parameters passed in which need
    a spatial reference have a valid spatial refernence.
    """
    warning_message = ""

    for param in parameters:
        valid_sr = True

        # ignore unset parameters, output parameters, and parameters which haven't been changed since the last time validation ran
        if param.altered and param.direction == "Input":
            try:
                desc = arcpy.Describe(param)
                if hasattr(desc, "spatialReference"):
                    spatial_ref = desc.spatialReference
                    # If the spatial reference is unknown
                    if spatial_ref.name == "Unknown":
                        valid_sr = False
                        warning_message = warning_message_unknown
                    elif spatial_ref.type == "Geographic":
                        valid_sr = False
                        warning_message = warning_message_geographic
            except:
                continue
        else:
            continue

        # set or clear warning messages
        if valid_sr:
            if param.message and param.message == warning_message:
                param.clearMessage()
        else:
            param.setWarningMessage(warning_message)

    return
