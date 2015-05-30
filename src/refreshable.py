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
    """ Provides a `.refresh()` method to reload a class

    Adding the `SafeRefreshMixin` to a class allows you to "refresh" the class
    using the `.refresh()` method. This method reloads the python file the class
    came from and replaces all methods and *class* variables (*not* instance 
    variables!) with the versions from the new file.

    The refresh is "safe" because it tries very hard to keep the program running.
    On each refresh, a snapshot of the class is saved to form a history. If an
    error is encountered while performing the refresh, the state is reverted.

    In general, you can wrap calls to methods of your refreshed class in a try
    block that catches all errors and call `.revert()` on failure.

    Additionally, `DEFAULTS` and `AUTO_NONE` provide options for handling 
    missing attributes (preventing `AttributeError`s).

    Usage
    -----

    You can configure the behavior by setting the following class variables:

    - `STATICS`  : List of variable names (strings) that are not refreshed.
    - `DEFAULTS` : Dictionary of variable names -> values. If an `AttributeError` is
                   caught, and the attribute is in `DEFAULTS`, the attribute is
                   populated from the dictionary. This can be useful if you need to
                   initialize a new state variable.
    - `AUTO_NONE`: If `True`, catch `AttributeErrors` and set the attribute to `None` 
                   if the attribute is not in `DEFAULTS`.

    Additionally, there are the `.pre_refresh()` and `.post_refresh()` hooks 
    which can be overriden.

    Once initialized, instances have the following methods:

    - `.init_defaults()`: Initialize attributes from the `DEFAULTS` dict.
    - `.refresh()`      : Attempt to reload the class from disk.
    - `.revert()`       : Revert the changes from the previous `.refresh()`.
    - `.purge()`        : Remove the state history. Each call to `.refresh()` takes a
                          snapshot of the class. If you refresh often w/ a big class,
                          this can get large.

    Limitations
    -----------

    - `.refresh()` assumes all methods are bound (take a `self` parameter). As a
      result, static/class methods (methods declared with `@staticmethod`, or 
      `@classmethod`) will not be refreshed properly. These method names should
      be added to `STATICS` and they will not be refreshed.

    - This framework was designed around the singleton model with one instance of
      the given refreshed class. It hasn't been extensively tested with multiple
      instances, and may cause weird behavior around class variables.

    - The `__main__` module cannot be reloaded, so the class must exist in an 
      imported module.
    """
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
        """ Attempt to refresh the class.

        The class's module is reloaded, and all of the methods and *class* (not instance)
        variables are replaced with the new version.

        A snapshot of the class is kept to allow revisions in case of error.
        (See `.revert()`)
        """
        try:
            # Pre-refresh hook.
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
                    # need to re-bind methods first;
                    #XXX: Assumes all methods are bound (i.e. take a `self` parameter)
                    #     This means the class cannot refresh static or class methods.
                    if hasattr(item, '__call__'):
                        # Re-bind with .__get__
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
        """ Revert to a previous snapshot of the class. 

        Usually called when an error is encountered."""
        if not history:
            try:
                history = self._refresh_history.pop()
            except IndexError:
                return False # Failed to revert

        for key, value in history.items():
            self.__setattr__(key, value)
        return True # Reverted!

    def purge(self):
        """ Remove all of the pre-refresh snapshots from the history."""
        try:
            del self._refresh_history 
        except NameError:
            pass
        self._refresh_history = []

class SafeRefreshableLoop(threading.Thread, SafeRefreshMixin):
    """ Run a function in a loop while making the parent class refreshable.

    The function `.step()` is called repeatedly while the loop is running.
    You can start the loop in one of two ways:
    
    - `.start()`: Run the loop in a thread.
    - `.run()`  : (the target of the thread) Run the loop "inline".

    The loop can also be paused with `.stop()` and unpaused with `.restart()`.

    If you subclass, make sure you call threading.Thread.__init__
    
    As with the SafeRefreshMixin, you can set the following class variables:

    - `STATICS`  : List of variable names (strings) that are not refreshed.
    - `DEFAULTS` : Dictionary of variable names -> values. If an `AttributeError` is
                   caught, and the attribute is in `DEFAULTS`, the attribute is
                   populated from the dictionary. This can be useful if you need to
                   initialize a new state variable.
    - `AUTO_NONE`: If `True`, catch `AttributeErrors` and set the attribute to `None` 
                   if the attribute is not in `DEFAULTS`.

    And call the following methods:

    - `.refresh()`: Attempt to reload the class from disk.
    - `.revert()` : Revert the changes from the previous `.refresh()`.
    - `.purge()`  : Remove the state history. Each call to `.refresh()` takes a
                    snapshot of the class. If you refresh often w/ a big class,
                    this can get large.

    Additionally, there are the `.pre_refresh()` and `.post_refresh()` hooks 
    which can be overriden.
    """

    daemon = True

    def stop(self):
        """ Pauses the refresh loop until `restart` is called. """
        self.stopped = True

    def restart(self):
        """ Restarts the refresh loop after `stop` was called."""
        self.stopped = False

    def step(self):
        """ Override this method. This is called repeatedly in a loop."""
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
                except KeyboardInterrupt:
                    print "Recieved KeyboardInterrupt. Stopping loop."
                    self.stopped = True
                    break
                except:
                    traceback.print_exc()
                    if self.revert():
                        print "Error running loop. Reverting to previous version. Trying again..."
                    else:
                        print "Error running loop. No previous version to revert to. Stopping."
                        self.stopped = True
