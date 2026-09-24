"""Fig. 6 -- partial-cable $p_b$ and barotropic-velocity skill maps
(``fig:bp_uvbt_skill``).

Port of ``smart_cables/osse/barotropic_vel_skill_pfe.ipynb`` (cells 3-5, the
cell that writes ``regions_skill_bp_and_uvbt_square_iter20_vmax1.png``) onto
this package's per-figure module conventions.

Eight panels, four partial-cable OSSEs x two quantities. Every panel is the
same skill score (``osse._compute_skill``)::

    S = 1 - rms(x^20 - x^NR) / rms(x^0 - x^NR)

over January 2012 with time means removed, drawn on the package's standard
white-centred ``cmocean curl_r`` map over ``[-1, 1]`` with 12 levels. The
white markers are the assimilated cable's sensor locations, taken from that
run's own `BPReader` sensor mask.

Rows/columns are the four segments of the SPNA cable, in the notebook's order:

    ``newfoundland`` (Nfl_cable), ``labsea`` (LS_cable),
    ``subgyre`` (SPG_cable), ``northsea`` (NS_cable)

Two orientations, same panels and same letters
----------------------------------------------
* ``orientation='vertical'`` -- the notebook's own 4x2: one row per region,
  left column $p_b$, right column barotropic velocity. Letters run down each
  column, so $p_b$ is (a)-(d) and velocity is (e)-(h).
* ``orientation='horizontal'`` -- 2x4: **top row $p_b$, bottom row velocity**,
  one column per region. The letter of a given (region, quantity) panel is
  unchanged, so the caption's "(a-d) $p_b$ and (e-h) ... barotropic velocity"
  reads correctly either way.

Which velocity component?
-------------------------
`VEL_STR` selects it, and the notebook's value -- ``'U'``, the **zonal**
component -- is kept as the default so this module reproduces
``regions_skill_bp_and_uvbt_square_iter20_vmax1.png`` exactly.

Note that ``sections/results.tex``'s caption for this figure says panels (e-h)
are the *meridional* component ($V_{bt}$), with the zonal one "not shown" --
it was written against the older ``..._iter10_vmax0.6.png`` render that is
still the one ``\\includegraphics``'d there. Pass ``--vel V`` (or set
`VEL_STR`) to build the figure the current caption describes; nothing else
changes. The two components' skill patterns are described in the text as
quantitatively comparable, and both are cached by `build_cache`, so switching
is a re-plot, not a recompute.

The other departure from the notebook's saved PNG is the iteration and colour
range: this reproduces the ``iter20_vmax1`` render (`ITERNUMS`, `VMAX`), not
the ``iter10_vmax0.6`` one currently in the manuscript.

Mechanical departures from the notebook, none of which change the panels
-----------------------------------------------------------------------
* **One `llc_map` per figure instead of one per panel.** ``osse.plot_skill``
  goes through ``ds.plotpc(...)``, which builds a fresh `llc_map` (a KD-tree
  over the full ASTE swath) on every one of the eight calls. This module
  builds it once and calls it directly -- same regrid, same ``contourf``,
  same colormap and levels. Same pattern as `fig5_misfit_rmse_skill`.
* **The panel fields are cached to netCDF** (`CACHE`), so re-laying-out the
  figure never re-reads ``/scratch``. Building the cache is the expensive
  step: the barotropic velocity comes from ``trsp_3d_set1``, i.e. a month of
  daily 3-D transports for two iterations in each of four run directories.
* **The colorbar reuses the last panel's mappable.** The notebook drew a
  ninth, throwaway ``plot_skill`` call purely to get something to hand to
  ``fig.colorbar``; it is constructed identically to the panels'.
* **`contourf` fills are rasterized** (`rasterize=True`), per-collection
  because matplotlib 3.4's ``ContourSet`` is not an Artist and a
  ``rasterized=`` kwarg passed to ``contourf`` is silently dropped. No effect
  on the PNG; it takes the PDF from ~5.9 MB to well under 1 MB. Pass
  ``--no-rasterize`` for fully vector fills. Rasterizing on matplotlib < 3.5
  *requires* ``figs_utils.patch_pdf_indexed_image_bitdepth()`` (called in
  ``__main__``) or the PDF's palette-encoded panels are undecodable -- see
  that helper's docstring.

The figure is saved on an **opaque white** background, not with the notebook's
``transparent=True``: the Natural Earth land polygons and the regridded ASTE
field leave alpha=0 gaps along the coastlines, which any viewer compositing
onto a dark ground turns into black blobs behind the grey land. See the
2026-08-14 entry in ``STATUS.md``.

A known issue in the underlying quantity (not introduced here):
``osse.ForecastModel._load_fm_bt`` computes ``UVELMASS * hFacW * dyG * drF``,
but ``UVELMASS`` is already ``u*hFacW``, so partial bottom cells are squared.
That affects the velocity panels of this figure. See ``STATUS.md``.

How to run
----------
::

    module load texlive
    conda activate /work2/08381/goldberg/ls6/miniforge3/envs/esmpy_3.10
    cd /work2/08381/goldberg/ls6/smartosse
    python -m smartosse.figures.fig6_regions_skill_bp_uvbt
    python -m smartosse.figures.fig6_regions_skill_bp_uvbt --rebuild   # redo cache

Writes ``output/fig6_regions_skill_bp_uvbt.{png,pdf}`` (the notebook's 4x2),
``output/fig6_regions_skill_bp_uvbt_horizontal.{png,pdf}`` (2x4), and the
cache ``data/fig6_regions_skill_bp_uvbt.nc``.
"""
import argparse
import os

