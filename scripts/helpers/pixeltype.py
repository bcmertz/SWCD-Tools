# --------------------------------------------------------------------------------
# Name:        Pixel Type
# Purpose:     This helper returns the string representation of the raster pixel type
#
# License:     GNU Affero General Public License v3.
#              Full license in LICENSE file, or at <https://www.gnu.org/licenses/>
# --------------------------------------------------------------------------------

import arcpy

pixel_types = {
    "U1": "1_BIT",
    "U2": "2_BIT",
    "U4": "4_BIT",
    "S8": "8_BIT_SIGNED",
    "U8": "8_BIT_UNSIGNED",
    "S16": "16_BIT_UNSIGNED",
    "U16": "16_BIT_SIGNED",
    "S32": "32_BIT_UNSIGNED",
    "U32": "32_BIT_SIGNED",
    "F32": "32_BIT_FLOAT",
    "F64": "64_BIT"
}       

def pixel_type(id):
    """return the object ID of a given layer"""
    return pixel_types[id]
