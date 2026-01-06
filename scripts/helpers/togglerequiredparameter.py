# --------------------------------------------------------------------------------
# Name:        Toggle Tequired Parameter
# Purpose:     This helper is used in various other tools to make an optional
#              parameter required while enabled.
#
# Notes:       This tool expects to run in updatemessages
#
# License:     GNU Affero General Public License v3.
#              Full license in LICENSE file, or at <https://www.gnu.org/licenses/>
# --------------------------------------------------------------------------------

def toggle_required_parameter(toggle, parameter) -> None:
    """Toggle Tequired Parameter
    This takes a TOGGLE parameter and a PARAMETER to act on that gets switched
    between optional and required based off of the TOGGLE boolean parameter.
    """
    # make newly toggled on parameter required
    if not toggle.hasBeenValidated:
        if toggle.value == True:
            if not parameter.value:
                parameter.setIDMessage("ERROR", 530)

    # handle deleted parameter value
    if not parameter.hasBeenValidated and not parameter.value:
        parameter.setIDMessage("ERROR", 530)

    return