import numpy as np
import pandas as pd
import xarray as xr
import cmocean

from ..cmaps import Colormaps
from ..dataset import open_astedataset
from ..osse import NatureRun, MultiOSSE
from ..plot import llc_map, spna, gl_label_defaults, retain_only_perimiter_gl_labels
from .figs_utils import add_panel_label, add_cable_scatter

# =============================================================================
# Data locations / run config
# =============================================================================

# The four partial-cable OSSEs, January 2012, reanalysis-spread p_atm
# uncertainty -- the notebook's `run_dir_root`.
RUN_DIR_ROOT = ('/scratch/08381/goldberg/aste_270x450x180/osses/'
                'runc68v_froman_partialcables_jraspread/')

# Barotropic-velocity nature run (LLC4320, already depth-integrated).
# The p_b nature run uses `NatureRun`'s own default nr_dir.
NR_BT_DIR = '/work2/08381/goldberg/ls6/llc4320/global/barotropic_velocity/201201/'

# The notebook overrides each run's own iter0000/ grid with the standalone one.
GRID_DIR = '/work2/08381/goldberg/ls6/aste_270x450x180/GRID_noblank_real4/'

# First guess and final iteration. Iteration 0 enters only as the skill
# score's denominator. The manuscript's current (older) render used 10.
ITERNUMS = (0, 20)

MONTH = '201201'

# Notebook order -- this is the row order (vertical) / column order
# (horizontal) of the panels.
REGIONS = ('newfoundland', 'labsea', 'subgyre', 'northsea')

# Manuscript names (models.tex Table 1), for `show_titles=True` only.
REGION_LABELS = {'newfoundland': 'Nfl_cable', 'labsea': 'LS_cable',
                 'subgyre': 'SPG_cable', 'northsea': 'NS_cable'}

# Velocity component in the second row/column: 'U' (zonal, the notebook's and
# this module's default) or 'V' (meridional, what results.tex's caption
# currently describes). See the module docstring.
VEL_STR = 'U'

DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
OUT_DIR = os.path.join(os.path.dirname(__file__), 'output')
CACHE = os.path.join(DATA_DIR, 'fig6_regions_skill_bp_uvbt.nc')
FIG_NAME = 'fig6_regions_skill_bp_uvbt'

