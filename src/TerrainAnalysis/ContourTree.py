# --------------------------------------------------------------------------------
# Name:        Contour Tree
# Purpose:     TODO.
#
# License:     Contextual Copyleft AI (CCAI) License v1.0.
#              Full license in LICENSE file.
# --------------------------------------------------------------------------------

import os

import arcpy

from helpers import license, empty_workspace, set_required_parameter, reload_module, log, warn, \
    LINEAR_UNITS, Z_UNITS, get_z_unit, raster_and_layer, LINEAR_UNITS, LinearUnit, fc_to_geometry
from helpers import setup_environment as setup
from helpers import validate_spatial_reference as validate

class ContourTree:
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Contour Tree"
        self.description = "Contour Tree"
        self.category = "Terrain Analysis"

    def getParameterInfo(self):
        """Define parameter definitions"""
        param0 = arcpy.Parameter(
            displayName="DEM",
            name="dem",
            datatype="GPRasterLayer",
            parameterType="Required",
            direction="Input")

        param1 = arcpy.Parameter(
            displayName="Z Unit",
            name="z_unit",
            datatype="GPString",
            parameterType="Required",
            direction="Input")
        param1.filter.list = Z_UNITS

        param2 = arcpy.Parameter(
            displayName="Analysis Area",
            name="analysis_area",
            datatype="GPExtent",
            parameterType="Optional",
            direction="Input")
        param2.controlCLSID = '{15F0D1C1-F783-49BC-8D16-619B8E92F668}'

        param3 = arcpy.Parameter(
            displayName="Contour Interval",
            name="small_radius",
            datatype="GPLinearUnit",
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


    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool parameter."""
        # make optional parameters[3] required based off of parameters[2]
        validate(parameters)

        return

    def updateParameters(self, parameters):
        # find z unit of raster based on vertical coordinate system
        #  - if there is none, let the user define it
        #  - if it exists, set the value and hide the parameter
        #  - if it doesn't exist show the parameter and set the value to None
        if not parameters[0].hasBeenValidated:
            if parameters[0].value:
                z_unit = get_z_unit(parameters[0].value)
                if z_unit is not None:
                    parameters[1].enabled = False
                    parameters[1].value = z_unit
                else:
                    parameters[1].enabled = True
                    parameters[1].value = None
            else:
                parameters[1].enabled = False
                parameters[1].value = None

        return

    @reload_module(__name__)
    def execute(self, parameters, messages):
        """The source code of the tool."""
        # Setup
        log("setting up project")
        project, active_map = setup()
        spatial_reference_name = active_map.spatialReference.name
        spatial_reference = arcpy.SpatialReference(spatial_reference_name)
        env_path = r"{}".format(arcpy.env.workspace)

        # read in parameters
        log("reading in parameters")
        dem, _ = raster_and_layer(parameters[0].value)
        z_unit = LINEAR_UNITS[parameters[1].valueAsText]
        extent = parameters[2].value
        contour_interval = LinearUnit(parameters[3].valueAsText).to_unit(z_unit).length
        output_file = parameters[4].valueAsText

        # set extent
        if extent is not None:
            arcpy.env.extent = extent

        # # create scratch layers
        # log("creating scratch layers")
        scratch_contour = arcpy.CreateScratchName("scratch_contour", data_type="DEFeatureClass", workspace=arcpy.env.scratchGDB)
        scratch_poly = arcpy.CreateScratchName("scratch_poly", data_type="DEFeatureClass", workspace=arcpy.env.scratchGDB)
        # scratch_line = arcpy.CreateScratchName("scratch_line", data_type="DEFeatureClass", workspace=arcpy.env.scratchGDB)

        # contour
        log("contour")
        arcpy.sa.Contour(
            in_raster=dem,
            out_polyline_features=scratch_contour,
            contour_interval=contour_interval,
            base_contour=0,
        )

        # log("hi")
        # arcpy.management.FeatureToPolygon(scratch_contour, scratch_poly)
        # log("bye")
        # arcpy.management.FeatureToLine(scratch_poly, output_file)

        old_contours = fc_to_geometry(scratch_contour, ["SHAPE@", "Contour"])

        polygons = [[arcpy.Polygon(geo.getPart()), elev] for geo, elev in old_contours]

        new_contours = [[arcpy.Polyline(geo.getPart()), elev] for geo, elev in polygons if geo.partCount > 0]

        closed_contours = [i for i, j in zip(old_contours, new_contours) if i[0] == j[0]]

        out_name = scratch_contour.split("\\")[-1]

        output_file = arcpy.management.CreateFeatureclass(env_path, out_name, "POLYLINE", spatial_reference=spatial_reference)
        arcpy.management.AddField(output_file, "Contour", "LONG")
        with arcpy.da.InsertCursor(output_file, ["SHAPE@", "Contour"]) as cursor:
            for closed_contour in closed_contours:
                cursor.insertRow(closed_contour)

        log("adding results to map")
        active_map.addDataFromPath(output_file)
        return


        # get setof objectIDs
        log("getting spatial relationships")
        info = {}
        with arcpy.da.SearchCursor(output_file, field_names=['OID@', 'SHAPE@']) as lines:
            for line in lines:
                oid = line[0]
                shape = line[1]
                polygon = arcpy.Polygon(shape.getPart())
                oids_within = [row[0] for row in arcpy.da.SearchCursor(output_file, field_names=['OID@'], spatial_filter=polygon, spatial_relationship="CONTAINS")]
                info[oid] = oids_within
        log(info)

        # add results to map
        log("adding results to map")
        active_map.addDataFromPath(output_file)

        # cleanup
        log("deleting unneeded data")
        empty_workspace(arcpy.env.scratchGDB, keep=[])

        # save
        log("saving project")
        project.save()

        return
