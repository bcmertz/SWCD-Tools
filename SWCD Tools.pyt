# -*- coding: utf-8 -*-

from src import AgAssessment, BufferTools, FluvialGeomorphology, Hydrology, TerrainAnalysis, TerrainModification, TileDrainage, Utilities

class Toolbox(object):
    def __init__(self):
        """Define the toolbox (the name of the toolbox is the name of the
        .pyt file)."""
        self.label = "SWCD Tools"
        self.alias = "SWCD Tools"

        tools = [
            AgAssessment.DefineParcels,
            AgAssessment.Agland,
            AgAssessment.NonAg,
            AgAssessment.Forest,
            AgAssessment.Process,
            AgAssessment.Export,
            AgAssessment.Restart,
            BufferTools.PointPlots,
            BufferTools.ShrubClusters,
            BufferTools.BufferPotential,
            FluvialGeomorphology.StreamNetwork,
            FluvialGeomorphology.LeastAction,
            FluvialGeomorphology.StreambankDetection,
            FluvialGeomorphology.StreamElevation,
            FluvialGeomorphology.GenerateCrossSections,
            FluvialGeomorphology.PolygonCenterline,
            Hydrology.CalculateEFH2,
            Hydrology.RunoffCurveNumber,
            Hydrology.SubBasinDelineation,
            Hydrology.WatershedDelineation,
            Hydrology.WatershedSize,
            TerrainModification.BermAnalysis,
            TerrainModification.DamRemoval,
            TerrainModification.BurnCulverts,
            TerrainAnalysis.StreamPowerIndex,
            TerrainAnalysis.LandscapePosition,
            TerrainAnalysis.VBET,
            TerrainAnalysis.TopographicWetness,
            TerrainAnalysis.RelativeElevationModel,
            TerrainAnalysis.PotentialWetlands,
            TerrainAnalysis.TopographicPositionIndex,
            TileDrainage.DecisionTree,
            TileDrainage.ImageDifferencingSetup,
            TileDrainage.ImageDifferencing,
            TileDrainage.ImageDifferencingClouds,
            Utilities.SlopePolygon,
            Utilities.ContourPolygon,
            Utilities.ExportLayouts,
            Utilities.LocalMinimums,
            Utilities.GeocodeAddress,
            Utilities.RemoveUnused,
            Utilities.CollectRasters,
        ]

        # List of tool classes associated with this toolbox
        self.tools = tools