# =============================================================================
# Panel styling -- all of this is the notebook's, unchanged
# =============================================================================

VMAX = 1.0
NLEV = 12

LETTERS = 'abcdefgh'

PANEL_LABEL_FONTSIZE = 40
PANEL_LABEL_XY = (0.02, 0.95)

# `osse._plot_skill`'s scatter defaults, which the notebook also passes
# explicitly for the velocity panels (whose FM has no BPReader).
CABLE_SCATTER_KWARGS = dict(s=10, edgecolor='k', facecolor='w')

GL_LABEL_FONTSIZE = 30
GL_XPADDING = 20

CBAR_TICK_KWARGS = dict(labelsize=30, length=10, width=2)
CBAR_NTICKS = 5

# Per-orientation layout. `cbar_rect` is a figure-fraction
# [left, bottom, width, height] for the shared horizontal colorbar; the
# vertical one is the notebook's.
LAYOUTS = {
    'vertical':   dict(nrows=4, ncols=2,
                       cbar_rect=[0.113, 0.06, 0.8, 0.024],
                       subplots_adjust=dict(wspace=-.35)),
    # The 2x4 needs its own bottom margin: with only two rows the panels sit
    # much closer to the bottom of the figure than in the 4x2, and the
    # notebook's colorbar y would land on top of the longitude labels.
    'horizontal': dict(nrows=2, ncols=4,
                       cbar_rect=[0.27, 0.07, 0.46, 0.026],
                       subplots_adjust=dict(wspace=-.35, hspace=.05, bottom=.18)),
}

TITLE_FONTSIZE = 30


# =============================================================================
# Loaders
# =============================================================================

def month_datetimes(month=MONTH):
    """The FM's daily record timestamps, 2012-01-01 .. 2012-01-31 (31 days)."""
    start = pd.to_datetime(month, format='%Y%m')
    return pd.date_range(start=start, end=start + pd.offsets.MonthEnd(1), freq='D')


def region_run_dir(region, run_dir_root=RUN_DIR_ROOT, month=MONTH):
    """``<root>/<month>/<region>/`` -- the notebook's per-region run_dir."""
    return f'{run_dir_root}/{month}/{region}/'


def cable_sensor_lonlat(osse_bp):
    """Cable sensor lon/lat from the run's own `BPReader` sensor mask.

    The notebook's ``osse_bp.grid_ds[coord].isel(osse_bp.fm.bpr.sensor_args)``.
    `get_sensors` is called defensively in case ``get_cost`` (which normally
    populates ``sensor_args`` during `BPReader.__post_init__`) was skipped
    because ``bpdifanom_raw`` was missing.
    """
    bpr = osse_bp.fm.bpr
    if not getattr(bpr, 'sensor_args', None):
        bpr.get_sensors()
    lons, lats = (osse_bp.grid_ds[coord].isel(bpr.sensor_args).values
                  for coord in ('XC', 'YC'))
    return np.asarray(lons), np.asarray(lats)


