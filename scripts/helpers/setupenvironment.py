# --------------------------------------------------------------------------------
# Name:        Setup Environment
# Purpose:     This helper is used in various other tools to help setup
#              environmental variables and return the active project and map.
#
# License:     GNU Affero General Public License v3.
#              Full license in LICENSE file, or at <https://www.gnu.org/licenses/>
# --------------------------------------------------------------------------------

import arcpy

def setup_environment():
    """Setup environment for analysis"""
    # setup project and active map
    project = arcpy.mp.ArcGISProject("Current")
    active_map = project.activeMap

    # setup arcpy environmental variables
    # TODO: consider setting output coordinate system to map coordinate system
    arcpy.env.overwriteOutput = True
    if arcpy.env.outputCoordinateSystem == None:
        arcpy.env.outputCoordinateSystem = arcpy.SpatialReference("WGS 1984 UTM Zone 18N")

    return project, active_map
