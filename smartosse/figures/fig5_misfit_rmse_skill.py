"""Fig. 5 -- SPNA_cable misfit / RMSE / skill triptych (``fig:fullnatl_noapress_rms_skill``).

Port of ``smart_cables/osse/fullnatl_skill.ipynb`` (cells 1-11, the cell that
writes ``misfit_rmse_skill_opt_20ONLY.png``) onto this package's per-figure
module conventions.

Caption (``smartosse-manuscript/sections/results.tex``): "(a) Normalized
$p_b$ spatial misfit on January 1, 2012, (b) RMSE between $\\tilde{p}_b$ and
$p_b^{NR}$, and (c) $p_b$ skill in the SPNA cable experiment."

All three panels come from one OSSE -- the full SPNA cable, January 2012,
iterations 0 and 20 (`RUN_DIR` / `ITERNUMS`) -- and all three show the FINAL
iteration only (hence the notebook's "20ONLY" filename; an earlier version of
the figure carried a pre-optimization row, dropped in the Round-2 revision):

    (a) **Misfit**, ``bpdifanom_smooth * weight`` at iteration 20 on a single
        day (`MISFIT_TIME_INDEX`, day 0 = 2012-01-01). This is the *weighted*
        model-minus-data residual the cost function actually sees, i.e.
        normalized by :math:`\\sigma_{\\phi_{bot}}^{-2}` (Fig. 3's field), which
        is why the caption calls it "normalized" and why the colorbar is
        dimensionless. It is nonzero away from the sensors because of the
        spatial smoother (``Eqn. smoother``), not because there are data there.
    (b) **RMSE** of the optimized run against the NR over the month, in cm,
        time-means removed -- ``osse.compute_rms(fld_after, nr_fld, 'time')``.
    (c) **Skill**, ``osse._compute_skill``'s definition unchanged::

            s = 1 - rms(p_b^20 - p_b^NR) / rms(p_b^0 - p_b^NR)

The one deliberate styling change from the notebook
---------------------------------------------------
**Gridline (meridian/parallel) width and color**, per Matt's request that this
figure match Fig. 3. `GL_LINEWIDTH`/`GL_COLOR` are *imported* from
`fig3_bp_std` rather than re-declared, so the two figures cannot drift apart --
change them there and both follow. The notebook called a bare ``spna(1, 3)``,
which leaves ``ax.gridlines()`` on matplotlib's ``grid.linewidth``/``grid.color``
rcParam defaults (0.8 pt, ``'#b0b0b0'``); Fig. 3 uses 1.0 pt / ``'gray'``
(verified against the saved ``output/fig3_bp_std.png`` itself, not just its
source: its parallels measure 3-4 px wide at dpi=300 -- 1.0 pt, not the 1.8 pt
an older STATUS.md entry records -- with core pixels at RGB 128, i.e. ``gray``).
Everything else -- data, colormaps, color ranges, level counts, colorbar ticks
and tick labels, cable markers, panel-label placement, the negative
``wspace``/``hspace`` -- is the notebook's, unchanged.

Two mechanical departures, neither of which changes the rendered panels
----------------------------------------------------------------------
* **One `llc_map` per figure instead of one per panel.** The notebook called
  ``ds.plotpc(...)`` three times, and `plot.plotpc` constructs a fresh
  `llc_map` (a KD-tree over the full ASTE swath) on every call. This module
  builds it once and calls it directly, which is what `plotpc` does internally
  anyway -- same regrid, same `contourf`. Same pattern as
  `smart_grace_mo_skill` / `advfw_skill_maps`.
* **`contourf` fills are rasterized** (`rasterize=True`), per-collection
  because matplotlib 3.4's ``ContourSet`` is not an Artist and a
  ``rasterized=`` kwarg passed to ``contourf`` is silently dropped. No effect
  on the PNG at all; it takes the PDF from ~4.3 MB to well under 1 MB. Pass
  ``--no-rasterize`` (or ``rasterize=False``) for fully vector fills.

  Rasterizing on matplotlib < 3.5 *requires*
  ``figs_utils.patch_pdf_indexed_image_bitdepth()`` (called in ``__main__``
  below): a rasterized panel with <= 256 colors is written as a palette image
  whose ``/DecodeParms`` omits ``/BitsPerComponent``, so Acrobat cannot decode
  it and the PDF opens blank or "damaged" while the PNG is fine. See that
  helper's docstring.

The figure is saved on an **opaque white** background, not with
``transparent=True``: the Natural Earth land polygons and the regridded ASTE
field leave alpha=0 gaps along the coastlines, which any viewer compositing
onto a dark ground turns into black blobs behind the grey land.

The "N" latitude labels on panels (b)/(c) are hidden by
`plot.retain_only_perimiter_gl_labels`, the package's general version of the
notebook's hand-written ``for gl in gls[1:]: ... if 'N' in text`` loop.

As with the other figure modules, everything here is a small function over
already-loaded data, so the layout can be tweaked interactively from a
notebook; `make_fig5()` assembles the full figure as a starting template.

How to run
----------
::

    module load texlive
    conda activate /work2/08381/goldberg/ls6/miniforge3/envs/esmpy_3.10
    cd /work2/08381/goldberg/ls6/smartosse
    python -m smartosse.figures.fig5_misfit_rmse_skill
    python -m smartosse.figures.fig5_misfit_rmse_skill --rebuild   # redo cache

Writes ``output/fig5_misfit_rmse_skill.{png,pdf}`` and the cache
``data/fig5_misfit_rmse_skill.nc``.
"""
import argparse
import os

