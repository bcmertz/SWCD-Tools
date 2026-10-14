# --------------------------------------------------------------------------------------------------
# Name:        StreamStats
# Purpose:     TODO
#
# License:     Contextual Copyleft AI (CCAI) License v1.0.
#              Full license in LICENSE file.
# --------------------------------------------------------------------------------------------------

# Sources used:
#
# https://www.usgs.gov/streamstats/new-york-streamstats
# Lumia, Richard, Freehafer, D.A., and Smith, M.J., 2006, Magnitude and Frequency of Floods in New York: U.S. Geological Survey Scientific Investigations Report 2006–5112, 152 p.
# Mulvihill, C.I., Baldigo, B.P., Miller, S.J., and DeKoskie, Douglas, 2009, Bankfull Discharge and Channel Characteristics of Streams in New York State: U.S. Geological Survey Scientific Investigations Report 2009-5144, 51 p

import arcpy

from helpers.logging import log
from helpers.parameter import raster_and_layer
from helpers.parameter import validate_spatial_reference as validate
from helpers.tool import EXTENSIONS, license, reload_module
from helpers.tool import setup_environment as setup
from helpers.units import SPATIAL_UNITS, Distance, get_z_unit


class StreamStats:
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "StreamStats"
        self.description = "TODO"
        self.category = "Hydrology"

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
        param1.filter.list = list(SPATIAL_UNITS)

        param2 = arcpy.Parameter(
            displayName="Analysis Area",
            name="analysis_area",
            datatype="GPExtent",
            parameterType="Optional",
            direction="Input")
        param2.controlCLSID = '{15F0D1C1-F783-49BC-8D16-619B8E92F668}'

        param3 = arcpy.Parameter(
            displayName="Small Neighborhood Radius",
            name="small_radius",
            datatype="GPLinearUnit",
            parameterType="Required",
            direction="Input")

        param4 = arcpy.Parameter(
            displayName="Large Neighborhood Radius",
            name="large_radius",
            datatype="GPLinearUnit",
            parameterType="Required",
            direction="Input")

        param5 = arcpy.Parameter(
            displayName="Output Features",
            name="out_features",
            datatype="DEFeatureClass",
            parameterType="Required",
            direction="Output")
        param5.parameterDependencies = [param0.name]
        param5.schema.clone = True

        params = [param0, param1, param2, param3, param4, param5]
        return params

    def isLicensed(self):
        """Set whether the tool is licensed to execute."""
        return license([EXTENSIONS.Spatial])

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

        # define small neighborhood radius
        if parameters[3].value is None:
            parameters[3].value = "150 Meters"

        # default large neighborhood radius
        if parameters[4].value is None:
            parameters[4].value = "1000 Meters"


    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool parameter."""
        validate(parameters)


    @reload_module(__name__)
    def execute(self, parameters, _messages):
        """The source code of the tool."""
        # Setup
        log("setting up project")
        project, active_map = setup()
        map_unit = SPATIAL_UNITS[active_map.mapUnits].to_linear()

        # read in parameters
        log("reading in parameters")
        dem, _ = raster_and_layer(parameters[0].value)
        z_unit = SPATIAL_UNITS[parameters[1].value]
        extent = parameters[2].value
        radius_small = Distance(parameters[3].valueAsText).to_unit(map_unit).length
        radius_large = Distance(parameters[4].valueAsText).to_unit(map_unit).length
        output_file = parameters[5].valueAsText

        # set analysis extent
        if extent:
            arcpy.env.extent = extent

        # add results to map
        log("adding results to map")
        active_map.addDataFromPath(output_file)

        # save project
        log("saving project")
        project.save()
