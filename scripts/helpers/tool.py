# --------------------------------------------------------------------------------
# Name:        License
# Purpose:     This package contains various tools for arcgis toolboxes.
#
# License:     Contextual Copyleft AI (CCAI) License v1.0.
#              Full license in LICENSE file.
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
                if not os.path.exists("G:\\GIS"):
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

def __empty_workspace(ws_path: str, keep: list[str]=[]) -> None:
    """License:  Modification of work in NRCS Engineering Tools 2.0 (no license present)
                 Assumed to fall under this project's license: GNU Affero General Public
                 License v3."""
    tup = tuple(keep)
    ws_contents = []

    for dirpath, dirnames, filenames in arcpy.da.Walk(ws_path):
        for filename in filenames:
            file = os.path.join(dirpath, filename)
            if file not in tup:
                ws_contents.append(file)
    for fc in ws_contents:
        arcpy.management.Delete(fc)

    return

def empty_workspace(ws_path: str, keep: list[str]=[]) -> None:
    """Delete everything in a given workspace except for KEEP paths."""
    if len(keep) > 0:
        __empty_workspace(ws_path, keep)
    else:
        # get workspace type
        desc = arcpy.Describe(ws_path)
        wst = desc.workspaceType

        # get workspace path info
        ws_folder = os.path.dirname(ws_path)
        ws_name = os.path.basename(ws_path)
        ws_extension = ws_name.split(".")[-1]

        # check if we can completely delete and recreate it or if we need
        # to clear it file by file
        # for now we only delete and recreate folders and file geodatabases
        if wst == "FileSystem":
            # delete workspace
            arcpy.management.Delete(ws_path)

            # recreate workspace
            arcpy.management.CreateFolder(ws_folder, ws_name)

        elif wst == "LocalDatabase":
            if ws_extension == ".gdb":
                # delete workspace
                arcpy.management.Delete(ws_path)

                # recreate workspace
                arcpy.management.CreateFileGDB(ws_folder, ws_name)
            else:
                __empty_workspace(ws_path, keep)

        else:
            __empty_workspace(ws_path, keep)

    return
