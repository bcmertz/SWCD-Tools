# -*- coding: utf-8 -*-

import arcpy

# setup helpers
import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), "../helpers"))
from print_messages import print_messages as log
from setup_environment import setup_environment as setup

class CollectRasters:
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Collect historical imagery rasters"
        self.description = ""
        self.category = "Historical Imagery"
        self.canRunInBackground = False

    def getParameterInfo(self):
        """Define the tool parameters."""      
        params = []
        return params

    def isLicensed(self):
        """Set whether the tool is licensed to execute."""
        return True

    def execute(self, parameters, messages):
        """The source code of the tool."""
        # Setup
        setup()
        
        project = arcpy.mp.ArcGISProject("Current")
        orig_map = project.activeMap
        lyrs = orig_map.listLayers("*Key")

        for lyr in lyrs:
            if lyr.visible:
                log("Grabbing rasters for ", lyr.name)
                # get year from key feature class
                year = lyr.name.replace(" Key", "")
                oidfield = arcpy.Describe(lyr).OIDFieldName

                # get selected features in layer
                selection_tuple = tuple(lyr.getSelectionSet())
                selection = "("+",".join([str(i) for i in selection_tuple])+")"
                expression = "{0} IN{1}".format(arcpy.AddFieldDelimiters(lyr,oidfield),selection)
                with arcpy.da.SearchCursor(lyr, ("FULLPATH","IMAGENAME"), expression) as cursor:
                    for row in cursor:
                        # get raster filepath from attributes
                        path = "{}\{}".format(row[0], row[1])
                        # make a nice name
                        lyr_name = row[1].split(".")[0] + " " + year
                        # prevent adding existing maps
                        existing = orig_map.listLayers(lyr_name)
                        if len(existing) == 0:
                            # make raster layer from path
                            new_lyr = arcpy.management.MakeRasterLayer(path, path.split('\\')[-1])
                            new_lyr = new_lyr.getOutput(0)
                            # add raster to group
                            grp_lyr = orig_map.listLayers("In Use Map Layers")[0]
                            new_lyr = orig_map.addLayerToGroup(grp_lyr, new_lyr)[0]
                            # rename raster
                            new_lyr.name = lyr_name
                            new_lyr.visible = False
                            # collapse each added layer
                            new_lyr_cim = new_lyr.getDefinition('V3')
                            new_lyr_cim.expanded = False
                            new_lyr.setDefinition(new_lyr_cim)

        return


















































