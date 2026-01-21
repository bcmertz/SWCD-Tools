# -----------------------------------------------------------------------------------------
# Name:        Reload
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

def reload_module(name, force=False):
    """reload_module provides a function decorator which forces the module of NAME whose execute method it
    decorates to be reloaded. This only occurs when the swcdtools_dev environmental variable is set or the
    FORCE boolean is passed to it."""

    def reload_module(func):
        """this provides __wrapped__ on the underlying decorated function
        we use this later to call our origin function without the decorator
        to avoid infinite recursion"""

        @wraps(func)
        def wrapper(self, parameters, messages):
            if os.environ.get('swcdtools_dev') or force:
                class_name = self.__class__.__name__
                # delete the module we're executing and re-import it
                for module in list(sys.modules):
                    if name in module:
                        del sys.modules[module]
                out = import_module(name)
                # we can't just call return func(self, parameters, messages) since this wont pick
                # up the refreshed modules so we have to get the code from the output module
                return out.__dict__[class_name].execute.__wrapped__(self, parameters, messages)
            else:
                return func(self, parameters, messages)
        return wrapper
    return reload_module
