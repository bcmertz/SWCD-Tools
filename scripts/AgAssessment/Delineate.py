# --------------------------------------------------------------------------------
# Name:        Delineate
# Purpose:     This tool finds a parcel and sets up an ag assessment project
#
# License:     GNU Affero General Public License v3.
#              Full license in LICENSE file, or at <https://www.gnu.org/licenses/>
# --------------------------------------------------------------------------------
import os
import arcpy
import shutil
import pathlib
import openpyxl

from helpers import license, sanitize
from helpers import print_messages as log
from helpers import setup_environment as setup
from helpers import validate_spatial_reference as validate

class Delineate(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "1. Delineate Parcels"
        self.description = "Delienate parcels and create folder structure"
        self.category = "Automated Ag Assessment"
        self.canRunInBackground = False
 
    def getParameterInfo(self):
        """Define parameter definitions"""
        param0 = arcpy.Parameter(
            displayName="Parcels",
            name="parcels",
            datatype="GPFeatureLayer",
            parameterType="Required",
            direction="Input")
        param0.filter.list = ["Polygon"]
        
        param1 = arcpy.Parameter(
            displayName="Tax ID Number",
            name="tax_id_number",
            datatype="GPString",
            parameterType="Required",
            direction="Input",
            multiValue=True)

        param2 = arcpy.Parameter(
            displayName="Last Name",
            name="last_name",
            datatype="GPString",
            parameterType="Required",
            direction="Input")

        param3 = arcpy.Parameter(
            displayName="First Name",
            name="first_name",
            datatype="GPString",
            parameterType="Required",
            direction="Input")

        param4 = arcpy.Parameter(
            displayName="Mailing Street Name and Number",
            name="street_name_num",
            datatype="GPString",
            parameterType="Required",
            direction="Input")        

        param5 = arcpy.Parameter(
            displayName="Mailing City/Town",
            name="city_town",
            datatype="GPString",
            parameterType="Required",
            direction="Input")

        param6 = arcpy.Parameter(
            displayName="Mailing State (two letter)",
            name="state",
            datatype="GPString",
            parameterType="Required",
            direction="Input")

        param7 = arcpy.Parameter(
            displayName="Mailing Zip Code",
            name="zip_code",
            datatype="GPString",
            parameterType="Required",
            direction="Input")

        param8 = arcpy.Parameter(
            displayName="Output Folder",
            name="output_location",
            datatype="DEFolder",
            parameterType="Required",
            direction="Input")

        params = [param0, param1, param2, param3, param4, param5, param6, param7, param8]
        return params

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool parameter."""
        validate(parameters)
        return

    def isLicensed(self):
        """Set whether the tool is licensed to execute."""
        return license([])

    def execute(self, parameters, messages):
        """The source code of the tool."""
        # Setup
        log("setting up project")
        project, active_map = setup()

        # Parameters
        log("reading in parameters")
        parcel_layer = parameters[0].value
        tax_id_nums = parameters[1].valueAsText.split(";")
        last_name = parameters[2].valueAsText
        first_name = parameters[3].valueAsText
        street_name_num = parameters[4].valueAsText
        city_town = parameters[5].valueAsText
        state = parameters[6].valueAsText
        zip_code = parameters[7].valueAsText
        path_root = parameters[8].valueAsText

        # clear selections from map
        orig_map = active_map
        orig_map.clearSelection()

        # sgw template path
        sgw_template = os.path.join(os.path.dirname(__file__), os.pardir, os.pardir, 'assets', 'Soil Group Worksheet.xlsx')

        # use layout template
        log("finding layout")
        orig_layout = project.importDocument(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir, 'assets', 'agassessment_layout.pagx'))
        layouts = []
        
        for tax_id_num in tax_id_nums:
            layer_name = "{}_{}".format(last_name, tax_id_num)
            sanitized_name = sanitize(layer_name)
            layer_path = "{}\\{}".format(arcpy.env.workspace, sanitized_name)

            # create new map and make it active
            log("creating map for {}".format(tax_id_num))
            new_map = project.copyItem(orig_map, tax_id_num)
            new_map.openView()
            cam = project.activeView.camera

            # create a new layout
            log("creating layout for {}".format(tax_id_num))
            new_layout = project.copyItem(orig_layout, tax_id_num)
            layouts.append(new_layout)
            new_layout.openView()
            
            # set layout's map to new map created
            mf = new_layout.listElements("MAPFRAME_ELEMENT")[0]
            mf.map = new_map
            mf.name = tax_id_num

            # turn off parcel layer
            parcel_layer.visible = False
   
            # create sql expression to select correct parcel
            sql_expr="PRINT_KEY = '{}'".format(tax_id_num)

            # create parcel layer and add it to the map
            log("adding parcel {}".format(tax_id_num))
            feat = arcpy.management.MakeFeatureLayer(parcel_layer, layer_name, sql_expr)
            arcpy.management.CopyFeatures(feat, layer_path)
            lyr = new_map.addDataFromPath(layer_path)
            lyr.name = layer_name

            # update parcel symbology
            log("updating layer symbology {}".format(tax_id_num))
            sym = lyr.symbology
            sym.renderer.symbol.applySymbolFromGallery("Black Outline (2 pts)")
            lyr.symbology = sym

            # Create soil group worksheets for each layout
            log("creating soil group worksheet for {}".format(tax_id_num))
            sgw_path = r'{}\{}.xlsx'.format(path_root, new_layout.name)
            sgw_path = pathlib.PureWindowsPath(sgw_path).as_posix()            
            shutil.copyfile(sgw_template, sgw_path)
            
            # set SWIS code in layout
            log("finding property values for {}".format(tax_id_num))
            swis_box = new_layout.listElements("TEXT_ELEMENT", "SWIS")[0]
            swis_value = [row[0] for row in arcpy.da.SearchCursor(layer_path, "SWIS")][0]
            swis_box.text = "SWIS: {}".format(swis_value)

            # set name in layout
            name_box = new_layout.listElements("TEXT_ELEMENT", "Name")[0]
            name_box.text = "{}, {}".format(last_name, first_name)

            # set municipality in layout
            municipality_box = new_layout.listElements("TEXT_ELEMENT", "Municipality")[0]
            municipality_value = [row[0] for row in arcpy.da.SearchCursor(layer_path, "TOWN")][0]
            municipality_box.text = "{}".format(municipality_value)

            # get property address info
            location_value = [row[0] for row in arcpy.da.SearchCursor(layer_path, "LOCATION")][0]
            agdist_value = [row[0] for row in arcpy.da.SearchCursor(layer_path, "AGDIST")][0]
            if agdist_value in ["", None, " "]:
                agdist_value = "__"
            else:
                agdist_value = "x"

            # set SWIS, municipality, tax map identifier, etc in soil group worksheet
            log("writing values to soil group worksheet {}".format(tax_id_num))
            sgw_workbook = openpyxl.load_workbook(sgw_path)
            ws = sgw_workbook['SGW']
            ws['D24'] = swis_value
            ws['D19'] = municipality_value
            ws['D17'] = location_value
            ws['B20'] = agdist_value
            ws['D26'] = tax_id_num
            ws['F13'] = first_name
            ws['B13'] = last_name
            ws['B15'] = street_name_num
            ws['F15'] = city_town
            ws['J15'] = state
            ws['K15'] = zip_code
            sgw_workbook.save(sgw_path)
            sgw_workbook.close()

            # zoom to layer in map object
            log("zooming map to {}".format(tax_id_num))
            ext = arcpy.Describe(lyr).extent
            cam.setExtent(ext)

            # zoom layout to last active map
            mf = new_layout.listElements("MAPFRAME_ELEMENT")[0]
            mf.camera.setExtent(mf.getLayerExtent(lyr))
            mf.camera.scale = mf.camera.scale * 1.1

            # Need to close layouts for camera change to take effect
            project.closeViews("LAYOUTS")

        # export parcel layouts to folder
        log("exporting layouts")
        for layout in layouts:
            layout_file_path = "{}\{}.pdf".format(path_root, layout.name)
            layout.exportToPDF(layout_file_path)

        # remove unused layout
        project.deleteItem(orig_layout) 
        
        # cleanup
        log("saving project")
        project.save()

        # open folder to print out maps
        log("opening project folder")
        os.startfile(path_root)

        return
