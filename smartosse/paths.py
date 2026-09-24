"""Site-aware path resolution for smartosse's data-location defaults.

Several functions in this package (``dataset.open_astedataset``, ``osse.NatureRun``,
``utils.get_latitude_masks``, …) need a default location for things like the ASTE
grid or the nature run when the caller doesn't pass one explicitly. Those defaults
used to be hardcoded TACC paths (``/work/08381/goldberg/...``), which meant the
package could not even be *imported and used* off that one filesystem — see
ROADMAP.md §4.

This module resolves such a path in three steps, in order:

1. An ``SMARTOSSE_<KEY>`` environment variable (e.g. ``SMARTOSSE_GRID_DIR``) —
   always wins, so a new machine is a one-line export, never a code change.
2. The active site's entry in ``config/sites.yml`` (``SMARTOSSE_SITE`` picks the
   site directly; otherwise it's detected from the hostname).
3. Nothing — raises `PathNotConfiguredError` with an actionable message rather
   than silently returning `None` or a wrong path. Which tier the caller needs
   is passed through so the error can say so (see each wrapper below).

Deliberately NOT here: any assumption that every key exists for every site. The
``docker`` site in ``sites.yml`` has no ``run_root`` at all, on purpose — that is
what makes Tier 0 (regenerate figures from shipped caches, no model data needed)
actually work. Code that calls `run_root()` unconditionally is code that cannot
run at Tier 0.
"""
import fnmatch
import os
import socket
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover - PyYAML is a base dependency; this is
    yaml = None       # just so `import smartosse.paths` alone never hard-fails.

_ENV_PREFIX = 'SMARTOSSE_'
_SITES_YML = Path(__file__).resolve().parent.parent / 'config' / 'sites.yml'
_DEFAULT_CACHE_DIR = Path(__file__).resolve().parent / 'figures' / 'data'


class PathNotConfiguredError(RuntimeError):
    """Raised when a path is needed but no env var or site config supplies it."""


def _load_sites(sites_yml=_SITES_YML):
    if yaml is None or not sites_yml.exists():
        return {}
    with open(sites_yml) as f:
        data = yaml.safe_load(f) or {}
    return data.get('sites', {})


def detect_site(sites=None, sites_yml=_SITES_YML):
    """Return the active site name, or None if nothing matches.

    ``SMARTOSSE_SITE`` always wins over hostname detection.
    """
    if 'SMARTOSSE_SITE' in os.environ:
        return os.environ['SMARTOSSE_SITE']

    sites = _load_sites(sites_yml) if sites is None else sites
    host = socket.gethostname()
    for name, cfg in sites.items():
        patterns = (cfg or {}).get('detect', {}).get('hostname', [])
        if any(fnmatch.fnmatch(host, pattern) for pattern in patterns):
            return name
    return None


def resolve(key, tier_hint=None, sites_yml=_SITES_YML):
    """Resolve a path by key (e.g. ``'grid_dir'``, ``'run_root'``, ``'nr_dir'``).

    Parameters
    ----------
    key : str
        The ``sites.yml`` field name; also the (lowercased) suffix of the
        environment variable checked first, e.g. ``key='grid_dir'`` checks
        ``SMARTOSSE_GRID_DIR``.
    tier_hint : str, optional
        One line describing what this path is needed for, folded into the
        error message if resolution fails — e.g. ``'Tier 1: regenerating
        caches from run output'``. Purely cosmetic; makes the error useful
        instead of just correct.

    Returns
    -------
    str
        The resolved path.

    Raises
    ------
    PathNotConfiguredError
        If neither an environment variable nor the active site's `sites.yml`
        entry supplies this key.
    """
    env_var = f'{_ENV_PREFIX}{key.upper()}'
    if env_var in os.environ:
        return os.environ[env_var]

    sites = _load_sites(sites_yml)
    site = detect_site(sites)
    site_cfg = sites.get(site) or {}
    if key in site_cfg:
        return site_cfg[key]

    hint = f' ({tier_hint})' if tier_hint else ''
    detected = f'{site!r}' if site else 'none (hostname matched no entry in sites.yml)'
    raise PathNotConfiguredError(
        f"No {key!r} configured{hint}. Detected site: {detected}. Fix by either:\n"
        f"  - exporting {env_var}=/path/to/it, or\n"
        f"  - adding a '{key}:' line under this site in {sites_yml}\n"
        f"See config/sites.yml for the site list and ROADMAP.md §0/§4 for what "
        f"each reproducibility tier needs."
    )


def grid_dir():
    """The ASTE grid directory (``open_astedataset``'s default ``data_dir``)."""
    return resolve('grid_dir', tier_hint='Tier 1/2: reading model output or grid')


def nr_dir():
    """The nature-run directory (``NatureRun``'s default ``nr_dir``)."""
    return resolve('nr_dir', tier_hint='Tier 2: scoring skill against the nature run')


def basin_dir():
    """The basin-mask input directory (``utils``'s latitude/basin helpers)."""
    return resolve('basin_dir', tier_hint='Tier 1/2: basin-restricted gateway masks')


def run_root():
    """The root of the OSSE run-output tree. Deliberately absent at Tier 0 sites."""
    return resolve('run_root', tier_hint='Tier 1: regenerating caches from run output')


def cache_dir():
    """Where the small `.nc` figure caches live.

    Unlike the others, this one has a real fallback instead of raising: the
    caches shipped inside the package itself (``smartosse/figures/data/``),
    which is what makes Tier 0 work with zero configuration.
    """
    try:
        return resolve('cache_dir', tier_hint='Tier 0: rendering figures from caches')
    except PathNotConfiguredError:
        return str(_DEFAULT_CACHE_DIR)
