# --------------------------------------------------------------------------------------------------
# Name:        Image Differencing - Setup
# Purpose:     This tool uses precipitation data to select the optimal SWIR rasters for image
#              differencing analysis to detect agricultural drainage tile.
#
# License:     GNU Affero General Public License v3.
#              Full license in LICENSE file, or at <https://www.gnu.org/licenses/>
# --------------------------------------------------------------------------------------------------

import glob
import arcpy
from datetime import datetime, timedelta

from ..helpers import license, reload_module, log, add_layer_to_group
from ..helpers import setup_environment as setup
from ..helpers import validate_spatial_reference as validate

class ImageDifferencingSetup(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Image Differencing - Setup"
        self.description = "Setup image differencing workflow to model potential tile drainage areas"
        self.category = "Hydrology\\Drainage Tile"
        self.canRunInBackground = False

    def getParameterInfo(self):
        """Define parameter definitions"""
        param0 = arcpy.Parameter(
            displayName="Precipitation Data",
            name="precip",
            datatype="DETable",
            parameterType="Required",
            direction="Input")

        param1 = arcpy.Parameter(
            displayName="Date Field",
            name="date_field",
            datatype="GPString",
            parameterType="Required",
            direction="Input")
        param1.filter.type = "ValueList"
        param1.filter.list = []

        param2 = arcpy.Parameter(
            displayName="Precipitation Field",
            name="precip_field",
            datatype="GPString",
            parameterType="Required",
            direction="Input")
        param2.filter.type = "ValueList"
        param2.filter.list = []

        param3 = arcpy.Parameter(
            displayName="SWIR Data Folder",
            name="folder",
            datatype="DEFolder",
            parameterType="Required",
            direction="Input")

        param4 = arcpy.Parameter(
            displayName="Number of raster options per location",
            name="num",
            datatype="GPLong",
            parameterType="Required",
            direction="Input")

        params = [param0, param1, param2, param3, param4]
        return params

    def isLicensed(self):
        """Set whether the tool is licensed to execute."""
        return license()

    def updateParameters(self, parameters):
        # get soils field
        if not parameters[0].hasBeenValidated:
            if parameters[0].value:
                parameters[1].enabled = True
                parameters[2].enabled = True
                fields = [f.name for f in arcpy.ListFields(parameters[0].value)]
                parameters[1].filter.list = fields
                parameters[2].filter.list = fields
                if "DATE" in fields:
                    parameters[1].value = "DATE"
                if "PRCP" in fields:
                    parameters[2].value = "PRCP"
            else:
                parameters[1].enabled = False
                parameters[2].enabled = False
                parameters[1].value = None
                parameters[2].value = None

        if parameters[4].value == None:
            parameters[4].value = 3

        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool parameter."""
        validate(parameters)
        return

    @reload_module(__name__)
    def execute(self, parameters, messages):
        """The source code of the tool."""
        # Setup
        log("setting up project")
        project, active_map = setup()

        log("reading in parameters")
        precip = parameters[0].valueAsText
        precip_field_date = parameters[1].valueAsText
        precip_field_in = parameters[2].valueAsText
        swir_folder = parameters[3].valueAsText
        num = parameters[4].value

        # collect all short-wave infrared files (Band 6 - B6)
        #
        # file structure and description
        # LC08_L2SP_015030_20250812_20250821_02_T1_SR_B6.TIF (example file name)
        # LXSS_LLLL_PPPRRR_YYYYMMDD_yyyymmdd_CC_TX_*.tif
        # L -Landsat
        # X - Sensor of: C = Combined TIRS and OLI Indicates which sensor collected data for this product
        # SS - Landsat satellite (08 for Landsat 8, 09 for Landsat 9)
        # LLLL - Processing level (L2SP, L2SR)
        # PPPRRR - Satellite orbit location
        # YYYYMMDD - Acquisition date of the image
        # yyyymmdd - Processing date of the image
        # CC - Collection number (e.g., 02)
        # TX - Collection category: "T1" for Tier 1 (highest quality), "T2" for Tier 2
        log("collecting all unique SWIR dataset dates")
        swir_files = glob.glob("{}/*_SR_B6.tif".format(swir_folder))
        # find SWIR image collection dates
        swir_dates = set()
        for i in swir_files:
            date = i.split("_")[-6]
            year = int(date[:4])
            month = int(date[4:6])
            day = int(date[6:8])
            swir_dates.add(datetime(year, month, day))

        # read in all precip data to dictionary
        log("reading in precipitation data")
        precip_table = arcpy.mp.Table(precip)
        precip_data = {} # date (datetime object): precipitation (inches - float)
        with arcpy.da.SearchCursor(precip_table, [precip_field_date, precip_field_in]) as cursor:
            for row in cursor:
                precip_data[row[0]] = row[1]

        # find relevant precip data and calculate antecedent moisture conditions
        log("calculating precipitation metrics")
        dryness = {} # low is better
        wetness = {} # high is better
        for date in swir_dates:
            if date in precip_data:
                day_0 = precip_data[date]
                day_1 = precip_data[date - timedelta(days=1)]
                day_2 = precip_data[date - timedelta(days=2)]
                day_3 = precip_data[date - timedelta(days=3)]

                dryness[date] = day_0 + day_1 + day_2 + day_3
                wetness[date] = 0 if day_0 > 0.05 else day_1 + day_2 + day_3

        log("sorting precipitation data")
        sorted_dry = sorted(dryness, key=lambda x: dryness[x])
        sorted_wet = sorted(wetness, key=lambda x: wetness[x], reverse=True)

        log("creating output group layer")
        wet_group = active_map.createGroupLayer("Wet SWIR Rasters")
        dry_group = active_map.createGroupLayer("Dry SWIR Rasters")
        log("adding SWIR rasters to map")
        for i in range(num, 0, -1):
            wet_day = sorted_wet[i]
            wet_day_formatted = wet_day.strftime("%Y%m%d")
            wet_raster = glob.glob("{}/*{}*SR_B6.tif".format(swir_folder, wet_day_formatted))[0]
            dry_day = sorted_dry[i]
            dry_day_formatted = dry_day.strftime("%Y%m%d")
            dry_raster = glob.glob("{}/*{}*SR_B6.tif".format(swir_folder, dry_day_formatted))[0]

            wet_fc = active_map.addDataFromPath(wet_raster)
            dry_fc = active_map.addDataFromPath(dry_raster)
            wet_fc.name = "wet_raster #{} - {} in. ({})".format(i, wetness[wet_day], wet_day_formatted)
            dry_fc.name = "dry_raster #{} - {} in. ({})".format(i, dryness[dry_day], dry_day_formatted)
            add_layer_to_group(active_map, wet_group, wet_fc, hide=True)
            add_layer_to_group(active_map, dry_group, dry_fc, hide=True)

        # save project
        log("saving project")
        project.save()

        return
