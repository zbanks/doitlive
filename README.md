\#doitlive
==========

\#doitlive - Tools for livecoding performances in Python.

\#doitlive allows you to "refresh" a class by reloading the source in an *almost*-sane and *almost*-safe way. It also provides facilities for catching and handling common errors that come up with livecoding, such as undeclared variables. 

It works under the philosophy that it's better to have weird behavior than to crash.

Besides livecoding, it can also be used as a tool for debugging or experimenting -- you can tweak algorithms as they run.

Projects
--------

 - https://github.com/zbanks/beetle
 - https://github.com/ervanalb/beat-off/tree/live
 - https://github.com/zbanks/aurora
 - https://github.com/zbanks/peebles 
 - https://github.com/ervanalb/noise 


SafeRefreshableMixin
--------------------

Provides a `.refresh()` method to reload a class

Adding the `SafeRefreshMixin` to a class allows you to "refresh" the class using the `.refresh()` method. This method reloads the python file the class came from and replaces all methods and *class* variables (*not* instance variables!) with the versions from the new file.

The refresh is "safe" because it tries very hard to keep the program running.  On each refresh, a snapshot of the class is saved to form a history. If an error is encountered while performing the refresh, the state is reverted.

In general, you can wrap calls to methods of your refreshed class in a try block that catches all errors and call `.revert()` on failure.

Additionally, `DEFAULTS` and `AUTO_NONE` provide options for handling missing attributes (preventing `AttributeError`s).

### Usage

You can configure the behavior by setting the following class variables:

- `STATICS`  : List of variable names (strings) that are not refreshed.
- `DEFAULTS` : Dictionary of variable names -> values. If an `AttributeError` is caught, and the attribute is in `DEFAULTS`, the attribute is populated from the dictionary. This can be useful if you need to initialize a new state variable.
- `AUTO_NONE`: If `True`, catch `AttributeErrors` and set the attribute to `None` if the attribute is not in `DEFAULTS`.

Additionally, there are the `.pre_refresh()` and `.post_refresh()` hooks which can be overriden.

Once initialized, instances have the following methods:

- `.init_defaults()`: Initialize attributes from the `DEFAULTS` dict.
- `.refresh()`      : Attempt to reload the class from disk.
- `.revert()`       : Revert the changes from the previous `.refresh()`.
- `.purge()`        : Remove the state history. Each call to `.refresh()` takes a snapshot of the class. If you refresh often w/ a big class, this can get large.

### Limitations

- `.refresh()` assumes all methods are bound (take a `self` parameter). As a result, static/class methods (methods declared with `@staticmethod`, or `@classmethod`) will not be refreshed properly. These method names should be added to `STATICS` and they will not be refreshed.

- This framework was designed around the singleton model with one instance of the given refreshed class. It hasn't been extensively tested with multiple instances, and may cause weird behavior around class variables.

- The `__main__` module cannot be reloaded, so the class must exist in an imported module.


SafeRefreshableLoop
-------------------

Run a function in a loop while making the parent class refreshable.

The function `.step()` is called repeatedly while the loop is running.  You can start the loop in one of two ways:

- `.start()`: Run the loop in a thread.
- `.run()`  : (the target of the thread) Run the loop "inline".

The loop can also be paused with `.stop()` and unpaused with `.restart()`.

If you subclass, make sure you call `threading.Thread.__init__`

As with the SafeRefreshMixin, you can set the following class variables:

- `STATICS`  : List of variable names (strings) that are not refreshed.
- `DEFAULTS` : Dictionary of variable names -> values. If an `AttributeError` is caught, and the attribute is in `DEFAULTS`, the attribute is populated from the dictionary. This can be useful if you need to initialize a new state variable.
- `AUTO_NONE`: If `True`, catch `AttributeErrors` and set the attribute to `None` if the attribute is not in `DEFAULTS`.

And call the following methods:

- `.refresh()`: Attempt to reload the class from disk.
- `.revert()` : Revert the changes from the previous `.refresh()`.
- `.purge()`  : Remove the state history. Each call to `.refresh()` takes a snapshot of the class. If you refresh often w/ a big class, this can get large.

Additionally, there are the `.pre_refresh()` and `.post_refresh()` hooks which can be overriden.


Testing
-------

- Test it out by running `python refreshable.py` and modifying `test.py`.