import numpy as np
import pandas as pd
import xarray as xr
import cmocean

from ..cmaps import Colormaps
from ..dataset import open_astedataset
from ..osse import NatureRun, MultiOSSE, compute_rms
from ..plot import llc_map, spna, gl_label_defaults, retain_only_perimiter_gl_labels
from .figs_utils import add_panel_label, add_cable_scatter
# Imported, not re-declared: this figure's gridlines are meant to match Fig. 3's
# exactly (Matt's ask). See the module docstring.
from .fig3_bp_std import GL_LINEWIDTH, GL_COLOR

# =============================================================================
# Data locations / run config
# =============================================================================

# SPNA_cable, January 2012, reanalysis-spread p_atm uncertainty -- the notebook's
# first (uncommented) `run_dir_root` + 'fullnatl/'.
RUN_DIR = ('/scratch/08381/goldberg/aste_270x450x180/osses/'
           'runc68v_froman_partialcables_jraspread/201201/fullnatl/')

# The notebook overrides the run's own iter0000/ grid with the standalone one.
GRID_DIR = '/work2/08381/goldberg/ls6/aste_270x450x180/GRID_noblank_real4/'

# First guess and final iteration. Panels show the FINAL one throughout
# (`ioptim=-1`); iteration 0 enters only as the skill score's denominator.
ITERNUMS = (0, 20)

MONTH = '201201'

# Day of the month drawn in panel (a). 0 = 2012-01-01, the caption's date.
# "Spatial misfits on subsequent days (not shown) are qualitatively
# comparable" -- results.tex.
MISFIT_TIME_INDEX = 0

DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
OUT_DIR = os.path.join(os.path.dirname(__file__), 'output')
CACHE = os.path.join(DATA_DIR, 'fig5_misfit_rmse_skill.nc')
FIG_NAME = 'fig5_misfit_rmse_skill'

# =============================================================================
# Panel styling -- all of this is the notebook's, unchanged
# =============================================================================

NLEV_DEFAULT = 18       # misfit and skill panels
NLEV_RMSE = 18

MISFIT_VMAX = 0.02      # dimensionless (weighted residual)
RMS_VMIN = 0.
RMS_VMAX = 5.           # cm
SKILL_VMAX = 1.0

# Per-panel colorbar tick counts. Panel (a)'s is overridden below by its own
# [-vmax, 0, +vmax] scientific-notation ticks, so its entry is unused; kept so
# the three lists stay index-aligned with the notebook's.
CBAR_NTICKS = (5, 3, 5)
CBAR_KWARGS = dict(pad=.1, shrink=.45)
CBAR_LABELS = ('', '[cm]', '')
CBAR_LABEL_FONTSIZE = 20
CBAR_TICK_KWARGS = dict(labelsize=20, length=6, width=1)