def build_region_skills(region, nr_bp, nr_bt, grid_dir=GRID_DIR,
                        iternums=ITERNUMS, datetimes=None,
                        run_dir_root=RUN_DIR_ROOT, month=MONTH):
    """One region's three panel-relevant fields: p_b skill, U_bt skill, V_bt
    skill, plus the cable's sensor lon/lat.

    Both velocity components are computed because the expensive part -- the
    ``trsp_3d_set1`` read and the depth integral in
    ``ForecastModel._load_fm_bt`` -- is shared between them: `toggle_uv` just
    swaps which of the already-loaded ``fldUV`` pair the skill is taken over.
    That makes `VEL_STR` a plotting choice rather than a recompute.
    """
    datetimes = month_datetimes(month) if datetimes is None else datetimes
    run_dir = region_run_dir(region, run_dir_root=run_dir_root, month=month)

    print(f'[{region}] loading bp...', flush=True)
    multi_bp = MultiOSSE(nr_bp)
    multi_bp.add_forecast_model(run_dir, iternums=list(iternums),
                                datetimes=datetimes, fld_type='bp',
                                grid_dir=grid_dir)
    osse_bp = multi_bp.comparisons[run_dir]

    print(f'[{region}] loading bt...', flush=True)
    multi_bt = MultiOSSE(nr_bt)
    multi_bt.add_forecast_model(run_dir, iternums=list(iternums),
                                datetimes=datetimes, fld_type='bt',
                                grid_dir=grid_dir)
    osse_bt = multi_bt.comparisons[run_dir]

    bp_skill = osse_bp.fld_skill
    osse_bt.toggle_uv(vel_str='U')
    u_skill = osse_bt.fld_skill
    osse_bt.toggle_uv(vel_str='V')
    v_skill = osse_bt.fld_skill

    lons, lats = cable_sensor_lonlat(osse_bp)
    print(f'[{region}] {len(lons)} sensors; '
          f'mean skill bp={float(bp_skill.mean()):+.4f} '
          f'U_bt={float(u_skill.mean()):+.4f} '
          f'V_bt={float(v_skill.mean()):+.4f}', flush=True)

    return dict(bp=bp_skill, U=u_skill, V=v_skill, lon=lons, lat=lats)


def build_cache(out_path=CACHE, regions=REGIONS, run_dir_root=RUN_DIR_ROOT,
                grid_dir=GRID_DIR, iternums=ITERNUMS, month=MONTH):
    """Compute all eight (well, twelve -- both velocity components) skill maps
    and the four cables' sensor locations once, and cache.

    Returns a Dataset with ``bp_skill``/``U_bt_skill``/``V_bt_skill`` on
    ``(region, tile, j, i)`` and ``cable_lon``/``cable_lat`` on
    ``(region, sensor)``, NaN-padded to the longest cable.
    """
    datetimes = month_datetimes(month)

    # One NatureRun each, shared across the four regions (the notebook's
    # single `MultiOSSE` per field type does the same) -- these are the only
    # objects here worth not re-reading per region.
    nr_bp = NatureRun(fld_type='bp')
    nr_bt = NatureRun(nr_dir=NR_BT_DIR, fld_type='bt')

    per_region = {}
    for region in regions:
        per_region[region] = build_region_skills(
            region, nr_bp, nr_bt, grid_dir=grid_dir, iternums=iternums,
            datetimes=datetimes, run_dir_root=run_dir_root, month=month)

    n_sensor = max(len(per_region[r]['lon']) for r in regions)
    lon = np.full((len(regions), n_sensor), np.nan)
    lat = np.full((len(regions), n_sensor), np.nan)
    for ir, region in enumerate(regions):
        n = len(per_region[region]['lon'])
        lon[ir, :n] = per_region[region]['lon']
        lat[ir, :n] = per_region[region]['lat']

    def _stack(key):
        das = [per_region[r][key].reset_coords(drop=True) for r in regions]
        return xr.concat(das, dim='region')

    cache = xr.Dataset(
        dict(bp_skill=_stack('bp'),
             U_bt_skill=_stack('U'),
             V_bt_skill=_stack('V'),
             cable_lon=(('region', 'sensor'), lon),
             cable_lat=(('region', 'sensor'), lat)),
        coords=dict(region=list(regions)),
    )
    cache.attrs.update(
        note=('skill = 1 - rms(x^N - x^NR)/rms(x^0 - x^NR) over the month, '
              'time means removed (smartosse.osse._compute_skill); '
              'U_bt/V_bt are the true-E/N rotated depth-integrated transports '
              'from ForecastModel._load_fm_bt'),
        run_dir_root=run_dir_root,
        grid_dir=grid_dir,
        nr_bt_dir=NR_BT_DIR,
        iternums=str(list(iternums)),
        month=month,
        n_sensors=str([int(np.isfinite(lon[i]).sum()) for i in range(len(regions))]),
    )
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    cache.to_netcdf(out_path)
    print('wrote', out_path, flush=True)
    return cache


