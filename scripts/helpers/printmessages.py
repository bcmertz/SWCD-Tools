# --------------------------------------------------------------------------------
# Name:        Print Messages
# Purpose:     This helper is used in various other tools to combine and print
#              messages to the tool output.
#
# License:     GNU Affero General Public License v3.
#              Full license in LICENSE file, or at <https://www.gnu.org/licenses/>
# --------------------------------------------------------------------------------

import arcpy

def log(*args):
    """provide a list of messages to this method"""
    out_str = ""
    #args = args[1:] # get rid of first argument
    for arg in args:
        out_str += str(arg)+" "
    arcpy.AddMessage(out_str+"\n") # and newline and print
    return

def warn(*args):
    """provide a list of messages to this method"""
    out_str = ""
    #args = args[1:] # get rid of first argument
    for arg in args:
        out_str += str(arg)+" "
    arcpy.AddWarning(out_str+"\n") # and newline and print
    return

def error(*args):
    """provide a list of messages to this method"""
    out_str = ""
    #args = args[1:] # get rid of first argument
    for arg in args:
        out_str += str(arg)+" "
    arcpy.AddError(out_str+"\n") # and newline and print
    return