# Titles are off in the published figure (the caption carries them), but the
# strings are kept so `show_titles=True` reproduces the notebook's other render.
PANEL_TITLES = (r'Misfit',
                r'$\mathrm{RMSE}(\tilde{p}_b, p_b^{\mathrm{NR}})$',
                r'$\mathrm{skill}$')
TITLE_FONTSIZE = 20

PANEL_LABEL_FONTSIZE = 40
PANEL_LABEL_XY = (0.01, 0.8)

# Two overlaid scatters -> a black ring with a white centre, legible over both
# the pale and the saturated ends of all three colormaps.
CABLE_SCATTER_KWARGS = (
    dict(s=15, facecolor='k', edgecolor='k', linewidths=0.5, alpha=1, zorder=6),
    dict(s=7, facecolor='white', edgecolor='white', linewidths=0.5, alpha=1, zorder=7),
)

# Gridline label handling: the notebook's `gl_label_defaults()` overrides, then
# a post-hoc pass setting rotation/padding on the Gridliner itself.
GL_LABEL_FONTSIZE = 20
GL_XPADDING = 15

SUBPLOTS_ADJUST = dict(wspace=-.4, hspace=-.15)


# =============================================================================
# Loaders
# =============================================================================

def month_datetimes(month=MONTH):
    """The FM's daily record timestamps, 2012-01-01 .. 2012-01-31 (31 days).

    The notebook's ``start + MonthEnd(1)``; the commented-out ``+ 1 day`` in
    the notebook is deliberately not reproduced -- ``m_bpday`` holds 31
    records for January and an extra label would misalign the NR comparison.
    """
    start = pd.to_datetime(month, format='%Y%m')
    return pd.date_range(start=start, end=start + pd.offsets.MonthEnd(1), freq='D')


def build_osse(run_dir=RUN_DIR, grid_dir=GRID_DIR, iternums=ITERNUMS,
               datetimes=None, nr=None):
    """The notebook's cells 1-2: one `OSSE` over the full SPNA cable run.

    Returns the `OSSE`, which carries the FM (`osse.fm`, including its
    `BPReader` at ``osse.fm.bpr``), the sliced NR (`osse.nr.fld`), the grid
    (`osse.grid_ds`) and the already-computed skill map (`osse.fld_skill`).
    """
    datetimes = month_datetimes() if datetimes is None else datetimes
    nr = NatureRun() if nr is None else nr

    multi = MultiOSSE(nr)
    multi.add_forecast_model(run_dir, grid_dir=grid_dir, iternums=list(iternums),
                             datetimes=datetimes, ecco_frequency='day')
    return multi.comparisons[run_dir]


def compute_panel_fields(osse, time_index=MISFIT_TIME_INDEX):
    """The notebook's ``load_summary_data``: the three 2-D panel fields.

    Returns ``(misfit, rms, skill)``, each on the native ASTE ``(tile, j, i)``
    grid and not yet masked to wet cells (`make_fig5` does that, per panel, the
    way the notebook did).

    `misfit` is the weighted residual at the FINAL iteration
    (``ioptim=-1``, i.e. iteration 20 for the default `ITERNUMS`) on one day;
    `rms` and `skill` are month-long statistics with time means removed.
    """
    fld_after = osse.fm.fld.isel(ioptim=-1)
    rms = compute_rms(fld_after, osse.nr.fld, dim='time').compute()

    bp = osse.fm.bpr.ds
    misfit = (bp.bpdifanom_smooth * bp.weight).isel(ioptim=-1, time=time_index)

    return misfit.compute(), rms, osse.fld_skill


