# -*- coding: utf-8 -*-

from src.BufferTools import *
from src.FluvialGeomorphology import *
from src.Hydrology import *
from src.TerrainAnalysis import *
from src.TerrainModification import *
from src.TileDrainage import *
from src.Utilities import *
from src.AgAssessment import *

class Toolbox(object):
    def __init__(self):
        """Define the toolbox (the name of the toolbox is the name of the
        .pyt file)."""
        self.label = "SWCD Tools"
        self.alias = "SWCD Tools"

        tools = [
            DefineParcels,
            Agland,
            NonAg,
            Forest,
            Process,
            Export,
            Restart,
            PointPlots,
            ShrubClusters,
            BufferPotential,
            StreamNetwork,
            LeastAction,
            StreambankDetection,
            StreamElevation,
            GenerateCrossSections,
            PolygonCenterline,
            CalculateEFH2,
            RunoffCurveNumber,
            SubBasinDelineation,
            WatershedDelineation,
            WatershedSize,
            BermAnalysis,
            DamRemoval,
            BurnCulverts,
            StreamPowerIndex,
            LandscapePosition,
            VBET,
            TopographicWetness,
            RelativeElevationModel,
            PotentialWetlands,
            TopographicPositionIndex,
            DecisionTree,
            ImageDifferencingSetup,
            ImageDifferencing,
            ImageDifferencingClouds,
            SlopePolygon,
            ContourPolygon,
            ExportLayouts,
            LocalMinimums,
            GeocodeAddress,
            RemoveUnused,
            CollectRasters,
        ]

        # List of tool classes associated with this toolbox
        self.tools = tools
