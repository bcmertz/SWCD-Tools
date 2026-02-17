# -----------------------------------------------------------------------------------
# Name:        Layer Helper
# Purpose:     This package contains various tools for working with arcpy layers.
#
# License:     GNU Affero General Public License v3.
#              Full license in LICENSE file, or at <https://www.gnu.org/licenses/>
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