def cable_sensor_lonlat(osse):
    """Cable sensor lon/lat from the run's own `BPReader` sensor mask.

    Unlike `fig3_bp_std.load_cable_sensor_lonlat` / `smart_grace_mo_skill`,
    this run's ``iter0000`` still has its ``bpdifanom_raw`` on ``/scratch``, so
    the `BPReader` built for the panels already knows the sensors (via
    ``get_cost`` -> ``get_sensors``) and there is nothing to work around.
    `get_sensors` is called defensively in case that ever stops holding.
    """
    bpr = osse.fm.bpr
    if not getattr(bpr, 'sensor_args', None):
        bpr.get_sensors()
    lons, lats = (osse.grid_ds[coord].isel(bpr.sensor_args).values
                  for coord in ('XC', 'YC'))
    return lons, lats


def build_cache(out_path=CACHE, run_dir=RUN_DIR, grid_dir=GRID_DIR,
                iternums=ITERNUMS, time_index=MISFIT_TIME_INDEX):
    """Compute the three panel fields + the sensor locations once, and cache.

    Everything the figure needs from ``/scratch`` lands here, so re-laying-out
    the figure (in a notebook or after a purge) needs only this file and the
    ``/work`` grid.
    """
    osse = build_osse(run_dir=run_dir, grid_dir=grid_dir, iternums=iternums)
    misfit, rms, skill = compute_panel_fields(osse, time_index=time_index)
    lons, lats = cable_sensor_lonlat(osse)

    cache = xr.Dataset(
        dict(misfit=misfit.reset_coords(drop=True),
             rms=rms.reset_coords(drop=True),
             skill=skill.reset_coords(drop=True),
             cable_lon=('sensor', np.asarray(lons)),
             cable_lat=('sensor', np.asarray(lats))),
    )
    cache.attrs.update(
        note=('(a) bpdifanom_smooth * weight at the final iteration on one day; '
              '(b) rms(p_b^N - p_b^NR) over the month, cm, time means removed; '
              '(c) skill = 1 - rms_after/rms_before (smartosse.osse._compute_skill)'),
        run_dir=run_dir,
        grid_dir=grid_dir,
        iternums=str(list(iternums)),
        misfit_time_index=str(time_index),
        misfit_date=str(month_datetimes()[time_index].date()),
        n_sensors=str(len(lons)),
    )
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    cache.to_netcdf(out_path)
    print(f'[cache] {len(lons)} sensors; '
          f'misfit |max|={float(np.abs(misfit).max()):.3g}  '
          f'rms max={float(rms.max()):.3g} cm  '
          f'skill mean={float(skill.mean()):+.4f}', flush=True)
    print('wrote', out_path, flush=True)
    return cache


# =============================================================================
# Plot pieces
# =============================================================================

def panel_cmaps(nlev_default=NLEV_DEFAULT, nlev_rmse=NLEV_RMSE):
    """(misfit, rms, skill) colormaps -- the notebook's three, unchanged.

    The skill map is the package's standard white-centred ``cmocean curl_r``
    (same construction as ``osse._plot_skill``, `si_skill_over_optim` and
    `smart_grace_mo_skill`, so those panels sit directly next to this one);
    the misfit map is `Colormaps.custom_div_cmap`'s default (``cmocean
    balance``) template.
    """
    return (Colormaps(nlev_default).custom_div_cmap(),
            'Purples',
            Colormaps(nlev_default).custom_div_cmap(template_cmap=cmocean.cm.curl_r))


def make_gl_label_args(fontsize=GL_LABEL_FONTSIZE):
    """The notebook's gridline-label config: bottom labels only, unrotated,
    nudged down off the frame."""
    args = gl_label_defaults()
    args['top'] = {'hide': True, 'rotate': True, 'pad': 0.0}
    args['right'] = {'hide': True, 'rotate': True, 'pad': 0.0}
    args['bottom'] = {'hide': False, 'rotate': True, 'pad': 0.06}
    args['fontsize'] = fontsize
    return args


def style_gridliners(gl_list, xpadding=GL_XPADDING):
    """The notebook's post-`spna` pass over the Gridliner objects.

    Redundant with `make_gl_label_args` for the hiding (`process_gridline_labels`
    has already set those artists invisible), but ``top_labels``/``right_labels``
    also stop Cartopy re-creating them on a later draw, and
    ``xlabel_style``/``xpadding`` are Gridliner-level knobs
    `process_gridline_labels` doesn't touch.
    """
    for gl in gl_list:
        gl.right_labels = False
        gl.top_labels = False
        gl.xlabel_style = {'rotation': 0}
        gl.xpadding = xpadding
    return gl_list


