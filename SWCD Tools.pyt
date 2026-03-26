# -*- coding: utf-8 -*-

from scripts import *

class Toolbox(object):
    def __init__(self):
        """Define the toolbox (the name of the toolbox is the name of the
        .pyt file)."""
        self.label = "SWCD Tools"
        self.alias = "SWCD Tools"

        tools = [
            SlopePolygon,
            ContourPolygon,
            BurnCulverts,
            CollectRasters,
            ExportLayouts,
            StreamNetwork,
            StreamElevation,
            GenerateCrossSections,
            LocalMinimums,
            RelativeElevationModel,
            PointPlots,
            ShrubClusters,
            BufferPotential,
            StreamPowerIndex,
            LeastAction,
            RunoffCurveNumber,
            CalculateEFH2,
            WatershedSize,
            StreambankDetection,
            WatershedDelineation,
            SubBasinDelineation,
            RemoveUnused,
            DecisionTree,
            ImageDifferencingSetup,
            ImageDifferencing,
            ImageDifferencingClouds,
            TopographicWetness,
            PotentialWetlands,
            BermAnalysis,
            DamRemoval,
            DefineParcels,
            Agland,
            NonAg,
            GeocodeAddress,
            Forest,
            Process,
            Export,
            Restart
        ]

        # List of tool classes associated with this toolbox
        self.tools = tools
