# --------------------------------------------------------------------------------
# Name:        License
# Purpose:     This helper is used in various other tools to verify whether the
#              user has the required GIS license installed
#
# License:     GNU Affero General Public License v3.
#              Full license in LICENSE file, or at <https://www.gnu.org/licenses/>
# --------------------------------------------------------------------------------

import os
import arcpy
from packaging.version import Version

# only needed for spatial analyst, but potential image analyst, ddd or others if
# we end up using them
# https://pro.arcgis.com/en/pro-app/3.3/arcpy/functions/checkextension.htm

def license(licenses=[], version_required=""):
    """verify the required licenses are installed"""
    try:
        if version_required:
            v_installed = arcpy.GetInstallInfo()['Version']
            if Version(v_installed) < Version(version_required):
                return False
        for l in licenses:
            if l == "OSWCD_GIS":
                if not os.path.exists("G:\GIS"):
                    return False
            else:
                status = arcpy.CheckExtension(l)
                if status != "Available":
                    return False
        return True
    except:
        return False
