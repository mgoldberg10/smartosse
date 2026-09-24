"""SMART cable OSSE analysis utilities.

Names from the submodules below are resolved lazily, so importing a single
module costs only that module's dependencies::

    from smartosse.bp import BPReader     # numpy/xarray/xmitgcm only
    from smartosse import read_aste_bin   # imports smartosse.utils on demand
    import smartosse; smartosse.spna(...) # imports smartosse.plot on demand

This matters because the plotting modules pull in cartopy, matplotlib,
cmocean and pyresample, while the data-extraction path (``bp``, ``utils``,
``dataset``) needs none of them. Eagerly star-importing everything -- as this
module used to -- made a bare ``import smartosse.bp`` drag in the whole
plotting stack, which is why CI could not install a light dependency set and
why the extraction step could not run on a machine without cartopy.

``from smartosse import *`` still works and still pulls everything in, so
notebooks are unaffected.
"""

# Search order for lazy attribute lookup. Two constraints:
#
#   * ``dataset`` precedes ``utils``/``bp``/``osse`` so that its aste1080-aware
#     ``get_extra_metadata`` override wins. That is the only name in this
#     package that resolves to different objects in different modules, and
#     under the previous star-import order ``dataset`` won it too -- keep it
#     that way.
#   * ``osse`` and ``plot`` come last so their heavy dependencies
#     (ecco_v4_py; cartopy/matplotlib/cmocean/pyresample) are imported only
#     when a name genuinely lives there.
_SUBMODULES = ('dataset', 'utils', 'cmaps', 'bp', 'osse', 'plot')


def __getattr__(name):
    """PEP 562 lazy attribute lookup across the submodules above."""
    import importlib

    if name == '__all__':
        # Star-import: the caller wants everything, so eagerly load it all.
        names = set()
        for mod_name in _SUBMODULES:
            mod = importlib.import_module(f'.{mod_name}', __name__)
            names |= {n for n in getattr(mod, '__all__', dir(mod))
                      if not n.startswith('_')}
        globals()['__all__'] = sorted(names)
        return globals()['__all__']

    for mod_name in _SUBMODULES:
        mod = importlib.import_module(f'.{mod_name}', __name__)
        if hasattr(mod, name):
            value = getattr(mod, name)
            globals()[name] = value   # cache, so this runs once per name
            return value

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__():
    return sorted(set(globals()) | set(_SUBMODULES) | set(__getattr__('__all__')))