def draw_panel(ax, lm, field, cmap, vmin, vmax, nlev, cbar_kwargs=None,
               rasterize=True):
    """Filled-contour one panel and return ``(cb, p)``.

    Calls the prebuilt `llc_map` directly rather than ``ds.plotpc(...)``, which
    would build a new one per panel; the draw itself is identical.
    """
    cbar_kwargs = CBAR_KWARGS if cbar_kwargs is None else cbar_kwargs
    _, cb, p = lm(field, ax=ax,
                  plot_type='contourf',
                  cmap=cmap,
                  vmin=vmin, vmax=vmax,
                  levels=np.linspace(vmin, vmax, nlev),
                  cbar_kwargs=dict(cbar_kwargs),
                  show_cbar=True)
    if rasterize:
        # Per-collection: matplotlib 3.4's ContourSet is not an Artist, so a
        # `rasterized=` kwarg handed to contourf is silently dropped.
        for coll in p.collections:
            coll.set_rasterized(True)
    return cb, p


def format_misfit_cbar(cb, vmin=-MISFIT_VMAX, vmax=MISFIT_VMAX):
    """Panel (a): three ticks at -vmax / 0 / +vmax, scientific-notation labels.

    The notebook's own one-liner, spelled out: ``f'{t:.0e}'`` gives ``2e-02``,
    and the replaces strip the exponent's leading zero (and any ``+``) to give
    ``2e-2``, with a bare ``0`` in the middle.
    """
    ticks = [vmin, 0, vmax]
    cb.set_ticks(ticks)
    cb.set_ticklabels([
        '0' if t == 0
        else f'{t:.0e}'.replace('+', '').replace('e0', 'e').replace('e-0', 'e-')
        for t in ticks
    ])
    return cb


def format_linear_cbar(cb, vmin, vmax, nticks):
    """Panels (b)/(c): `nticks` evenly spaced ticks, one decimal place."""
    ticks = np.linspace(vmin, vmax, nticks)
    cb.set_ticks(ticks)
    cb.set_ticklabels([f'{t:.1f}' for t in ticks])
    return cb


# =============================================================================
# Assembly
# =============================================================================

