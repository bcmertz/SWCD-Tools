# --------------------------------------------------------------------------------
# Name:        Watershed Delineation
# Purpose:     This tool delineates a watershed from a DEM for a given pour point.
#
# Author:      Reya Mertz
#
# Created:     11/2025
# Modified:    11/2025
# License:     GNU Affero General Public License v3.
#              Full license in LICENSE file, or at <https://www.gnu.org/licenses/>
# --------------------------------------------------------------------------------

import arcpy

# setup helpers
import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), "../helpers"))
from print_messages import print_messages as log
from setup_environment import setup_environment as setup
from validate_spatial_reference import validate_spatial_reference as validate
from license import license as license

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
        raster_layer = parameters[0].value
        XMin = parameters[1].value.XMin if parameters[1].value else 0
        YMin = parameters[1].value.YMin if parameters[1].value else 0
        XMax = parameters[1].value.XMax if parameters[1].value else 0
        YMax = parameters[1].value.YMax if parameters[1].value else 0
        extent = arcpy.Extent(XMin, YMin, XMax, YMax)
        if parameters[1].value:
                extent.spatialReference = parameters[1].value.spatialReference
        pour_points = parameters[2].value
        snap_adjustment = parameters[3].value
        output_file = parameters[4].valueAsText

        # create scratch layers
        log("creating scratch layers")
        scratch_dem = "{}\\dem_raster_clip".format(arcpy.env.workspace)
        clip_flow_accumulation_scratch = arcpy.CreateScratchName("clip_flow_accumulation_scratch", data_type="RasterDataset", workspace=arcpy.env.scratchFolder)
        pour_points_adjusted_scratch = "{}\\pour_points_adjusted_scratch".format(arcpy.env.workspace)

        if parameters[1].value:
            # clip DEM raster to the study area
            log("clipping raster to analysis area")
            rectangle = "{} {} {} {}".format(extent.XMin, extent.YMin, extent.XMax, extent.YMax)
            arcpy.management.Clip(raster_layer, rectangle, scratch_dem)
            raster_layer = scratch_dem

        # fill raster
        log("filling raster")
        fill_raster_scratch = arcpy.sa.Fill(raster_layer)

        # flow direction
        log("calculating flow direction")
        flow_direction_scratch = arcpy.sa.FlowDirection(fill_raster_scratch)

        # flow accumulation
        log("calculating flow accumulation")
        flow_accumulation_scratch = arcpy.sa.FlowAccumulation(flow_direction_scratch)

        # adjust pour points
        log("adjusting pour point data")
        pour_points_oid = arcpy.Describe(pour_points).OIDFieldName
        pour_points_adjusted = arcpy.sa.SnapPourPoint(pour_points, flow_accumulation_scratch, snap_adjustment, pour_points_oid)
        pour_points_adjusted.save(pour_points_adjusted_scratch)

        # watershed
        log("delineating watershed")
        watershed = arcpy.sa.Watershed(flow_direction_scratch, pour_points_adjusted_scratch)

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
        arcpy.management.Delete([scratch_dem, clip_flow_accumulation_scratch, pour_points_adjusted_scratch])

        # save and exit program successfully
        log("saving project")
        project.save()

        return
