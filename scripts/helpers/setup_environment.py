# --------------------------------------------------------------------------------
# Name:        Agland
# Purpose:     This tool categorizes a piece of land in an ag assessment as
#              agricultural land for further processing
#
# Author:      Reya Mertz
#
# Created:     11/2025
# Modified:    11/2025
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