# =============================================================================
# Plot pieces
# =============================================================================

def skill_cmap(nlev=NLEV):
    """The package's standard white-centred ``cmocean curl_r`` skill map --
    the same construction as ``osse._plot_skill``, `fig5_misfit_rmse_skill`'s
    panel (c) and `si_skill_over_optim`, so those panels sit next to these."""
    return Colormaps(nlev).custom_div_cmap(template_cmap=cmocean.cm.curl_r)


def make_gl_label_args(fontsize=GL_LABEL_FONTSIZE):
    """The notebook's gridline-label config: left and bottom labels only,
    latitudes unrotated, both nudged off the frame."""
    args = gl_label_defaults()
    args['top'] = {'hide': True, 'rotate': True, 'pad': 0.0}
    args['right'] = {'hide': True, 'rotate': True, 'pad': 0.0}
    args['left'] = {'hide': False, 'rotate': False, 'pad': 0.05}
    args['bottom'] = dict(args['bottom'], pad=0.15)
    args['fontsize'] = fontsize
    return args


def style_gridliners(gl_list, nrows, ncols, xpadding=GL_XPADDING):
    """The notebook's post-`spna` pass over the Gridliner objects, written
    against the grid shape rather than its hard-coded 4x2 indices.

    Redundant with `make_gl_label_args` for the top/right hiding
    (`process_gridline_labels` has already set those artists invisible), but
    ``top_labels``/``right_labels`` also stop Cartopy re-creating them on a
    later draw, and ``xlabel_style``/``xpadding`` are Gridliner-level knobs
    `process_gridline_labels` doesn't touch.

    `gl_list` is in ``axes.ravel()`` (row-major) order.
    """
    for ig, gl in enumerate(gl_list):
        gl.right_labels = False
        gl.top_labels = False
        if ig % ncols != 0:
            gl.left_labels = False
        if ig < (nrows - 1) * ncols:
            gl.bottom_labels = False
        else:
            gl.xlabel_style = {'rotation': 0}
            gl.xpadding = xpadding
    return gl_list


def draw_panel(ax, lm, field, cmap, vmax=VMAX, nlev=NLEV, rasterize=True):
    """Filled-contour one skill panel and return the mappable.

    Calls the prebuilt `llc_map` directly rather than
    ``osse.plot_skill``/``ds.plotpc(...)``, which would build a new one per
    panel; the draw itself is identical (``plot_type='contourf'`` is
    `llc_map.__call__`'s default and it sets ``extend='both'`` itself).
    """
    _, _, p = lm(field, ax=ax,
                 plot_type='contourf',
                 cmap=cmap,
                 vmin=-vmax, vmax=vmax,
                 levels=np.linspace(-vmax, vmax, nlev),
                 show_cbar=False)
    if rasterize:
        # Per-collection: matplotlib 3.4's ContourSet is not an Artist, so a
        # `rasterized=` kwarg handed to contourf is silently dropped.
        for coll in p.collections:
            coll.set_rasterized(True)
    return p


def add_shared_colorbar(fig, mappable, rect, vmax=VMAX, nticks=CBAR_NTICKS):
    """The notebook's one shared horizontal colorbar in a manually placed
    axes, with ``[-vmax .. vmax]`` ticks at one decimal place."""
    cb = fig.colorbar(mappable, cax=fig.add_axes(rect),
                      orientation='horizontal', extend='both')
    ticks = np.linspace(-vmax, vmax, nticks)
    cb.set_ticks(ticks)
    cb.set_ticklabels([f'{t:.1f}' for t in ticks])
    cb.ax.tick_params(**CBAR_TICK_KWARGS)
    return cb


