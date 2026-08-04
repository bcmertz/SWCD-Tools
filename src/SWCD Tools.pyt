# -*- coding: utf-8 -*-

from AgAssessment import *
from BufferTools import *
from FluvialGeomorphology import *
from Hydrology import *
from TerrainAnalysis import *
from TerrainModification import *
from TileDrainage import *
from Utilities import *

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
            StreamPowerIndex,
            LandscapePosition,
            VBET,
            TopographicWetness,
            ContourTree,
            RelativeElevationModel,
            PotentialWetlands,
            TopographicPositionIndex,
            BermAnalysis,
            DamRemoval,
            BurnCulverts,
            DecisionTree,
            ImageDifferencingSetup,
            ImageDifferencing,
            ImageDifferencingClouds,
            ExportLayouts,
            LocalMinimums,
            GeocodeAddress,
            RemoveUnused,
            CollectRasters,
        ]

        # List of tool classes associated with this toolbox
        self.tools = tools
