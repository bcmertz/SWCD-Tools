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

class Process(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "3. Process"
        self.category = "Automated Ag Assessment"
        self.description = "Run after splitting parcels into use areas"

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
    
        maps = project.listMaps()
        layouts = []
        for m in maps:
            # Clear selection
            m.clearSelection()
            # Get Tax ID Number for map
            tax_id_num = m.name
            # Check if we're on a created map
            lyts = project.listLayouts(tax_id_num)
            lyt = ""
            if len(lyts) == 1:
                lyt = lyts[0]
                layouts.append(lyt)
            else:
                continue

            # Helper variables
            soils_layers = []
            use_layers = []
            tables = []

            # Start work
            lyrs = m.listLayers()
            lyr_types = set()
            for lyr in lyrs:
                # Update symbology
                lyr_type = ""
                if "agland" in lyr.name.lower():
                    use_layers.append(lyr)
                    lyr_type = "Agland"
                elif "nonag" in lyr.name.lower():
                    use_layers.append(lyr)
                    lyr_type = "NonAg"
                elif "forest" in lyr.name.lower():
                    use_layers.append(lyr)
                    lyr_type = "Forest"
                else:
                    continue
                lyr_types.add(lyr_type)

                # Create clip layer
                soil_layer = m.listLayers("Soils")[0]
                new_layer_path = "{}\\{}".format(arcpy.env.workspace, "{}_{}_soils".format(sanitize(lyr.name), sanitize(tax_id_num)))
                arcpy.analysis.Clip(soil_layer, lyr, new_layer_path)

                # Dissolve duplicate MUSYMs
                dissolve_layer_path = "{}\\{}".format(arcpy.env.workspace, "{}_{}_soils_dissolved".format(sanitize(lyr.name), sanitize(tax_id_num)))
                arcpy.management.Dissolve(new_layer_path, dissolve_layer_path, "MUSYM")

                # Add to map
                new_layer = m.addDataFromPath(dissolve_layer_path)               
                soils_layers.append(new_layer)
                new_layer.name = "{}_soils".format(lyr.name)

                # Add acreage field
                field_alias = "{} Acres".format(lyr_type)
                arcpy.management.AddField(new_layer, "Acres", "FLOAT", 2, 2, field_alias=field_alias)

                # Calculate geometry
                arcpy.management.CalculateGeometryAttributes(in_features=new_layer.name, geometry_property=[["Acres", "AREA_GEODESIC"]], area_unit="ACRES_US")

                # Update soils clip layer symbology    
                sym = new_layer.symbology
                sym.renderer.symbol.color = {'RGB' : [0, 0, 0, 0]}
                sym.renderer.symbol.outlineColor = {'RGB' : [255, 255, 0, 100]}
                sym.renderer.symbol.size = 1.5
                new_layer.symbology = sym

                # Add label
                new_layer.showLabels = True
                label_class = new_layer.listLabelClasses()[0]
                label_class.visible = True
                label_class.expression = "$feature.MUSYM"

                l_cim = new_layer.getDefinition('V3')
                lc = l_cim.labelClasses[0]
      
                # Update text properties of label
                lc.textSymbol.symbol.height = 12
                lc.textSymbol.symbol.symbol.symbolLayers = [
                    {
                        "type": "CIMSolidFill",
                        "enable": True,
                        "color": {
                            "type": "CIMRGBColor",
                            "values": [255, 255, 0, 100]
                        }
                    }
                ]
                lc.standardLabelPlacementProperties.numLabelsOption = "OneLabelPerPart"

                # Update CIM defintion
                new_layer.setDefinition(l_cim)

                # Get soils layer attribute table and export / extract needed fields for layout
                table_path = "{}\\{}".format(arcpy.env.workspace, "{}_ExportTable".format(sanitize(new_layer.name)))
                arcpy.conversion.ExportTable(new_layer.name, table_path)
                arcpy.management.DeleteField(table_path, ["MUSYM", "Acres"], "KEEP_FIELDS")

                # Add soils table export to the given map
                soils_table = arcpy.mp.Table(table_path)
                tables.append(soils_table)
                addTab = m.addTable(soils_table)
                soils_table_uri = soils_table.URI

                # Get layout table
                tbl = lyt.listElements("MAPSURROUND_ELEMENT", lyr_type)[0]

                # Set layout table to exported attributes table
                tbl_cim = tbl.getDefinition("V3")
                tbl_cim.mapMemberURI = soils_table_uri
                tbl.setDefinition(tbl_cim)

                # Refresh layout
                lyt_cim = lyt.getDefinition('V3')
                lyt.setDefinition(lyt_cim)

                project.save()            
                project.closeViews("LAYOUTS")

            # Reorder layers so soils layers are last
            for soils_layer in soils_layers:
                for use_layer in use_layers:
                    m.moveLayer(use_layer, soils_layer, "AFTER")

            # Remove unused tables
            uses = {'Agland', 'Forest', 'NonAg'}
            for i in uses:
                if not i in lyr_types:
                    tbl_remove = lyt.listElements("MAPSURROUND_ELEMENT", i)[0]
                    lyt.deleteElement(tbl_remove)

            # Display wanted legend items only
            legend = lyt.listElements("LEGEND_ELEMENT")[0]
            legend_items = legend.items
            use_layer_names = [ i.name for i in use_layers ]
            for item in legend_items:
                if item.name in use_layer_names:
                    item.visible = True
                else:
                    item.visible = False

            # Export tables
            soils_tables = []
            for table in tables:
                table_file_path = "{}\{}.csv".format(path_root, table.name)
                soils_tables.append(table_file_path)
                arcpy.conversion.ExportTable(table, table_file_path)

            # Soil group worksheet
            sgw_path = "{}\{}.xlsx".format(path_root, lyt.name)

            # Populate soil group worksheet with values
            sgw_path = pathlib.PureWindowsPath(sgw_path).as_posix()
            sgw_workbook = openpyxl.load_workbook(sgw_path)
            ws = sgw_workbook['SGW']
            for tbl in soils_tables:
                if "agland" in tbl.lower():
                    with open(tbl, 'r') as csvfile:
                        csvreader = csv.reader(csvfile)
                        fields = next(csvreader)
                        idx = 0
                        for row in csvreader:
                            if idx < 24:
                                soil_cell = 'A{}'.format(34 + idx)
                                area_cell = 'H{}'.format(34 + idx)
                                ws[soil_cell] = row[0]
                                ws[area_cell] = round(float(row[1]), 2)
                            else:
                                # overflow
                                soil_cell = 'N{}'.format(9 + idx)
                                area_cell = 'U{}'.format(9 + idx)
                                ws[soil_cell] = row[0]
                                ws[area_cell] = round(float(row[1]), 2)                                
                            idx += 1
                elif "nonag" in tbl.lower():
                    tot = 0
                    with open(tbl, 'r') as csvfile:
                        csvreader = csv.reader(csvfile)
                        fields = next(csvreader)
                        for row in csvreader:
                            tot += float(row[1])
                    ws['K28'] = tot
                elif "forest" in tbl.lower():
                    tot = 0
                    with open(tbl, 'r') as csvfile:
                        csvreader = csv.reader(csvfile)
                        fields = next(csvreader)
                        for row in csvreader:
                            tot += float(row[1])
                    ws['L24'] = tot                
            sgw_workbook.save(sgw_path)
            sgw_workbook.close()

        for layout in layouts:
            layout.openView()

        # Cleanup
        project.save()

        return

