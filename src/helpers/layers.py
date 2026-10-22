# -----------------------------------------------------------------------------------
# Name:        Layer Helper
# Purpose:     This package contains various tools for working with arcpy layers.
#
# License:     Contextual Copyleft AI (CCAI) License v1.0.
#              Full license in LICENSE file.
# -----------------------------------------------------------------------------------

import arcpy


def get_oid(layer):
    """Return the object ID of a given layer."""
    return arcpy.Describe(layer).OIDFieldName


def add_layer_to_group(active_map, group, layer, hide=False):
    """Add layer to group, remove old layer, return new layer."""
    active_map.addLayerToGroup(group, layer)
    layer_name = layer.name
    active_map.removeLayer(layer)
    new_layer = active_map.listLayers(layer_name)[0]
    if hide:
        new_layer.visible = False
    return new_layer


def find_layer(active_map, data_source: str) -> arcpy._mp.Layer | None:
    """Find layer from data source if it exists.
    data_source - file path, layer name, or layer long name
    """
    layers = active_map.listLayers()
    for layer in layers:
        if layer.supports("DATASOURCE") and layer.dataSource == data_source:  # noqa: SIM114
            return layer
        elif layer.supports("NAME") and layer.name == data_source:  # noqa: SIM114
            return layer
        elif layer.supports("LONGNAME") and layer.longName == data_source:
            return layer