def make_fig5(cache, ds=None, lm=None, show_titles=False, rasterize=True,
              gl_linewidth=GL_LINEWIDTH, gl_color=GL_COLOR, verbose=True):
    """Assemble the 1x3 figure: (a) misfit, (b) RMSE, (c) skill.

    `cache` is `build_cache`'s Dataset. `ds` (the ASTE grid) and `lm` (the
    `llc_map` regridder) may be passed in to avoid rebuilding them when
    iterating on layout from a notebook.

    Returns
    -------
    fig, axes
    """
    if ds is None:
        ds = open_astedataset(GRID_DIR, grid_dir=GRID_DIR, iters=None)
    if lm is None:
        lm = llc_map(ds)

    fig, axes, gl_list = spna(1, 3, return_gl=True,
                              gl_label_args=make_gl_label_args(),
                              gl_linewidth=gl_linewidth, gl_color=gl_color)
    style_gridliners(gl_list)

    cmaps = panel_cmaps()
    fields = (cache['misfit'], cache['rms'], cache['skill'])
    vmins = (-MISFIT_VMAX, RMS_VMIN, -SKILL_VMAX)
    vmaxs = (MISFIT_VMAX, RMS_VMAX, SKILL_VMAX)
    nlevs = (NLEV_DEFAULT, NLEV_RMSE, NLEV_DEFAULT)

    wet = ds.hFacC[0]
    for col, ax in enumerate(axes):
        # The notebook masks (b) with `.where(hFacC)` -- keeping NaN land -- but
        # multiplies (a) and (c) by it, so land there goes to 0 rather than NaN.
        # Deliberately preserved: it is what puts (a)/(c)'s land at the centre
        # of their diverging colormaps instead of leaving it blank.
        field = fields[col].where(wet) if col == 1 else fields[col] * wet

        cb, _ = draw_panel(ax, lm, field, cmaps[col], vmins[col], vmaxs[col],
                           nlevs[col], rasterize=rasterize)

        for scatter_kwargs in CABLE_SCATTER_KWARGS:
            add_cable_scatter(ax, cache['cable_lon'].values,
                              cache['cable_lat'].values, **scatter_kwargs)

        add_panel_label(ax, 'abc'[col], fontsize=PANEL_LABEL_FONTSIZE,
                        x=PANEL_LABEL_XY[0], y=PANEL_LABEL_XY[1])

        if show_titles:
            ax.set_title(PANEL_TITLES[col], fontsize=TITLE_FONTSIZE, pad=10)

        if cb is not None:
            cb.ax.set_xlabel(CBAR_LABELS[col], fontsize=CBAR_LABEL_FONTSIZE)
            cb.ax.tick_params(**CBAR_TICK_KWARGS)
            if col == 0:
                format_misfit_cbar(cb, vmins[col], vmaxs[col])
            else:
                format_linear_cbar(cb, vmins[col], vmaxs[col], CBAR_NTICKS[col])

    # Latitude labels on the left panel only -- the package's general version of
    # the notebook's hand-written "hide the 'N' labels on gls[1:]" loop.
    fig.canvas.draw()
    retain_only_perimiter_gl_labels(np.array([axes]), gl_list)

    fig.subplots_adjust(**SUBPLOTS_ADJUST)

    if verbose:
        for name, vmax in (('misfit', MISFIT_VMAX), ('rms', RMS_VMAX),
                           ('skill', SKILL_VMAX)):
            da = cache[name]
            frac = float((np.abs(da) > vmax).sum() / np.isfinite(da).sum())
            print(f'[fig] {name}: mean={float(da.mean()):+.4g} '
                  f'p98|x|={float(np.abs(da).quantile(0.98)):.4g} '
                  f'{100 * frac:.1f}% beyond |{vmax}|', flush=True)

    return fig, axes


# =============================================================================
if __name__ == '__main__':
    ap = argparse.ArgumentParser(description='Fig. 5: misfit / RMSE / skill')
    ap.add_argument('--run-dir', default=RUN_DIR, help='SPNA_cable OSSE run directory')
    ap.add_argument('--time-index', type=int, default=MISFIT_TIME_INDEX,
                    help='day of the month shown in panel (a); 0 = 2012-01-01')
    ap.add_argument('--titles', action='store_true',
                    help="draw the notebook's per-panel titles (off in the manuscript)")
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
    # < 3.5, or the PDF's palette-encoded panels are unreadable. See the
    # helper's docstring and the "Two mechanical departures" note above.
    patch_pdf_indexed_image_bitdepth()

    if args.rebuild or not os.path.exists(args.out):
        cache = build_cache(out_path=args.out, run_dir=args.run_dir,
                            time_index=args.time_index)
    else:
        cache = xr.open_dataset(args.out).load()
        print(f'loaded cache {args.out} (--rebuild to recompute)', flush=True)

    fig, axes = make_fig5(cache, show_titles=args.titles,
                          rasterize=not args.no_rasterize)

    os.makedirs(OUT_DIR, exist_ok=True)
    for ext in ('png', 'pdf'):
        # Opaque white, NOT transparent=True. The land feature and the
        # regridded field don't tile the map exactly, so a transparent save
        # leaves alpha=0 pinholes and blobs along every coastline; any viewer
        # that composites onto a dark ground (and pdflatex, and Acrobat's dark
        # mode) renders those as black smudges behind the grey land.
        fig.savefig(os.path.join(OUT_DIR, f'{FIG_NAME}.{ext}'), dpi=300,
                    bbox_inches='tight', facecolor='white', edgecolor='none')
    print(f'wrote {FIG_NAME}.{{png,pdf}} to {OUT_DIR}')
