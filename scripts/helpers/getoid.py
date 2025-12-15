# --------------------------------------------------------------------------------
# Name:        Get OID
# Purpose:     This helper returns the object ID for a given layer file
#
# License:     GNU Affero General Public License v3.
#              Full license in LICENSE file, or at <https://www.gnu.org/licenses/>
# --------------------------------------------------------------------------------

import arcpy

def get_oid(layer):
    """return the object ID of a given layer"""
    return arcpy.Describe(layer).OIDFieldName
