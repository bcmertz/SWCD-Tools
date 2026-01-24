# -----------------------------------------------------------------------------------------
# Name:        Reload Module
# Purpose:     This package provides the reload_module decorator. When applied to the
#              the execute method of a tool, this decorator fully reloads the module
#              prior to running the tool. This enables us to pick up any code changes
#              since it was last run for ease of development.
#
# License:     GNU Affero General Public License v3.
#              Full license in LICENSE file, or at <https://www.gnu.org/licenses/>
# -----------------------------------------------------------------------------------------

import sys
import os
from importlib import import_module
from functools import wraps

def reload_module(name, force=True):
    """reload_module reads in the NAME and FORCE arguments and returns the 
    actual reload_module function decorator."""
    
    def reload_module(func):
        """reload_module takes the original execute FUNC and returns a wrapper
        function with additional logic to run prior to either executing FUNC or
        reloading it."""

        @wraps(func) # provide __wrapped__ method on execute to avoid calling decorator again
        def wrapper(self, parameters, messages):
            """wrapper checks whether to load any code changes based off FORCE,
            and either calls the new execute method or the original."""

            if force:
                # delete the module we're executing and re-import it
                class_name = self.__class__.__name__
                for module in list(sys.modules):
                    if name in module:
                        del sys.modules[module]
                out = import_module(name)
                # call the updated execute method without it's decorator
                return out.__dict__[class_name].execute.__wrapped__(self, parameters, messages)
            else:
                # call the original execute method
                return func(self, parameters, messages)
        return wrapper
    return reload_module
