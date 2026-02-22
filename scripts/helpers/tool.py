# --------------------------------------------------------------------------------
# Name:        License
# Purpose:     This package contains various tools for arcgis toolboxes.
#
# License:     GNU Affero General Public License v3.
#              Full license in LICENSE file, or at <https://www.gnu.org/licenses/>
#              See licensing note for empty_workspace
# --------------------------------------------------------------------------------

import os
import sys
from functools import wraps
from importlib import import_module
from packaging.version import Version
import arcpy

# only needed for spatial analyst, but potential image analyst, ddd or others if
# we end up using them
# https://pro.arcgis.com/en/pro-app/3.3/arcpy/functions/checkextension.htm
def license(licenses=[], version_required=""):
    """Verify the required licenses are installed."""
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


def setup_environment():
    """Setup project environment for analysis and return project and active map."""
    # setup project and active map
    project = arcpy.mp.ArcGISProject("Current")
    active_map = project.activeMap

    # setup arcpy environmental variables
    arcpy.env.overwriteOutput = True
    arcpy.env.scratchWorkspace = arcpy.env.scratchGDB
    if arcpy.env.outputCoordinateSystem is None:
        spatial_reference_name = active_map.spatialReference.name
        arcpy.env.outputCoordinateSystem = arcpy.SpatialReference(spatial_reference_name)

    return project, active_map


# When applied to the execute method of a tool, the reload_module decorator fully
# reloads the module prior to running the tool. This enables us to pick up any code
# changes since it was last run for ease of development.
def reload_module(name, force=True):
    """reload_module reads in the NAME and FORCE arguments and returns the
    actual reload_module function decorator."""

    def reload_module(func):
        """reload_module takes the original execute FUNC and returns a wrapper
        function with additional logic to run prior to either executing FUNC or
        reloading it."""

        @wraps(func) # provide __wrapped__ method on execute to avoid calling decorator again
        def wrapper(self, parameters, messages):
            """wrapper checks whether to load any code changes based off FORCE,
            and either calls the new execute method or the original."""

            if force:
                # delete the module we're executing and re-import it
                class_name = self.__class__.__name__
                for module in list(sys.modules):
                    if name in module:
                        del sys.modules[module]
                out = import_module(name)
                # call the updated execute method without it's decorator
                return out.__dict__[class_name].execute.__wrapped__(self, parameters, messages)
            else:
                # call the original execute method
                return func(self, parameters, messages)
        return wrapper
    return reload_module


def empty_workspace(gdb_path: str, keep: list[str]=[]) -> None:
    """Delete everything in a given workspace except for KEEP paths.

    License:  Modification of work in NRCS Engineering Tools 2.0 (no license present)
              Assumed to fall under this project's license: GNU Affero General Public
              License v3.
    """
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
