import arcpy

def printMessages(*args):
    """provide a list of messages to this method"""
    out_str = ""
    args = args[1:] # get rid of first argument
    for arg in args:
        out_str += str(arg)+" "
    arcpy.AddMessage(out_str+"\n") # and newline and print
    return
