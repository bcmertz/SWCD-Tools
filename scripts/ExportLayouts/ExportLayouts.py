# -*- coding: utf-8 -*-

import arcpy

# import log tool
import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), "../helpers"))
from printmessages import printMessages as log

class ExportLayouts(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Export Layouts"
        self.description = "Run to export layouts"
        self.category = "Export Layouts"
        self.canRunInBackground = False
   
    def getParameterInfo(self):
        """Define parameter definitions"""
        project = arcpy.mp.ArcGISProject("Current")
        layout_list = [l.name for l in project.listLayouts()]
        
        param0 = arcpy.Parameter(
            displayName="Layouts to Export",
            name="layouts",
            datatype="GPString",
            parameterType="Required",
            direction="Input",
            multiValue=True)

        param0.filter.list = layout_list
    
        param1 = arcpy.Parameter(
            displayName="Output Folder",
            name="output_folder",
            datatype="DEType",
            parameterType="Required",
            direction="Input")
            
        params = [param0, param1]
        return params

    def printMessages(*args):
        """provide a list of messages to this method"""
        out_str = ""
        #args = args[1:] # get rid of first argument
        for arg in args:
            out_str += str(arg)+" "
        arcpy.AddMessage(out_str+"\n") # and newline and print
        return

    def execute(self, parameters, messages):
        """The source code of the tool."""
        # Setup
        arcpy.env.overwriteOutput = True
        project = arcpy.mp.ArcGISProject("Current")
        log("here23")
        file_path = parameters[1].valueAsText
        layouts = parameters[0].valueAsText.replace("'", "").split(";")
        project_layouts = project.listLayouts()

        # Export layouts
        for layout in project_layouts:
            if layout.name in layouts:
                layout_file_path = "{}\{}.pdf".format(file_path, layout.name)
                layout.exportToPDF(layout_file_path)

        # Open project folder
        os.startfile(file_path)

        return

    
