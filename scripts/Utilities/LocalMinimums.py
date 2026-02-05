# --------------------------------------------------------------------------------
# Name:        Local Minimums
# Purpose:     This tool finds local minimums that are larger minimums than the
#              given threshold value.
#
#              example: minimums greater than the diameter of a proposed pipe would
#                       be detected - this would correspond to areas where water
#                       would pool after draining
#
# License:     GNU Affero General Public License v3.
#              Full license in LICENSE file, or at <https://www.gnu.org/licenses/>
# --------------------------------------------------------------------------------

import arcpy

from ..helpers import license, get_z_unit, z_units, empty_workspace, reload_module, log
from ..helpers import setup_environment as setup
from ..helpers import validate_spatial_reference as validate

class LocalMinimums:
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Local Minimums"
        self.description = "Find local minimums along line for a given raster"
        self.category = "Utilities"
        self.canRunInBackground = False

    def isLicensed(self):
        """Set whether the tool is licensed to execute."""
        return license()

    def getParameterInfo(self):
        """Define the tool parameters."""
        param0 = arcpy.Parameter(
            displayName="Line",
            name="line",
            datatype="GPFeatureLayer",
            parameterType="Required",
            direction="Input")
        param0.filter.list = ["Polyline"]
        param0.controlCLSID = '{60061247-BCA8-473E-A7AF-A2026DDE1C2D}' # allows line creation

        param1 = arcpy.Parameter(
            displayName="DEM",
            name="dem",
            datatype="GPRasterLayer",
            parameterType="Required",
            direction="Input")

        param2 = arcpy.Parameter(
            displayName="Z Unit",
            name="z_unit",
            datatype="GPString",
            parameterType="Required",
            direction="Input")
        param2.filter.list = z_units

        param3 = arcpy.Parameter(
            displayName="Analysis Area",
            name="analysis_area",
            datatype="GPExtent",
            parameterType="Optional",
            direction="Input")
        param3.controlCLSID = '{15F0D1C1-F783-49BC-8D16-619B8E92F668}'

        param4 = arcpy.Parameter(
            displayName="Search Interval",
            name="search_distance",
            datatype="GPLinearUnit",
            parameterType="Required",
            direction="Input")

        param5 = arcpy.Parameter(
            displayName="Minimum Elevation Difference Threshold",
            name="threshold",
            datatype="GPLinearUnit",
            parameterType="Required",
            direction="Input")

        param6 = arcpy.Parameter(
            displayName="Output Features",
            name="out_features",
            datatype="DEFeatureClass",
            parameterType="Required",
            direction="Output")
        param6.parameterDependencies = [param0.name]
        param6.schema.clone = True

        params = [param0, param1, param2, param3, param4, param5, param6]
        return params

    def updateParameters(self, parameters):
        # default search interval
        if parameters[4].value is None:
            parameters[4].value = "1 Meters"

        # default threshold value
        if parameters[5].value is None:
            parameters[5].value = "2 InchesUS"

        # find z unit of raster based on vertical coordinate system
        #  - if there is none, let the user define it
        #  - if it exists, set the value and hide the parameter
        #  - if it doesn't exist show the parameter and set the value to None
        if not parameters[1].hasBeenValidated:
            if parameters[1].value:
                z_unit = get_z_unit(parameters[1].value)
                if z_unit:
                    parameters[2].enabled = False
                    parameters[2].value = z_unit
                else:
                    parameters[2].enabled = True
                    parameters[2].value = None
            else:
                parameters[2].enabled = False
                parameters[2].value = None

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
        spatial_reference_name = active_map.spatialReference.name
        spatial_reference = arcpy.SpatialReference(spatial_reference_name)
        arcpy.env.outputCoordinateSystem = spatial_reference

        log("reading in parameters")
        line = parameters[0].value
        dem_layer = parameters[1].value
        dem = arcpy.Raster(dem_layer.name)
        z_linear_unit = parameters[2].value
        extent = parameters[3].value
        search_interval = parameters[4].valueAsText
        threshold, threshold_unit = parameters[5].valueAsText.split(" ")
        threshold = float(threshold) * arcpy.LinearUnitConversionFactor(threshold_unit, z_linear_unit)
        output_file = parameters[6].valueAsText

        # create scratch layers
        scratch_line = arcpy.CreateScratchName("line", "DEFeatureClass", arcpy.env.scratchGDB)

        # clip or copy feature class to scratch layer
        if extent:
            log("clipping line to analysis area")
            arcpy.env.extent = extent
            arcpy.analysis.Clip(line, extent.polygon, scratch_line)
        else:
            arcpy.management.CopyFeatures(line, scratch_line)

        # generate points along line
        log("generate points along line")
        arcpy.edit.Densify(scratch_line, "DISTANCE", search_interval)

        # iterate through lines and points
        log("finding local minimums")
        with arcpy.da.SearchCursor(scratch_line, ["SHAPE@"]) as cursor:
            # keep track of local minimums
            local_minimums = []

            for sub_line in cursor:
                # helper variables to find local minimums
                elev_prev = -9999
                lowpoint = None
                lowpoint_elev = -9999
                prev_local_maximum_elev = -9999

                # iterate through each vertex of the given stream polyline
                num_vertices = len(sub_line[0][0])
                for i in range(num_vertices):
                    # get current vertex and elevation
                    vertex = sub_line[0][0][i]
                    coord = "{} {}".format(vertex.X, vertex.Y)
                    elev_cur = arcpy.management.GetCellValue(dem, coord)
                    elev_cur = float(elev_cur.getOutput(0))

                    # first point
                    if i == 0:
                        lowpoint = vertex
                        lowpoint_elev = elev_cur

                    if i == num_vertices - 1:
                        if elev_cur < lowpoint_elev:
                            lowpoint = vertex
                            lowpoint_elev = elev_cur
                        delta_1 = threshold if prev_local_maximum_elev == -9999 else prev_local_maximum_elev - lowpoint_elev
                        if delta_1 >= threshold:
                            local_minimums.append(arcpy.PointGeometry(lowpoint))

                    # downhill
                    elif elev_prev > elev_cur:
                        delta_1 = threshold if prev_local_maximum_elev == -9999 else prev_local_maximum_elev - lowpoint_elev
                        delta_2 = elev_prev - lowpoint_elev

                        # both pass
                        if delta_1 >= threshold and delta_2 >= threshold:
                            local_minimums.append(arcpy.PointGeometry(lowpoint))
                            prev_local_maximum_elev = elev_prev
                            lowpoint = vertex
                            lowpoint_elev = elev_cur

                        # 1st threshold passes
                        elif delta_1 >= threshold and delta_2 < threshold:
                            if prev_local_maximum_elev == -9999:
                                if elev_cur < lowpoint_elev:
                                    lowpoint = vertex
                                    lowpoint_elev = elev_cur
                            elif elev_cur < lowpoint_elev:
                                lowpoint = vertex
                                lowpoint_elev = elev_cur
                            else:
                                pass

                        # 2nd passes
                        elif delta_1 < threshold and delta_2 >= threshold:
                            prev_local_maximum_elev = elev_prev
                            lowpoint = vertex
                            lowpoint_elev = elev_cur

                        # neither passes
                        else:
                            if elev_cur < lowpoint_elev:
                                lowpoint = vertex
                                lowpoint_elev = elev_cur

                    # uphill
                    else:
                        pass

                    # setup for next iteration
                    elev_prev = elev_cur

            # add points to map
            if len(local_minimums) > 0:
                log("copying points to feature class")
                arcpy.management.CopyFeatures(local_minimums, output_file)
                #log("defining spatial reference of feature")
                #arcpy.management.DefineProjection(output_file,spatial_reference)
                log("adding minimums to map")
                active_map.addDataFromPath(output_file)
            else:
                log("no local minimums found")

        # cleanup
        log("deleting unneeded data")
        empty_workspace(arcpy.env.scratchGDB, keep=[])

        # save
        log("saving project")
        project.save()

        return
