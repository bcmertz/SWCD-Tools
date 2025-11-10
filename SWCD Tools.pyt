# -*- coding: utf-8 -*-
import os
import sys
import arcpy
from importlib import reload

scripts = os.path.join(os.path.dirname(__file__), "scripts")
sys.path.append(scripts)

from ExportLayouts import ExportLayouts
from BufferTools import PointPlots, ShrubClusters
from AnalyzeArea import ContourArea, SlopeArea
from CollectHistoricalRasters import CollectRasters
from LineAnalysis import LocalMinimums
from REMCalculator import RelativeElevationModel
from StreamCenterlineAdjuster import LeastAction, LeastActionAcc
from Hydrology import RunoffPotential, CalculateHydrology, WatershedDelineation, SubBasinDelineation, CalculateStreamline, StreamElevation, TopographicWetness
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
         LeastActionAcc,
         RunoffPotential,
         CalculateHydrology,
         WatershedDelineation,
         SubBasinDelineation,
         CalculateStreamline,
         StreamElevation,
         TopographicWetness,
         PotentialWetlands,
         BermAnalysis,
         DamRemoval,
         Delineate,
         Agland,
         NonAg,
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
        #    if i[0] == 'AnalyzeArea':
        #        reload(i[1])

        #my_reloader(ExportLayouts.__name__)

        # List of tool classes associated with this toolbox
        self.tools = tools
