# -----------------------------------------------------------------------------------------
# Name:        Reload
# Purpose:     This package provides the reload_module decorator for the execute method of
#              a tool. This decorator reloads a module when it is ran to pick up any code
#              changes since it was last ran.
#
# License:     GNU Affero General Public License v3.
#              Full license in LICENSE file, or at <https://www.gnu.org/licenses/>
# -----------------------------------------------------------------------------------------

import sys
import os
from importlib import import_module
from functools import wraps

def reload_module(name):
    def reload_module(func):
        # this provides __wrapped__ on the underlying decorated function
        # we use this later to call our origin function without the decorator
        # to avoid infinite recursion
        @wraps(func)
        def wrapper(self, parameters, messages):
            if os.environ.get('swcdtools_dev'):
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
