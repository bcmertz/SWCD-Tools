# -*- coding: utf-8 -*-
import os
import sys
import arcpy
from importlib import reload, import_module

scripts = os.path.join(os.path.dirname(__file__), "scripts")
sys.path.append(scripts)

from BufferTools import PointPlots, ShrubClusters
from AnalyzeArea import ContourArea, SlopeArea
from Misc import CollectRasters, ExportLayouts, GeocodeAddress
from LineAnalysis import LocalMinimums
from Hydrology import RunoffPotential, CalculateHydrology, WatershedDelineation, RelativeElevationModel, SubBasinDelineation, CalculateStreamline, LeastAction, TopographicWetness
from Wetlands import PotentialWetlands, BermAnalysis, DamRemoval
from AgAssessment import Delineate, Agland, NonAg, Forest, Process, Export

def my_reloader(name):
    del globals() [name]
    del sys.modules [name]
    globals() [name] = __import__(name)

tools = [SlopeArea,
         ContourArea,
         CollectRasters,
         ExportLayouts,
         LocalMinimums,
         RelativeElevationModel,
         PointPlots,
         ShrubClusters,
         LeastAction,
         RunoffPotential,
         CalculateHydrology,
         WatershedDelineation,
         SubBasinDelineation,
         CalculateStreamline,
         TopographicWetness,
         PotentialWetlands,
         BermAnalysis,
         DamRemoval,
         Delineate,
         Agland,
         NonAg,
         GeocodeAddress,
         Forest,
         Process,
         Export]

class Toolbox(object):
    def __init__(self):
        """Define the toolbox (the name of the toolbox is the name of the
        .pyt file)."""
        self.label = "SWCD Tools"
        self.alias = "SWCD Tools"

        #ls = []
        #for i,j in sys.modules.items():
        #    r,v=i,j
        #    ls.append((r,v))
        #for i in ls:
        #    if i[0] == "AnalyzeArea.SlopeArea":
        #        #raise ValueError(i[1])
        #        reload(i[1])
        #        my_reloader(i[1])
        #import_module(ExportLayouts)
        #reload(ExportLayouts)

        #import_module(SlopeArea)
        ##for t in tools:
         #   import_module(t)
         #   reload(t)

        # List of tool classes associated with this toolbox
        self.tools = tools
