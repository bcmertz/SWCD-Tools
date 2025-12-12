# --------------------------------------------------------------------------------
# Name:        Sanitize
# Purpose:     This helper is used in various other tools to sanitize a file path
#
# License:     GNU Affero General Public License v3.
#              Full license in LICENSE file, or at <https://www.gnu.org/licenses/>
# --------------------------------------------------------------------------------

import string

def sanitize(text):
    """return a sanitized file path string"""
    return str(text).translate(str.maketrans('', '', string.punctuation)).replace(" ", "")
