"""Per-figure plotting modules for the smart_osse manuscript.

Each module here (e.g. ``fig9_patm_unc``) is meant to be imported into a
notebook, not run as a script: it exposes small ``load_*`` / ``plot_*``
functions that take already-open datasets and return ``ax`` (or ``fig, ax``),
so panels can be built, tweaked, and re-laid-out interactively.
"""
