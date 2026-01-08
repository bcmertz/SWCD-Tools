# --------------------------------------------------------------------------------
# Name:        Point Plots
# Purpose:     This tool creates point plots for a given analysis area based off
#              the Upper Susquehanna Coalition (USC) riparian forest buffer
#              yearly monitoring program rates:
#                  < 1/2 acres - monitor 100%
#                  < 3 acres - plot radius 26.3ft; 2 / acre
#                  > 3 acres - plot radius 26.3ft; 1 / acre
#              Consider eventually making these user set to allow for more broad
#              use cases.
#
# License:     GNU Affero General Public License v3.
#              Full license in LICENSE file, or at <https://www.gnu.org/licenses/>
# --------------------------------------------------------------------------------

import os
import math
import arcpy

from helpers import license, empty_workspace, toggle_required_parameter
from helpers import print_messages as log
from helpers import setup_environment as setup
from helpers import validate_spatial_reference as validate

class PointPlots:
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Point Plots"
        self.description = "Point Plots"
        self.category = "Buffer tools"
        self.canRunInBackground = False

    def getParameterInfo(self):
        """Define the tool parameters."""
        param0 = arcpy.Parameter(
            displayName="Project Area",
            name="polygon",
            datatype="GPFeatureLayer",
            parameterType="Required",
            direction="Input")
        param0.filter.list = ["Polygon"]
        param0.controlCLSID = '{60061247-BCA8-473E-A7AF-A2026DDE1C2D}' # allows polygon creation

        param1 = arcpy.Parameter(
            displayName="Output Point Feature Class",
            name="out_point",
            datatype="DEFeatureClass",
            parameterType="Required",
            direction="Output")
        param1.parameterDependencies = [param0.name]

        param2 = arcpy.Parameter(
            displayName="Output point plot GPS coordinates to spreadsheet?",
            name="locations",
            datatype="GPBoolean",
            parameterType="Optional",
            direction="Input")

        param3 = arcpy.Parameter(
            displayName="Output Folder - Coordinates Spreadsheet",
            name="coordinates_output",
            parameterType="Optional",
            datatype="DEType",
            direction="Input")

        params = [param0, param1, param2, param3]
        return params

    def isLicensed(self):
        """Set whether the tool is licensed to execute."""
        return license()

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool parameter."""
        # make optional parameters[4] required based off of parameters[3]
        toggle_required_parameter(parameters[2], parameters[3])

        validate(parameters)
        return

    def updateParameters(self, parameters):
        # toggle asking for coordinate output path
        if not parameters[2].hasBeenValidated:
            if parameters[2].value == True:
                parameters[3].enabled = True
            else:
                parameters[3].enabled = False
        return

    def execute(self, parameters, messages):
        """The source code of the tool."""
        # Setup
        log("setting up project")
        project, active_map = setup()

        log("reading in parameters")
        planting_area = parameters[0].value
        output_points = parameters[1].valueAsText
        coords = parameters[2].value
        output_coords = parameters[3].valueAsText

        # create scratch layers
        log("creating scratch layers")
        scratch_buffer = arcpy.CreateScratchName("scratch_buffer", data_type="DEFeatureClass", workspace=arcpy.env.scratchGDB)
        scratch_dissolve = arcpy.CreateScratchName("scratch_dissolve", data_type="DEFeatureClass", workspace=arcpy.env.scratchGDB)

        # dissolve
        log("dissolve polygons")
        arcpy.management.Dissolve(planting_area, scratch_dissolve, multi_part="MULTI_PART")

        # calculate total area of planting
        log("calculate acreage")
        field_name = "Acres"
        arcpy.management.AddField(scratch_dissolve, field_name, "FLOAT")
        arcpy.management.CalculateGeometryAttributes(in_features=scratch_dissolve, geometry_property=[[field_name, "AREA_GEODESIC"]], area_unit="ACRES_US")

        # determine number of sampling plots
        #   < 1/2 acres - monitor 100%
        #   < 3 acres - plot radius 26.3ft; 2 / acre
        #   > 3 acres - plot radius 26.3ft; 1 / acre
        values = [row[0] for row in arcpy.da.SearchCursor(scratch_dissolve, field_name)]
        acreage = max(set(values))

        radius = 26.3
        num = 1

        if acreage < 0.5:
            log("Buffer less than 0.5 acres, please assess 100% of the buffer without point plots")
        else:
            if acreage >= 0.5 and acreage < 3:
                num = int(math.ceil(acreage * 2))
            elif acreage >= 3:
                num = int(math.ceil(acreage * 1))

            try:
                # create buffer inside the planting area
                log("buffer output area")
                arcpy.analysis.PairwiseBuffer(scratch_dissolve, scratch_buffer, "{} Feet".format(-radius))

                # create random plot centers
                log("create sampling locations")
                arcpy.management.CreateSpatialSamplingLocations(scratch_buffer, output_points, sampling_method="STRAT_POLY", strata_id_field=None, strata_count_method="PROP_AREA", num_samples=num, geometry_type="POINT", min_distance="{} Feet".format(radius*2))

            except:
                log("Failed to create {} point plots with a radius of {} feet. It is likely because the buffer is too narrow to fit all of the point plots.".format(num, radius))

                radius = 11.8
                num = int(math.ceil(acreage * 10))

                log("Trying again to make {} point plots with a radius of {} feet.".format(num, radius))

                # create buffer inside the planting area
                log("buffer output area")
                arcpy.analysis.PairwiseBuffer(scratch_dissolve, scratch_buffer, "{} Feet".format(-radius))

                # create random plot centers
                log("create sampling locations")
                arcpy.management.CreateSpatialSamplingLocations(scratch_buffer, output_points, sampling_method="STRAT_POLY", strata_id_field=None, strata_count_method="PROP_AREA", num_samples=num, geometry_type="POINT", min_distance="{} Feet".format(radius*2))

            # add data to map
            log("add data to map")
            points_lyr = active_map.addDataFromPath(output_points)

            if coords:
                log("calculating point x y coordinates")
                # add coordinate fields
                arcpy.management.AddField(points_lyr, "x_coord", "FLOAT", 6, 6, field_alias="X Coordinate")
                arcpy.management.AddField(points_lyr, "y_coord", "FLOAT", 6, 6, field_alias="X Coordinate")

                # calculate geometry - coordinates
                arcpy.management.CalculateGeometryAttributes(in_features=points_lyr.name, geometry_property=[["x_coord", "POINT_X"]],coordinate_format="DD")
                arcpy.management.CalculateGeometryAttributes(in_features=points_lyr.name, geometry_property=[["y_coord", "POINT_Y"]],coordinate_format="DD")

                # export attribute table to csv at path
                log("exporting point plot coordinates")
                arcpy.conversion.ExportTable(output_points, r"{}/point_plots.csv".format(output_coords))

                # open coordinates folder
                log("opening folder with coordinates")
                os.startfile(output_coords)

        # cleanup
        log("deleting unneeded data")
        empty_workspace(arcpy.env.scratchGDB, keep=[])

        # save
        log("saving project")
        project.save()

        return
