#!/usr/bin/python
# refreshable.py - Refreshable classes for livecoding adventures
# Author: Zach Banks <zbanks@mit.edu>
# License: MIT

import collections
import imp
import inspect
import threading
import time
import traceback

class SafeRefreshMixin(object):
    DEFAULTS = {
        "_refresh_history": lambda : [],
        "_refresh_rev": lambda : 0,
    }
    STATICS = [] # Things to not refreshable
    AUTO_NONE = False # Automatically populate attributes with None

    def __getattr__(self, name):
        # Called when an attribute isn't found (AttributeError)
        # Instantiate the value from DEFAULTS
        if name not in self.DEFAULTS and not self.AUTO_NONE:
            raise AttributeError
        value = self.DEFAULTS.get(name)
        if value and value.__call__:
            value = value()
        self.__setattr__( name, value)
        return value

    def init_defaults(self):
        # Can be called to init all the parameters in DEFAULTS if you don't like surprises
        for key in self.DEFAULTS:
            self.__getattr__(key)

    def pre_refresh(self):
        # Pre-refresh hook
        pass

    def post_refresh(self):
        # Post-refresh hook
        pass

    def refresh(self, NewClass=None):
        # Reload all class variables & methods
        # Record existing version to allow reversions if an error is encountered

        try:
            self.pre_refresh()
        except:
            # It's really bad if the pre_refresh hook fails, but there's a chicken-and-egg problem if it does fail XXX
            traceback.print_exc()
            print "WARNING: Pre-refresh hook failed for module {}. Continuing to refresh...".format(NewClass)

        if NewClass is None:
            # Try to reload the module & new class
            try:
                cls = self.__class__
                module = inspect.getmodule(cls)
                new_module = imp.reload(module) # `module` should also be updated
                NewClass = new_module.__dict__[cls.__name__]
            except:
                traceback.print_exc()
                raise Exception("Unable to reload module. Did not refresh.")

        # Swap out class methods & variables
        history = {}
        try:
            for key, item in NewClass.__dict__.items():
                if key not in NewClass.STATICS:
                    if hasattr(item, '__call__'): # need to re-bind methods first; assumes all methods should be bound. (XXX) 
                        # Re-bind with .__get__
                        print "call", item
                        value = item.__get__(self, NewClass)
                    else:
                        value = item
                    if key in self.__dict__: # hasattr(...) won't work here
                        history[key] = self.__getattribute__(key)
                    self.__setattr__(key, value)
        except:
            traceback.print_exc()
            # Rollback
            self.revert(history=history)
            raise Warning("Unable to refresh module: {}. Reverted.".format(NewClass))

        try:
            self.post_refresh()
        except:
            # We can revert if the post_refresh hook fails. That's solvable
            traceback.print_exc()
            # Rollback
            self.revert(history=history)
            raise Warning("Post-refresh hook failed for module {}. Reverted.".format(NewClass))

        # Success!
        self._refresh_history.append(history)
        self._refresh_rev += 1
        
        return self

    def revert(self, history=None):
        # Any issues? Revert to a previous (hopefully working) version in-place
        if not history:
            try:
                history = self._refresh_history.pop()
            except IndexError:
                return False # Failed to revert

        for key, value in history.items():
            self.__setattr__(key, value)
        return True # Reverted!

    def purge(self):
        # History can build up -- purge if the program is stable
        try:
            del self._refresh_history 
        except NameError:
            pass
        self._refresh_history = []

class SafeRefreshableLoop(threading.Thread, SafeRefreshMixin):
    # If you subclass, make sure you call threading.Thread.__init__

    def stop(self):
        # Actually 'pause'
        self.stopped = True

    def restart(self):
        # Actually 'unpause'
        self.stopped = False

    def step(self):
        raise NotImplementedError

    def run(self):
        self.stopped = False
        while True:
            if self.stopped:
                time.sleep(0.01)
            else:
                # Tolerate errors in step()
                try: 
                    self.step()
                except:
                    traceback.print_exc()
                    if self.revert():
                        print "Error running loop. Reverting to previous version. Trying again..."
                    else:
                        print "Error running loop. No previous version to revert to. Stopping."
                        self.stopped = True


class Test(SafeRefreshableLoop):
    A = 9
    def b(self):
        return self.A
    def step(self):
        print "hello"
        time.sleep(0.5)
