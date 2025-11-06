# -*- coding: utf-8 -*-
import os
import sys
import arcpy

sys.path.append(os.path.join(os.path.dirname(__file__), "scripts"))

from BufferTools import PointPlots, ShrubClusters
from AnalyzeArea import ContourArea, SlopeArea
from CollectHistoricalRasters import CollectRasters
from ExportLayouts import ExportLayouts
from LinearAnalysis import LocalMinimums
from REMCalculator import RelativeElevationModel
from StreamCenterlineAdjuster import LeastAction, LeastActionAcc
from WatershedHydrology import RunoffPotential, CalculateHydrology, WatershedDelineation, SubBasinDelineation, CalculateStreamline, StreamElevation, TopographicWetness
from WetlandCalculator import PotentialWetlands, BermAnalysis, DamRemoval
from AgAssessment import Delineate, Agland, NonAg, Forest, Process, Export

tools = [SlopeArea,
         ContourArea,
         CollectRasters,
         ExportLayouts,
         LocalMinimums,
         RelativeElevationModel,
         PointPlots,
         ShrubClusters,
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

class Toolbox:
    def __init__(self):
        """Define the toolbox (the name of the toolbox is the name of the
        .pyt file)."""
        self.label = "SWCD Tools"
        self.alias = "tools"

        # List of tool classes associated with this toolbox
        self.tools = tools
