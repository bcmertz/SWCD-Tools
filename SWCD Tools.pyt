# -*- coding: utf-8 -*-
import os
import sys

scripts = os.path.join(os.path.dirname(__file__), "scripts")
sys.path.append(scripts)

from BufferTools import PointPlots, ShrubClusters, BufferPotential
from RasterTools import ContourPolygon, SlopePolygon, BurnCulverts
from Misc import CollectRasters, ExportLayouts, GeocodeAddress
from LineAnalysis import LocalMinimums
from Hydrology import RunoffCurveNumber, CalculateEFH2, WatershedDelineation, RelativeElevationModel, SubBasinDelineation, LeastAction, TopographicWetness, StreamNetwork, StreamPowerIndex
from TileDrainage import DecisionTree
from Wetlands import PotentialWetlands, BermAnalysis, DamRemoval
from AgAssessment import Delineate, Agland, NonAg, Forest, Process, Export

tools = [SlopePolygon,
         ContourPolygon,
         BurnCulverts,
         CollectRasters,
         ExportLayouts,
         StreamNetwork,
         LocalMinimums,
         RelativeElevationModel,
         PointPlots,
         ShrubClusters,
         BufferPotential,
         StreamPowerIndex,
         LeastAction,
         RunoffCurveNumber,
         CalculateEFH2,
         WatershedDelineation,
         SubBasinDelineation,
         DecisionTree,
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

        # List of tool classes associated with this toolbox
        self.tools = tools
