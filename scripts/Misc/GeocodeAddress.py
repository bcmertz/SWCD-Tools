# --------------------------------------------------------------------------------
# Name:        Geocode Address
# Purpose:     This tool takes an address and returns a geocoded point
#
# License:     GNU Affero General Public License v3.
#              Full license in LICENSE file, or at <https://www.gnu.org/licenses/>
# --------------------------------------------------------------------------------

import os
import arcpy

from ..helpers import license, reload_module, log
from ..helpers import setup_environment as setup

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
            displayName="Addresses",
            name="addresses",
            datatype="GPString",
            parameterType="Required",
            multiValue="True",
            direction="Input")

        param1 = arcpy.Parameter(
            displayName="Output Points Feature",
            name="out_features",
            datatype="DEFeatureClass",
            parameterType="Required",
            direction="Output")
        param1.parameterDependencies = [param0.name]
        param1.schema.clone = True

        params = [param0, param1]
        return params

    def updateParameters(self, parameters):
        return

    @reload_module(__name__)
    def execute(self, parameters, messages):
        """The source code of the tool."""
        # setup
        log("setting up project")
        project, active_map = setup()
        spatial_reference_name = active_map.spatialReference.name
        spatial_reference = arcpy.SpatialReference(spatial_reference_name)

        # read in parameters
        log("reading in addresses")
        addresses = parameters[0].valueAsText.replace("'","").split(";")
        output_file = parameters[1].valueAsText
        out_name = output_file.split("\\")[-1]
        out_dir = os.path.dirname(output_file)

        # Create a new Locator object from the NY Geocoding Service
        log("creating locator")
        locator_path = "https://gisservices.its.ny.gov/arcgis/rest/services/Locators/Street_and_Address_Composite/GeocodeServer"
        locator = arcpy.geocoding.Locator(locator_path)

        # return candidates
        log("geolocating addresses")
        points = {}
        for address in addresses:
            geocoding_candidates = locator.geocode("{}".format(address), False)

            out_loc = None
            if len(geocoding_candidates) == 0:
                # return warning
                arcpy.AddWarning("Warning: Couldn't find any matches for address '{}'".format(address))
                continue
            else:
                out_loc = geocoding_candidates[0]

            point = out_loc["Shape"]
            point_geometry = arcpy.PointGeometry(point, spatial_reference)
            points[address] = point_geometry

        # get point and add to map
        log("adding data to map")
        points_fc = arcpy.management.CreateFeatureclass(out_dir, out_name, "POINT", spatial_reference=spatial_reference)
        arcpy.management.AddField(points_fc, "Address", "TEXT")
        with arcpy.da.InsertCursor(points_fc, ["Address", "SHAPE@"]) as points_fc:
            for address in points:
                points_fc.insertRow([address, points[address]])
        address_fc = active_map.addDataFromPath(output_file)

        # zoom to layer
        log("zooming to layer")
        ext = arcpy.Describe(address_fc).extent
        cam = project.activeView.camera
        cam.setExtent(ext)

        # save project
        log("saving project")
        project.save()
        return
