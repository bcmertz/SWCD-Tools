# ------------------------------------------------------------------------------------
# Name:        Empty Geodatabase
# Purpose:     This helper clears the entire geodatabase while keeping specified files
#
# License:     Modification of work in NRCS Engineering Tools 2.0 (no license present)
#              Assumed to fall under this projects license: GNU Affero General Public
#              License v3.
#              Full license in LICENSE file, or at <https://www.gnu.org/licenses/>
# ------------------------------------------------------------------------------------

import os
import arcpy

def empty_workspace(gdb_path: str, keep: list[str]=[]) -> None:
    ''' Delete everything in a given geodatabase.'''
    keep = tuple(keep)
    gdb_contents = []

    for dirpath, dirnames, filenames in arcpy.da.Walk(gdb_path):
        for filename in filenames:
            file = os.path.join(dirpath, filename)
            if file not in keep:
                gdb_contents.append(file)
    for fc in gdb_contents:
        arcpy.management.Delete(fc)

    return