def panel_position(orientation, iregion, iquantity):
    """``(row, col)`` of the (region, quantity) panel, where ``iquantity`` is
    0 for $p_b$ and 1 for the barotropic velocity.

    vertical   -- one row per region, p_b left  / velocity right (the notebook)
    horizontal -- one column per region, p_b top / velocity bottom
    """
    if orientation == 'vertical':
        return iregion, iquantity
    return iquantity, iregion


def panel_letter(iregion, iquantity):
    """(a)-(d) for the four $p_b$ panels, (e)-(h) for the four velocity
    panels -- identical in both orientations, so the caption's
    "(a-d) $p_b$ and (e-h) ... barotropic velocity" holds either way."""
    return LETTERS[iquantity * len(REGIONS) + iregion]


# =============================================================================
# Assembly
# =============================================================================

def make_fig6(cache, orientation='vertical', vel_str=VEL_STR, ds=None, lm=None,
              vmax=VMAX, nlev=NLEV, show_titles=False, rasterize=True,
              figsize=None, verbose=True):
    """Assemble the eight-panel figure in either orientation.

    `cache` is `build_cache`'s Dataset. `ds` (the ASTE grid) and `lm` (the
    `llc_map` regridder) may be passed in to avoid rebuilding them when
    iterating on layout from a notebook, or when rendering both orientations
    back to back.

    Returns
    -------
    fig, axes
        `axes` has the layout's own ``(nrows, ncols)`` shape.
    """
    if orientation not in LAYOUTS:
        raise ValueError(f"orientation must be one of {sorted(LAYOUTS)}; "
                         f"received {orientation!r}")
    layout = LAYOUTS[orientation]
    nrows, ncols = layout['nrows'], layout['ncols']

    if ds is None:
        ds = open_astedataset(GRID_DIR, grid_dir=GRID_DIR, iters=None)
    if lm is None:
        lm = llc_map(ds)

    spna_kwargs = {} if figsize is None else dict(figsize=figsize)
    fig, axes, gl_list = spna(nrows, ncols, return_gl=True,
                              gl_label_args=make_gl_label_args(),
                              **spna_kwargs)
    style_gridliners(gl_list, nrows, ncols)

    cmap = skill_cmap(nlev)
    regions = [str(r) for r in cache['region'].values]
    fields = (cache['bp_skill'], cache[f'{vel_str}_bt_skill'])
    quantity_labels = (r'$p_b$',
                       rf'${vel_str}_{{bt}}$')

    p = None
    for iregion, region in enumerate(regions):
        lons = cache['cable_lon'].isel(region=iregion).values
        lats = cache['cable_lat'].isel(region=iregion).values
        finite = np.isfinite(lons)      # cables are NaN-padded to a common length
        lons, lats = lons[finite], lats[finite]

        for iquantity, field in enumerate(fields):
            row, col = panel_position(orientation, iregion, iquantity)
            ax = axes[row, col]

            p = draw_panel(ax, lm, field.isel(region=iregion), cmap,
                           vmax=vmax, nlev=nlev, rasterize=rasterize)
            add_cable_scatter(ax, lons, lats, **CABLE_SCATTER_KWARGS)
            add_panel_label(ax, panel_letter(iregion, iquantity),
                            fontsize=PANEL_LABEL_FONTSIZE,
                            x=PANEL_LABEL_XY[0], y=PANEL_LABEL_XY[1])

            # Titles are off in the published figure (the caption carries the
            # region/quantity mapping); `show_titles=True` is a build-time aid.
            if show_titles:
                ax.set_title(f'{quantity_labels[iquantity]} '
                             f'{REGION_LABELS.get(region, region)}',
                             fontsize=TITLE_FONTSIZE, pad=10)
            else:
                ax.set_title('')

    # Interior latitude/longitude labels off. The package's general version of
    # the notebook's hand-written "hide 'N' on odd panels, 'W' on all but the
    # last row" loops; needs a draw first to populate `gl._labels`.
    fig.canvas.draw()
    retain_only_perimiter_gl_labels(axes, gl_list)

    add_shared_colorbar(fig, p, layout['cbar_rect'], vmax=vmax)
    fig.subplots_adjust(**layout['subplots_adjust'])

    if verbose:
        for iquantity, (name, field) in enumerate(
                zip(('p_b', f'{vel_str}_bt'), fields)):
            for iregion, region in enumerate(regions):
                da = field.isel(region=iregion)
                frac = float((np.abs(da) > vmax).sum() / np.isfinite(da).sum())
                print(f'[fig] ({panel_letter(iregion, iquantity)}) {name:>6s} '
                      f'{region:<13s} mean={float(da.mean()):+.4f} '
                      f'{100 * frac:.1f}% beyond |{vmax}|', flush=True)

    return fig, axes


