# --------------------------------------------------------------------------------
# Name:        Watershed Delineation
# Purpose:     This tool delineates a watershed from a DEM for a given pour point.
#
# License:     GNU Affero General Public License v3.
#              Full license in LICENSE file, or at <https://www.gnu.org/licenses/>
# --------------------------------------------------------------------------------

import arcpy

from helpers import license, get_oid
from helpers import print_messages as log
from helpers import setup_environment as setup
from helpers import validate_spatial_reference as validate

class WatershedDelineation(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Watershed Delineation"
        self.description = "Calculate watershed for a given point"
        self.category = "Hydrology"
        self.canRunInBackground = False

    def getParameterInfo(self):
        """Define parameter definitions"""
        param0 = arcpy.Parameter(
            displayName="DEM",
            name="dem",
            datatype="GPRasterLayer",
            parameterType="Required",
            direction="Input")

        param1 = arcpy.Parameter(
            displayName="Analysis Area",
            name="analysis_area",
            datatype="GPExtent",
            parameterType="Optional",
            direction="Input")
        param1.controlCLSID = '{15F0D1C1-F783-49BC-8D16-619B8E92F668}'

        param2 = arcpy.Parameter(
            displayName="Pour Point",
            name="pourpoint",
            datatype="GPFeatureLayer",
            parameterType="Required",
            direction="Input")
        param2.filter.list = ["Point"]
        param2.controlCLSID = '{60061247-BCA8-473E-A7AF-A2026DDE1C2D}' # allows point creation

        param3 = arcpy.Parameter(
            displayName="Snap Pour Point Max Adjustment Distance",
            name="snap_adjustment",
            datatype="GPDouble",
            parameterType="Required",
            direction="Input")

        param4 = arcpy.Parameter(
            displayName="Output Features",
            name="out_features",
            datatype="DEFeatureClass",
            parameterType="Required",
            direction="Output")
        param4.parameterDependencies = [param0.name]
        param4.schema.clone = True

        params = [param0, param1, param2, param3, param4]
        return params

    def isLicensed(self):
        """Set whether the tool is licensed to execute."""
        return license(['Spatial'])

    def updateParameters(self, parameters):
        # Default snap pour point adjustment value
        if parameters[3].value == None:
            parameters[3].value = 10
        return

    def updateMessages(self, parameters):
        validate(parameters)
        return

    def execute(self, parameters, messages):
        """The source code of the tool."""
        # Setup
        log("setting up project")
        project, active_map = setup()

        # read in parameters
        dem_layer = parameters[0].value
        dem = arcpy.Raster(dem_layer.name)
        extent = parameters[1].value
        pour_points = parameters[2].value
        snap_adjustment = parameters[3].value
        output_file = parameters[4].valueAsText

        # set analysis extent
        if extent:
            arcpy.env.extent = extent

        # create scratch layers
        log("creating scratch layers")
        clip_flow_accumulation_scratch = arcpy.CreateScratchName("clip_flow_accumulation_scratch", data_type="RasterDataset", workspace=arcpy.env.scratchFolder)

        # fill raster
        log("filling raster")
        fill_raster_scratch = arcpy.sa.Fill(dem)

        # flow direction
        log("calculating flow direction")
        flow_direction_scratch = arcpy.sa.FlowDirection(fill_raster_scratch)

        # flow accumulation
        log("calculating flow accumulation")
        flow_accumulation_scratch = arcpy.sa.FlowAccumulation(flow_direction_scratch)

        # adjust pour points
        log("adjusting pour point data")
        pour_points_oid = get_oid(pour_points)
        pour_points_adjusted = arcpy.sa.SnapPourPoint(pour_points, flow_accumulation_scratch, snap_adjustment, pour_points_oid)

        # watershed
        log("delineating watershed")
        watershed = arcpy.sa.Watershed(flow_direction_scratch, pour_points_adjusted)

        # watershed raster to polyon
        log("converting watershed to polygon")
        watershed_polygon_path = arcpy.CreateUniqueName(output_file)
        watershed_polygon = arcpy.conversion.RasterToPolygon(watershed, watershed_polygon_path, create_multipart_features=True)
        watershed_polygon = active_map.addDataFromPath(watershed_polygon)
        sym = watershed_polygon.symbology
        sym.updateRenderer('UniqueValueRenderer')
        sym.renderer.fields = ['gridcode']
        watershed_polygon.symbology = sym

        # remove temporary variables
        log("cleaning up")
        arcpy.management.Delete([clip_flow_accumulation_scratch])

        # save and exit program successfully
        log("saving project")
        project.save()

        return
