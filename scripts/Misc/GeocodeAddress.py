# --------------------------------------------------------------------------------
# Name:        Geocode Address
# Purpose:     This tool takes an address and returns a geocoded point
#
# License:     GNU Affero General Public License v3.
#              Full license in LICENSE file, or at <https://www.gnu.org/licenses/>
# --------------------------------------------------------------------------------

import os
import arcpy

from helpers import license
from helpers import print_messages as log
from helpers import setup_environment as setup

class GeocodeAddress(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "NY Geocode Address"
        self.description = "Geocode NY address to point"
        self.category = "Misc"
        self.canRunInBackground = False

    def isLicensed(self):
        """Set whether the tool is licensed to execute."""
        return license()

    def getParameterInfo(self):
        """Define parameter definitions"""
        param0 = arcpy.Parameter(
            displayName="Street Name and Number",
            name="street_name_num",
            datatype="GPString",
            parameterType="Required",
            direction="Input")

        param1 = arcpy.Parameter(
            displayName="City/Town",
            name="city_town",
            datatype="GPString",
            parameterType="Required",
            direction="Input")

        param2 = arcpy.Parameter(
            displayName="State (two letter)",
            name="state",
            datatype="GPString",
            parameterType="Required",
            direction="Input")

        param3 = arcpy.Parameter(
            displayName="Zip Code",
            name="zip_code",
            datatype="GPString",
            parameterType="Required",
            direction="Input")
        
        params = [param0, param1, param2, param3]
        return params

    def updateParameters(self, parameters):
        # default state
        if parameters[2].value == None:
            parameters[2].value = "NY"

        return

    def execute(self, parameters, messages):
        """The source code of the tool."""
        # setup
        log("setting up project")
        project, active_map = setup()
        spatial_reference_name = active_map.spatialReference.name
        spatial_reference = arcpy.SpatialReference(spatial_reference_name)

        # read in parameters
        log("reading in address")
        address = parameters[0].valueAsText
        town = parameters[1].valueAsText
        state = parameters[2].valueAsText
        zipcode = parameters[3].valueAsText

        # Create a new Locator object from the NY Geocoding Service
        log("creating locator")
        locator_path = "https://gisservices.its.ny.gov/arcgis/rest/services/Locators/Street_and_Address_Composite/GeocodeServer"
        locator = arcpy.geocoding.Locator(locator_path)

        # return candidates
        log("geolocating address")
        geocoding_candidates = locator.geocode("{}, {}, {} {}".format(address, town, state, zipcode), False)

        out_loc = None
        if len(geocoding_candidates) == 0:
            # return warning
            arcpy.AddWarning("Warning: Couldn't find any matches for the address given")
            return
        else:
            out_loc = geocoding_candidates[0]

        # get point and add to map
        log("adding data to map")
        point = out_loc["Shape"]
        point_geometry = arcpy.PointGeometry(point, spatial_reference)
        output_name = arcpy.ValidateTableName(address)
        output_path = os.path.join(arcpy.env.workspace, output_name)
        arcpy.management.CopyFeatures(point_geometry, output_path)
        address_fc = active_map.addDataFromPath(output_path)

        # zoom to layer
        log("zooming to layer")
        ext = arcpy.Describe(address_fc).extent
        cam = project.activeView.camera
        cam.setExtent(ext)

        # save project
        log("saving project")
        project.save()
        return point_geometry
