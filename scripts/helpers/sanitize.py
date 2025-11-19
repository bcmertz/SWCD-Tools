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
import string

def sanitize(text):
    """provide a list of messages to this method"""
    return str(text).translate(str.maketrans('', '', string.punctuation))
