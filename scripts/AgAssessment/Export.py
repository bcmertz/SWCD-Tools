# -*- coding: utf-8 -*-

import string
import arcpy
import datetime
import shutil
import pathlib
import openpyxl
import re
import csv

from arcpy import env

# import log tool
import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), "../helpers"))
from printmessages import printMessages as log
from sanitize import sanitize

class Export(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "4. Export Layouts"
        self.description = "Run to export layouts"
        self.category = "Automated Ag Assessment"
        self.canRunInBackground = False
   
    def getParameterInfo(self):
        """Define parameter definitions"""
        return

    def execute(self, parameters, messages):
        """The source code of the tool."""
        # Setup
        arcpy.env.overwriteOutput = True

        # Helpers
        project = arcpy.mp.ArcGISProject("Current")
        project_name = project.filePath.split("\\")[-1][:-5]

        # Path Root
        year = datetime.date.today().year
        path_root = "O:\Ag Assessments\{}\{}".format(year, project_name)
    
        # Export layouts
        layouts = project.listLayouts()
        for layout in layouts:
            if layout.name == "Layout":
                continue
            layout_file_path = "{}\{}.pdf".format(path_root, layout.name)
            layout.exportToPDF(layout_file_path)

        # Open project folder
        os.startfile(path_root)

        return