def save_fig(fig, name, out_dir=OUT_DIR, exts=('png', 'pdf')):
    """Save on an **opaque white** background, not ``transparent=True``.

    The land feature and the regridded field don't tile the map exactly, so a
    transparent save leaves alpha=0 pinholes and blobs along every coastline;
    any viewer that composites onto a dark ground (pdflatex, Acrobat's dark
    mode) renders those as black smudges behind the grey land. See STATUS.md.
    """
    os.makedirs(out_dir, exist_ok=True)
    for ext in exts:
        fig.savefig(os.path.join(out_dir, f'{name}.{ext}'), dpi=300,
                    bbox_inches='tight', facecolor='white', edgecolor='none')
    print(f'wrote {name}.{{{",".join(exts)}}} to {out_dir}', flush=True)


# =============================================================================
if __name__ == '__main__':
    ap = argparse.ArgumentParser(
        description='Fig. 6: partial-cable p_b and barotropic-velocity skill')
    ap.add_argument('--vel', choices=('U', 'V'), default=VEL_STR,
                    help="barotropic velocity component in panels (e)-(h); "
                         "'U' (default) reproduces the notebook, 'V' is what "
                         "results.tex's caption currently describes")
    ap.add_argument('--orientation', choices=('vertical', 'horizontal', 'both'),
                    default='both', help='which layout(s) to render')
    ap.add_argument('--vmax', type=float, default=VMAX)
    ap.add_argument('--titles', action='store_true',
                    help='draw per-panel region/quantity titles (off in the manuscript)')
    ap.add_argument('--no-rasterize', action='store_true',
                    help='fully vector contourf fills (much larger PDF)')
    ap.add_argument('--rebuild', action='store_true', help='recompute the cache')
    ap.add_argument('--out', default=CACHE)
    args = ap.parse_args()

    from .figs_utils import (use_latex_times, use_embedded_pdf_fonts,
                             patch_pdf_indexed_image_bitdepth)

    use_latex_times()
    use_embedded_pdf_fonts()
    # Required whenever this module rasterizes (the default) on matplotlib
    # < 3.5, or the PDF's palette-encoded panels are unreadable.
    patch_pdf_indexed_image_bitdepth()

    if args.rebuild or not os.path.exists(args.out):
        cache = build_cache(out_path=args.out)
    else:
        cache = xr.open_dataset(args.out).load()
        print(f'loaded cache {args.out} (--rebuild to recompute)', flush=True)

    # The grid and the regridder are the expensive per-figure setup; share
    # them across the two orientations.
    grid_ds = open_astedataset(GRID_DIR, grid_dir=GRID_DIR, iters=None)
    lm = llc_map(grid_ds)

    orientations = (('vertical', 'horizontal') if args.orientation == 'both'
                    else (args.orientation,))
    for orientation in orientations:
        fig, _ = make_fig6(cache, orientation=orientation, vel_str=args.vel,
                           ds=grid_ds, lm=lm, vmax=args.vmax,
                           show_titles=args.titles,
                           rasterize=not args.no_rasterize)
        suffix = '' if orientation == 'vertical' else f'_{orientation}'
        save_fig(fig, f'{FIG_NAME}{suffix}')
