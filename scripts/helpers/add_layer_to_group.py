# --------------------------------------------------------------------------------
# Name:        Add Layer to Group
# Purpose:     This helper is used in various other tools add a given layer to a
#              group and remove the old layer. It returns the new layer reference
#
# License:     GNU Affero General Public License v3.
#              Full license in LICENSE file, or at <https://www.gnu.org/licenses/>
# --------------------------------------------------------------------------------

def addLayerToGroup(active_map, group, layer, hide=False):
    # add layer to group, remove old layer, return new layer
    active_map.addLayerToGroup(group, layer)
    layer_name = layer.name
    active_map.removeLayer(layer)
    new_layer = active_map.listLayers(layer_name)[0]
    if hide:
        new_layer.visible = False
    return new_layer
