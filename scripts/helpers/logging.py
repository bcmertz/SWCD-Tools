# ---------------------------------------------------------------------------------
# Name:        Logging Helper
# Purpose:     This package contains various tools for logging to the tool messages.
#
# License:     Contextual Copyleft AI (CCAI) License v1.0.
#              Full license in LICENSE file.
# ---------------------------------------------------------------------------------

import arcpy

def log(*args):
    """Print out messages."""
    out_str = ""
    for arg in args:
        out_str += str(arg)+" "
    arcpy.AddMessage(out_str+"\n") # and newline and print
    return

def warn(*args):
    """Print out warnings."""
    out_str = ""
    for arg in args:
        out_str += str(arg)+" "
    arcpy.AddWarning(out_str+"\n") # and newline and print
    return

def error(*args):
    """Print out errors."""
    out_str = ""
    for arg in args:
        out_str += str(arg)+" "
    arcpy.AddError(out_str+"\n") # and newline and print
    return
