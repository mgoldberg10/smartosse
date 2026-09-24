"""
Fig. 10 (extended to 3 x 2) -- p_atm mechanism (partial IB) + sea-level byproduct.

Layout (see smartosse-manuscript/reviews/fig_revision_plan_reviewer2.md):

    (a) p_b misfit, iter 0             [map]
    (b) p_b misfit, iter 20            [map]
    (c) dp_atm adjustment, iter 20     [map]
    (d) std(dp_atm)/sigma_patm ratio   [map]
    (e) IB scatter: dp_eta vs -dp_atm/(rho g), slope = IB fraction   [square]
    (f) eta skill (weak, vs. the dense p_b skill in Figs 5/6)        [map]

(a)-(d) reproduce the current published figure (fig:misfit_and_apressure in
controls.tex) for one partial-cable OSSE (default: SPG_cable / region
'subgyre'), following
smart_cables/osse/fig10_subgyre_pb_misfit_patm_adjustments.ipynb. (e) and (f)
are new, from the STD-BASED main run per the revision plan, reproducing the
prototype in smart_cables/osse/fullnatl_skill.ipynb (cells ~63-73), which
gets slope ~ 0.829 -- matching Reviewer #2's ~10-20% "departure from full IB"
estimate. See smartosse-manuscript/reviews/eta_ib_check_notes.md for what the
slope means physically (delta p_b = (1 - slope) * delta p_atm).

NOTE (2026-07-13, Matt's request): (e)/(f) content was swapped from the
original mechanism -> consequence layout (eta skill map under (c), IB scatter
under (d)) to IB scatter under (c) / eta skill map under (d) -- letters stay
in normal reading-order position (row 3 left = e, right = f), only the
content moved. This breaks the "(e)/(f) sit below the panel whose adjustment
field they explain" rationale the original layout was built around -- purely
a requested visual rearrangement, not a re-derivation of that logic.

As with fig9_patm_unc.py, everything here is a small function taking
already-loaded data (or a run directory) and returning ``ax``, so panels can
be built, tweaked, and re-laid-out interactively from a notebook.

NOTE (panel c/d time indexing): the day index used to pull a control knot for
panel (c) is `time + 1` relative to the misfit-panel day index `time`, a
convention carried over unmodified from the original fig10 notebook. This is
a *different* knot-alignment convention than fig9_patm_unc.load_patm_adjustment
(which reverses time) or the day-center interpolation used here for panel
(f) -- the three were developed independently and haven't been reconciled.
Reproduced as-is for (a)-(d) since the revision plan says to keep them
unchanged; see eta_ib_check_notes.md and fig9_patm_unc's module docstring
before trusting this indexing for anything new/quantitative.

NOTE (panel d vmax): the original notebook plotted patm_std/sigma with
vmax=0.11, even though the field's actual max is ~0.575 and the colorbar
ticks were hardcoded to [0, 0.5, 1] (i.e. written for vmax=1). That mismatch
looks like a leftover from interactive vmax tuning, not an intentional
choice -- ``make_fig10`` defaults to vmax=1 (matching the [0, 0.5, 1] ticks
and the "no more than about 50%" claim in controls.tex); pass
``vmax_ratio=0.11`` if you need to reproduce the currently-published PNG
exactly.

NOTE (panel subsets): ``make_fig10(ds, panels='abcd')`` builds just the top
2x2 -- the four map panels that reproduce the currently-published
fig:misfit_and_apressure -- skipping the (slow) eta OSSE load entirely, since
nothing in (a)-(d) depends on it. Panel content/styling is identical to the
full 3x2; the only layout differences are the grid shape, the default
figsize, and (d) keeping its bottom longitude labels (in the 3x2 they're
hidden only because (f) sits directly below it).

How to run
----------
::

    module load texlive
    conda activate /work2/08381/goldberg/ls6/miniforge3/envs/esmpy_3.10
    cd /work2/08381/goldberg/ls6/smartosse
    python -m smartosse.figures.fig10_patm_mechanism                  # full 3x2
    python -m smartosse.figures.fig10_patm_mechanism --panels abcd    # top 2x2

Writes ``output/fig10_patm_mechanism.{png,pdf}`` (full) or
``output/fig10_patm_mechanism_abcd.{png,pdf}`` (subset).

NOTE (run/sigma drift -- read before trusting a fresh render): ``RUN_DIR`` and
``load_sigma_patm_std`` come from ``fig9_patm_unc``, and both were repointed
after this figure was last rendered (2026-07-13) -- onto the
``jrastd_daytoday`` run and the ``wApressure_jra2012_daytoday_std.bin`` prior,
which is the file with the hPa-vs-Pa unit bug (see
``gen_patm_daytoday_weight_Pa.py`` and STATUS.md 2026-08-06). With those
defaults panels (c)/(d) are badly off scale. To reproduce the *published*
fig:misfit_and_apressure panels, pass the sub-daily-std run and prior::

    python -m smartosse.figures.fig10_patm_mechanism --panels abcd \
        --run-dir /scratch/08381/goldberg/aste_270x450x180/osses/\
runc68v_froman_partialcables_jrastd/201201/subgyre/ \
        --sigma-file /work2/08381/goldberg/ls6/aste_270x450x180/run_template/\
input_weight/wApressure_ASTE270_EXFpress_std_new.bin \
        --patm-iternums 1 20

NOTE (spread-prior variant): the reanalysis-SPREAD counterpart of (a)-(d) --
i.e. the notebook's
``subgyre_wmisfit_apressure_SPREAD_jan012012_opt0_opt20_ONLY_stdUncRatio.png``
-- is the ``runc68v_froman_partialcables_jraspread`` run with the notebook's
own color limits (its adjustments are ~8x smaller than the std run's, so 4 hPa
would show almost nothing in (c))::

    python -m smartosse.figures.fig10_patm_mechanism --panels abcd \
        --run-dir /scratch/08381/goldberg/aste_270x450x180/osses/\
runc68v_froman_partialcables_jraspread/201201/subgyre/ \
        --sigma-file /work2/08381/goldberg/ls6/aste_270x450x180/run_template/\
input_weight/wApressure_ASTE270_EXFpress_std_new.bin \
        --patm-iternums 1 20 --vmax-ctrl 0.5 \
        --vmax-ratio 0.051 --ratio-cbar-ticks 0 0.05 \
        --cbar-decimals 2 --gl-labels perimeter \
        --out-name fig10_patm_mechanism_abcd_spread

Note that this reproduces the notebook exactly, and the notebook divides the
SPREAD run's adjustments by the **std** sigma in panel (d) (its ``spread=True``
branch loads ``wApressure_ASTE270_EXFpress_std_new.bin``; hence "stdUncRatio"
in the filename). For (d) against the prior that run actually used, pass
``--sigma-file .../wApressure_ASTE270_jra55_jra3q_era_spread.bin --vmax-ratio
0.15 --ratio-cbar-ticks 0 0.15``. See STATUS.md 2026-08-17 (later).

NOTE (fonts): call ``figs_utils.use_serif_mathtext()`` once in your notebook
before plotting to get serif-rendered panel letters and math-mode axis
labels (e.g. panel (f)'s x/y labels) while leaving cartopy lat/lon gridline
labels, colorbar tick numbers, and axis tick numbers in the default font.
This replaces the old ``plt.rcParams.update({"text.usetex": True, ...})``
notebook cell, which would have made *all* text (including tick numbers)
serif.
"""
import copy
import os

import numpy as np
import xarray as xr
import pandas as pd
import matplotlib.pyplot as plt
import cartopy.crs as ccrs

from ..utils import read_aste_bin
from ..bp import BPReader
from ..osse import NatureRun, ForecastModel, OSSE
from ..plot import spna
from ..cmaps import Colormaps
from .figs_utils import add_panel_label, add_cable_scatter, style_colorbar
from .fig9_patm_unc import RUN_DIR_ROOT_STD, load_sigma_patm_std

REGION = 'subgyre'
RUN_DIR = RUN_DIR_ROOT_STD + REGION + '/'

# Two eta nature-run directories exist on this machine: this one (used by the
# working fullnatl_skill.ipynb prototype, multi-month) and the older
# /work2/08381/goldberg/ls6/Eta_llc4320_astefaces_coarsened/eta_processed_daily/
# (used by the original fig10 notebook, January-only). Defaulting to the
# former since it's the one the validated slope=0.829 result came from.
ETA_NR_DIR = '/scratch/08381/goldberg/llc_4320/eta_coarse/eta_daily/'

MO_STR = '201201'
RHO, G = 1029., 9.81

# sigma_phibot [cm], the p_b misfit weight's error file. `BPReader.read_weight`
# normally finds this by parsing `gencost_errfile` out of the run's
# `iter0000/data.ecco`, but the jrastd_daytoday reruns on /scratch shipped only
# their bp/diags output -- no data.ecco, and no run-local copy of the errfile --
# so the constructor raises. This is the canonical /work copy of that same
# field (byte-identical, md5 c2894df2..., to the run-local copies that survive
# in the sibling BADrunc68v_... tree, and it is the same file for every region,
# so nothing region-specific is lost by reading it from here). Same purge
# workaround, and same reason, as fig3_bp_std.load_cable_sensor_lonlat and
# gen_appendixB_skill_cache.load_bp_anom.
BP_SIGMA_FILE = ('/work/08381/goldberg/ls6/aste_270x450x180/run_template/'
                 'input_ecco/smart_phibot/'
                 'bp_var_day_coarse4320_detide16constituent_std_cm.bin')

OUT_DIR = os.path.join(os.path.dirname(__file__), 'output')
FIG_NAME = 'fig10_patm_mechanism'

# Panel sets make_fig10 knows how to lay out, and the default figsize for each.
# 'abcd' is the top 2x2 (the four map panels of the published
# fig:misfit_and_apressure); 'abcdef' is the full 3x2.
PANEL_SETS = {
    'abcd':   dict(nrows=2, figsize=(11, 10)),
    'abcdef': dict(nrows=3, figsize=(11, 15)),
}

# spna()'s own gl_label_args default (plot.py) -- kept here so panel (c) can
# override just the 'bottom' (longitude) entry without silently losing the
# other three (spna() replaces gl_label_args wholesale, it doesn't merge).
SPNA_GL_ARGS_DEFAULT = {
    'top':    {'hide': True,  'rotate': False, 'pad': 0.0},
    'bottom': {'hide': False, 'rotate': True,  'pad': 0.1, 'threshold': 0.0001},
    'left':   {'hide': False, 'rotate': False, 'pad': 0.0},
    'right':  {'hide': True,  'rotate': False, 'pad': 0.0, 'threshold': 0.2},
    'fontsize': 20,
}


# =============================================================================
# Loaders
# =============================================================================

def _attach_weight_from_sigma_file(bpr, sigma_file=BP_SIGMA_FILE):
    """Set `bpr.ds['sigma']`/`['weight']` from a standalone errfile binary,
    reproducing the last two lines of ``BPReader.read_weight`` verbatim (only
    the way the file is *located* differs -- see BP_SIGMA_FILE)."""
    sigma = read_aste_bin(sigma_file, var_name='sigma')
    bpr.ds['sigma'] = sigma.where(sigma != -9999.).squeeze()
    bpr.ds['weight'] = bpr.ds.sigma.where((bpr.ds.sigma != 0)
                                          & ~np.isnan(bpr.ds.sigma)) ** -2
    return bpr


def load_bp_misfit_maps(run_dir=RUN_DIR, iternums=(0, 20), time=1, ecco_frequency='day',
                         sigma_file=BP_SIGMA_FILE):
    """(a)/(b): BPReader + the smoothed, weighted p_b misfit field on one day,
    before and after optimization.

    Returns (bpr, misfit_before, misfit_after). `bpr` carries `.sensor_args`
    for the cable-scatter overlay used on every panel.

    If the run directory has no ``data.ecco`` (true of the jrastd_daytoday
    reruns as of 2026-08-17, though not when this module was first written),
    the reader is built with ``read_weight`` stubbed out and the weight is
    attached afterwards from `sigma_file` -- identical numbers, since that is
    the same field ``data.ecco`` would have pointed at.
    """
    try:
        bpr = BPReader(run_dir, iternums=list(iternums), ecco_frequency=ecco_frequency)
    except FileNotFoundError as exc:
        if 'data.ecco' not in str(exc):
            raise
        print(f'[fig10] no data.ecco in {run_dir}; taking the misfit weight from '
              f'{sigma_file}', flush=True)
        read_weight = BPReader.read_weight
        BPReader.read_weight = lambda self, *a, **kw: None
        try:
            # get_cost() (called from __post_init__) still runs and still sets
            # .sensor_args; it just bails on the now-absent 'sigma' instead of
            # computing self.cost -- which nothing here consumes anyway.
            bpr = BPReader(run_dir, iternums=list(iternums), ecco_frequency=ecco_frequency)
        finally:
            BPReader.read_weight = read_weight
        _attach_weight_from_sigma_file(bpr, sigma_file)
    ds0 = bpr.ds.isel(ioptim=0)
    ds1 = bpr.ds.isel(ioptim=-1)
    misfit_before = (ds0.bpdifanom_smooth * ds0.weight).isel(time=time)
    misfit_after = (ds1.bpdifanom_smooth * ds1.weight).isel(time=time)
    return bpr, misfit_before, misfit_after


def load_patm_adjustment_knots(run_dir=RUN_DIR, iternums=(1, 20)):
    """xx_apressure.effective control-adjustment knots [Pa], concatenated
    along 'ioptim'. Backs panels (c), (d), and (f)."""
    das = [
        read_aste_bin(f'{run_dir}iter{it:04d}/xx_apressure.effective.{it:010d}.data')
        for it in iternums
    ]
    ioptim = xr.DataArray(list(iternums), dims='ioptim', name='ioptim')
    xx = xr.concat(das, dim=ioptim)
    return xx.rename({'k': 'time'})


def compute_patm_adjustment_field(patm_adjustment, time=1, iternum_idx=-1):
    """(c): one day's dp_atm adjustment [hPa]. See module NOTE re: the
    `time + 1` knot offset."""
    return patm_adjustment.isel(ioptim=iternum_idx).isel(time=time + 1) / 100.


def compute_patm_std_ratio(patm_adjustment, sigma, iternum_idx=-1):
    """(d): std(dp_atm) over the month, divided by sigma_patm (dimensionless,
    ~0-0.6 in practice)."""
    patm_std = patm_adjustment.isel(ioptim=iternum_idx).std('time')
    return patm_std / sigma


def load_eta_osse(run_dir=RUN_DIR, iternums=(0, 20), nr_dir=ETA_NR_DIR, mo_str=MO_STR):
    """OSSE comparing the FM's ETAN against the (coarsened LLC4320) eta
    nature run. Backs both panel (e)'s eta skill and panel (f)'s IB scatter.

    Slow (reads a full month of 2D surface diagnostics via xmitgcm) -- load
    once per session and reuse.
    """
    start = pd.to_datetime(mo_str, format='%Y%m')
    end = start + pd.offsets.MonthEnd(1)
    datetimes = pd.date_range(start=start, end=end, freq='D')

    nr = NatureRun(nr_dir=nr_dir, fld_type='eta')
    fm = ForecastModel(run_dir, iternums=list(iternums), datetimes=datetimes, fld_type='eta')
    return OSSE(fm, nr)


def compute_ib_scatter(eta_osse, patm_adjustment, start=None, period=pd.Timedelta('1D'),
                        ctrl_offset=0, pct=75, subset_time=None, mo_str=MO_STR):
    """(f): dp_eta vs the IB-predicted sea level from the dp_atm adjustment.

    Aligns the (daily, instantaneous) control knots onto the (daily-mean)
    ETAN diagnostic's day-centers by linear interpolation, then restricts to
    grid points where |dp_atm| is in the top (100-pct)% -- reproduces
    smartosse-manuscript/reviews/eta_ib_histogram.py as a function. Returns
    a dict with the flattened, thresholded (x, y) arrays [cm] and the
    origin-through slope (the IB fraction; report this, not a pointwise
    ratio -- see eta_ib_check_notes.md).
    """
    if start is None:
        start = pd.to_datetime(mo_str, format='%Y%m')

    xx = patm_adjustment.isel(ioptim=-1)
    ctrl_t = start + (np.arange(xx.sizes['time']) + ctrl_offset) * period
    xx = xx.assign_coords(time=ctrl_t)

    eta = eta_osse.fm.ds_surf.ETAN
    d_eta = eta.isel(ioptim=-1) - eta.isel(ioptim=0)
    diag_t = start + (np.arange(d_eta.sizes['time']) + 0.5) * period
    d_eta = d_eta.assign_coords(time=diag_t)

    d_patm = xx.interp(time=diag_t, method='linear')
    ib_pred = -d_patm / (RHO * G)

    if subset_time is not None:
        d_eta = d_eta.isel(time=subset_time)
        d_patm = d_patm.isel(time=subset_time)
        ib_pred = ib_pred.isel(time=subset_time)

    x = np.asarray(ib_pred).ravel() * 100.   # cm
    y = np.asarray(d_eta).ravel() * 100.     # cm
    dp = np.abs(np.asarray(d_patm).ravel())

    good = np.isfinite(x) & np.isfinite(y) & np.isfinite(dp)
    thresh = np.nanpercentile(dp[good], pct)
    sel = good & (dp > thresh)
    x, y = x[sel], y[sel]

    slope = np.sum(x * y) / np.sum(x * x)   # least-squares slope, no intercept
    return dict(x=x, y=y, slope=float(slope), threshold_pa=float(thresh), pct=pct)


# =============================================================================
# Plotting primitives
# =============================================================================

def plot_ib_scatter(ax, ib_scatter, lim=None, cmap='viridis', hexbin_kwargs=None,
                     fit_kwargs=None, oneone_kwargs=None, ticks=(-1, 0, 1),
                     tick_labelsize=18, label_fontsize=20, legend_fontsize=14,
                     legend_loc='lower right', add_colorbar=True,
                     colorbar_label='log$_{10}$(count)', colorbar_labelsize=12,
                     colorbar_kwargs=None, aspect_anchor='NE'):
    """(f): hexbin density of dp_eta vs the IB prediction, with the
    origin-through fit (slope = IB fraction) and the 1:1 (full-IB) line."""
    x, y, slope = ib_scatter['x'], ib_scatter['y'], ib_scatter['slope']

    if lim is None:
        lim = np.nanpercentile(np.abs(np.concatenate([x, y])), 99)

    hk = dict(gridsize=60, bins='log', cmap=cmap, extent=(-lim, lim, -lim, lim))
    hk.update(hexbin_kwargs or {})
    hb = ax.hexbin(x, y, **hk)

    xline = np.linspace(-lim, lim, 100)
    # newline before "(IB fraction)" keeps the legend box narrow enough to
    # actually fit in the bottom-right quadrant instead of spanning the panel.
    fk = dict(color='r', lw=2, label=f'slope = {slope:.2f}\n(IB fraction)')
    fk.update(fit_kwargs or {})
    ax.plot(xline, slope * xline, **fk)

    ok = dict(color='k', ls='--', lw=1.5, label='1:1 (full IB)')
    ok.update(oneone_kwargs or {})
    ax.plot(xline, xline, **ok)

    ax.axhline(0, color='0.6', lw=0.5)
    ax.axvline(0, color='0.6', lw=0.5)
    ax.set_xlim(-lim, lim)
    ax.set_ylim(-lim, lim)
    # aspect_anchor: when this box is shrunk to enforce equal data aspect,
    # keep it flush with its allotted box's corner (see make_fig10's
    # panel_scatter_shrink, which pre-shrinks that box, using the matching
    # corner) rather than centering. 'NE' when this panel sits in the right
    # column, 'NW' when it sits in the left column.
    ax.set_aspect('equal', adjustable='box', anchor=aspect_anchor)
    ax.set_xlabel(r'$-\,\delta p_{atm}/(\rho g)$  [cm]', fontsize=label_fontsize)
    ax.set_ylabel(r'$\delta\eta$  [cm]', fontsize=label_fontsize)

    if ticks is not None:
        ax.set_xticks(ticks)
        ax.set_yticks(ticks)
    ax.tick_params(axis='both', which='major', labelsize=tick_labelsize)
    ax.legend(loc=legend_loc, fontsize=legend_fontsize, handlelength=1.4,
              labelspacing=0.6)

    cb = None
    if add_colorbar:
        cbk = dict(label=colorbar_label, shrink=0.8)
        cbk.update(colorbar_kwargs or {})
        cb = ax.figure.colorbar(hb, ax=ax, **cbk)
        cb.ax.tick_params(labelsize=colorbar_labelsize)

    return ax, hb, cb


def plot_eta_skill_map(eta_osse, ax=None, vmax=1., title='', **plot_kwargs):
    """(e): eta skill map -- expected weak/limited relative to the dense p_b
    skill in Figs 5/6. Thin wrapper around OSSE.plot_skill (osse.py); a
    fresh spna() axis is used if `ax` is None.

    Colormap is *not* set here -- OSSE.plot_skill -> osse._plot_skill builds
    it internally as ``Colormaps(nlev).custom_div_cmap(template_cmap=
    cmocean.cm.curl_r)``, where `nlev` is whatever gets passed through
    `plot_kwargs` (make_fig10 passes `nlev_eta_skill` here, which becomes
    that same `nlev` -- so the contourf level count and the colormap's color
    count always stay in sync automatically, not just something to keep
    parallel by hand).
    """
    fig, ax, cb, p = eta_osse.plot_skill(vmax_default=vmax, ax=ax, **plot_kwargs)
    ax.set_title(title)
    return fig, ax, cb, p


# =============================================================================
# Full-figure assembly
# =============================================================================

def make_fig10(
    ds,
    run_dir=RUN_DIR,
    time=1,
    sigma=None,
    bp_misfit=None,
    patm_adjustment=None,
    eta_osse=None,
    ib_scatter=None,
    vmax_misfit=0.01,
    vmax_ctrl=4.,
    vmax_ratio=1.,
    vmax_eta_skill=1.,
    nlev_eta_skill=20,
    eta_skill_cbar_ticks=None,
    ratio_cbar_ticks=None,
    cbar_decimals=None,
    gl_labels=None,
    patm_iternums=(1, 20),
    panels='abcdef',
    figsize=None,
    hspace=0.3,
    wspace=0.15,
    cbar_height_frac=0.9,
    cbar_y_shift_frac=None,
    gl_fontsize=13,
    panel_scatter_shrink=0.85,
):
    """Assemble the 3x2 mosaic (or a subset of it) from already-loaded pieces.

    `panels` selects which panels to build -- ``'abcdef'`` (default) for the
    full 3x2, or ``'abcd'`` for just the top 2x2 map row-pair. With
    ``'abcd'`` the eta OSSE and the IB scatter are never loaded or computed
    (nothing in (a)-(d) uses them), so `eta_osse`/`ib_scatter` can be left
    None even without a loaded OSSE in hand; panel content and styling are
    otherwise byte-for-byte the same code path as in the full figure. The one
    deliberate layout difference: (d) keeps its bottom (longitude) gridline
    labels, which the full figure hides only because (f) sits directly below
    it. `figsize=None` picks the default for the chosen panel set (see
    PANEL_SETS).

    Pass in sigma/bp_misfit/patm_adjustment/eta_osse/ib_scatter explicitly
    (e.g. from the load_*/compute_* functions above) rather than having this
    function load everything itself, so a notebook can load once (the eta
    OSSE load is slow) and iterate on layout/styling quickly.

    `cbar_height_frac`/`cbar_y_shift_frac` are passed straight through to
    figs_utils.style_colorbar for every map-panel colorbar (a/b/c/d/f) --
    see that function's docstring; they reproduce the original notebook's
    manual colorbar shrink-and-nudge, in case this gridspec's default
    spacing needs the same treatment.

    `gl_fontsize` sets every map panel's cartopy lat/lon gridline label size
    (spna()'s own default is 20, quite large for a 3x2 mosaic).

    `cbar_decimals` fixes every colorbar's tick-label precision (2 -> '-0.50',
    '0.05'; 0 always stays '0'), and `gl_labels='perimeter'` drops the interior
    lat/lon ticklabels so only the left column carries latitudes and only the
    bottom row longitudes -- the original notebook's framing, available for
    ``panels='abcd'`` only. Both default to the pre-existing behavior.

    `nlev_eta_skill`/`eta_skill_cbar_ticks` control panel (f)'s (eta skill)
    contourf level count and colorbar tick placement independently of the
    other map panels -- `eta_skill_cbar_ticks=None` falls back to
    style_colorbar's own default (3 evenly spaced ticks over (-vmax_eta_skill,
    vmax_eta_skill)).

    `panel_scatter_shrink` shrinks the IB-scatter panel's ((e), plain axes,
    no colorbar) raw gridspec cell (both width and height, before
    plot_ib_scatter's equal-aspect square gets fit into it), anchored at its
    top-left corner -- needed because (f) has a colorbar eating into the
    bottom of its cell (pushing its map up within row 3) while (e) has no
    colorbar, so (e)'s square would otherwise be centered in a taller box
    than (f)'s and sit too low. Set to 1.0 to disable.
    """
    if panels not in PANEL_SETS:
        raise ValueError(f'panels={panels!r} not supported; '
                         f'expected one of {sorted(PANEL_SETS)}')
    nrows = PANEL_SETS[panels]['nrows']
    figsize = figsize if figsize is not None else PANEL_SETS[panels]['figsize']

    # 'perimeter' = lat labels on the left column only, lon labels on the
    # bottom row only (the original notebook's framing); 'all' = every map
    # panel labels its own left/bottom edges, which is what the 3x2 has always
    # done. Only the 2x2 has an unambiguous perimeter (in the 3x2, (c)'s bottom
    # edge is interior to a row whose left panel is the plain-axes scatter), so
    # perimeter mode is restricted to `panels='abcd'`. Default stays 'all' so
    # the published-config renders keep matching the published 3x2's framing,
    # in which every panel labels its own edges.
    gl_labels = gl_labels if gl_labels is not None else 'all'
    if gl_labels not in ('perimeter', 'all'):
        raise ValueError(f"gl_labels={gl_labels!r}; expected 'perimeter' or 'all'")
    if gl_labels == 'perimeter' and nrows != 2:
        raise ValueError("gl_labels='perimeter' is only defined for panels='abcd'")

    sigma = sigma if sigma is not None else load_sigma_patm_std()
    bp_misfit = bp_misfit if bp_misfit is not None else load_bp_misfit_maps(run_dir, time=time)
    bpr, misfit_before, misfit_after = bp_misfit

    # `patm_iternums` only exists because iter0001 has since been purged from
    # the subgyre run on /scratch (only 0 and 20 survive). Every consumer of
    # these knots indexes `ioptim=-1`, i.e. the *last* iteration, so the first
    # entry is inert for the figure -- pass (0, 20) when iter0001 is gone.
    patm_adjustment = (patm_adjustment if patm_adjustment is not None
                        else load_patm_adjustment_knots(run_dir, iternums=patm_iternums))

    # Row 3 only. Guarded so the 'abcd' subset never pays for the slow eta
    # OSSE read (nor requires the eta nature run to be on disk at all).
    if 'e' in panels or 'f' in panels:
        eta_osse = eta_osse if eta_osse is not None else load_eta_osse(run_dir)
        ib_scatter = (ib_scatter if ib_scatter is not None
                      else compute_ib_scatter(eta_osse, patm_adjustment))

    cable_lons, cable_lats = [ds[c].isel(bpr.sensor_args).values for c in ('XC', 'YC')]

    # SPNA projection center, matching smartosse.plot.spna()'s defaults --
    # see fig9_patm_unc.make_fig9 for the same note.
    spna_proj = ccrs.LambertConformal(central_longitude=-35, central_latitude=60)

    fig = plt.figure(figsize=figsize)
    gs = fig.add_gridspec(nrows, 2, hspace=hspace, wspace=wspace)

    ax_a = fig.add_subplot(gs[0, 0], projection=spna_proj)
    ax_b = fig.add_subplot(gs[0, 1], projection=spna_proj)
    ax_c = fig.add_subplot(gs[1, 0], projection=spna_proj)
    ax_d = fig.add_subplot(gs[1, 1], projection=spna_proj)
    ax_e = ax_f = None
    if nrows == 3:
        ax_e = fig.add_subplot(gs[2, 0])                        # IB scatter (plain axes)
        ax_f = fig.add_subplot(gs[2, 1], projection=spna_proj)  # eta skill (map)

    if ax_e is not None and panel_scatter_shrink != 1.:
        # Shrink (e)'s raw gridspec cell *before* plot_ib_scatter's
        # aspect='equal' runs, anchored at the top-left so it stays flush
        # with (c)'s left edge while the (too-tall, colorbar-free) cell's
        # extra height is trimmed off the bottom. Doing this now (vs. after
        # plotting + a forced draw) avoids fighting matplotlib's own
        # aspect/anchor enforcement at the final render pass.
        pos_e = ax_e.get_position()
        new_w = pos_e.width * panel_scatter_shrink
        new_h = pos_e.height * panel_scatter_shrink
        ax_e.set_position([pos_e.x0, pos_e.y1 - new_h, new_w, new_h])

    def _gl_label_args(hide_bottom=False, hide_left=False):
        args = copy.deepcopy(SPNA_GL_ARGS_DEFAULT)
        args['fontsize'] = gl_fontsize
        if hide_bottom:
            args['bottom'] = dict(args['bottom'], hide=True)
        if hide_left:
            args['left'] = dict(args['left'], hide=True)
        return args

    map_axes = tuple(ax for ax in (ax_a, ax_b, ax_c, ax_d, ax_f) if ax is not None)

    if gl_labels == 'perimeter':
        # Perimeter-only framing (the original notebook's: latitudes on the
        # left column, longitudes on the bottom row, nothing on the interior
        # edges) -- so (a) keeps only its lat labels, (b) none, (c) both,
        # (d) only its lon labels.
        gl_by_ax = {ax_a: dict(hide_bottom=True),
                    ax_b: dict(hide_bottom=True, hide_left=True),
                    ax_c: {},
                    ax_d: dict(hide_left=True)}
        for ax in map_axes:
            spna(ax=ax, gl_label_args=_gl_label_args(**gl_by_ax.get(ax, {})))
    else:
        for ax in map_axes:
            spna(ax=ax, gl_label_args=_gl_label_args())

        # (d) sits directly above (f) -- another spatial/lat-lon panel -- so its
        # own bottom (longitude) gridline labels would just duplicate (f)'s top
        # border. Every other map panel keeps spna()'s normal bottom-lon/left-lat
        # framing. Without row 3, (d) is the bottom-right panel and keeps them.
        if ax_f is not None:
            spna(ax=ax_d, gl_label_args=_gl_label_args(hide_bottom=True))

    # (a), (b): misfit maps
    nlev = 27
    cmap_div = Colormaps(nlev).custom_div_cmap()
    mk = dict(plot_type='contourf', vmin=-vmax_misfit, vmax=vmax_misfit, cmap=cmap_div,
              levels=np.linspace(-vmax_misfit, vmax_misfit, nlev - 1))
    _, ax_a, cb_a, _ = ds.plotpc(misfit_before, ax=ax_a, **mk)
    _, ax_b, cb_b, _ = ds.plotpc(misfit_after, ax=ax_b, **mk)

    # (c): dp_atm adjustment
    ck = dict(plot_type='contourf', vmin=-vmax_ctrl, vmax=vmax_ctrl, cmap=cmap_div,
              levels=np.linspace(-vmax_ctrl, vmax_ctrl, nlev - 1))
    ctrl_field = compute_patm_adjustment_field(patm_adjustment, time=time)
    _, ax_c, cb_c, _ = ds.plotpc(ctrl_field, ax=ax_c, **ck)

    # (d): std ratio
    dk = dict(plot_type='contourf', vmin=0, vmax=vmax_ratio, cmap='Greys',
              levels=np.linspace(0, vmax_ratio, nlev - 1))
    ratio_field = compute_patm_std_ratio(patm_adjustment, sigma)
    _, ax_d, cb_d, _ = ds.plotpc(ratio_field, ax=ax_d, **dk)

    for ax in map_axes:
        add_cable_scatter(ax, cable_lons, cable_lats)

    cb_f = None
    if ax_f is not None:
        # (f): eta skill (moved here from (e)'s slot, see module NOTE)
        _, ax_f, cb_f, _ = plot_eta_skill_map(eta_osse, ax=ax_f, vmax=vmax_eta_skill,
                                               nlev=nlev_eta_skill)

    if ax_e is not None:
        # (e): IB scatter (moved here from (f)'s slot, see module NOTE) --
        # aspect_anchor='NW' since this panel now sits in the left column.
        plot_ib_scatter(ax_e, ib_scatter, aspect_anchor='NW')

    axes = dict(a=ax_a, b=ax_b, c=ax_c, d=ax_d, e=ax_e, f=ax_f)
    axes = {k: v for k, v in axes.items() if v is not None}

    for letter, ax in axes.items():
        # (e)'s hexbin fills its own top-left corner with dark viridis, unlike
        # the map panels whose top-left is always land/background -- give
        # just this label a white backing so it stays legible.
        label_kwargs = dict(bbox=dict(facecolor='white', edgecolor='none',
                                       alpha=0.75, pad=2)) if letter == 'e' else {}
        add_panel_label(ax, letter, fontsize=24, **label_kwargs)

    cbar_xlabels = {'a': '', 'b': '', 'c': '[hPa]', 'd': '', 'f': ''}
    # `ratio_cbar_ticks` matters whenever vmax_ratio isn't a round number:
    # style_colorbar's default 3 evenly spaced ticks over (0, vmax_ratio) gives
    # e.g. '0.0255' for the notebook's vmax=0.051.
    cbar_ticks = {'f': eta_skill_cbar_ticks, 'd': ratio_cbar_ticks}
    for letter, cb in zip('abcdf', (cb_a, cb_b, cb_c, cb_d, cb_f)):
        if cb is None:   # (f) absent in the 'abcd' subset
            continue
        style_colorbar(cb, xlabel=cbar_xlabels[letter], labelsize=14,
                        ticks=cbar_ticks.get(letter), decimals=cbar_decimals,
                        height_frac=cbar_height_frac, y_shift_frac=cbar_y_shift_frac)

    return fig, axes


if __name__ == '__main__':
    import argparse

    from ..dataset import open_astedataset
    from .figs_utils import (use_latex_times, use_embedded_pdf_fonts,
                             patch_pdf_indexed_image_bitdepth)

    ap = argparse.ArgumentParser(description='Fig. 10: p_atm mechanism')
    ap.add_argument('--panels', default='abcdef', choices=sorted(PANEL_SETS),
                    help="'abcd' = top 2x2 map panels only (skips the slow "
                         "eta OSSE load); 'abcdef' = full 3x2")
    ap.add_argument('--run-dir', default=RUN_DIR)
    ap.add_argument('--sigma-file', default=None,
                    help='path to a wApressure_*.bin weight binary for panel '
                         "(d)'s sigma_patm; default is fig9_patm_unc's current "
                         'load_sigma_patm_std (the day-to-day prior). Pass the '
                         'sub-daily-std file to match the published Fig. 10')
    ap.add_argument('--vmax-misfit', type=float, default=0.01,
                    help='panel (a)/(b) color limit (symmetric)')
    ap.add_argument('--vmax-ctrl', type=float, default=4.,
                    help='panel (c) color limit [hPa] (symmetric); 0.5 for the '
                         'spread-prior run, whose adjustments are ~8x smaller')
    ap.add_argument('--vmax-ratio', type=float, default=1.,
                    help='panel (d) color limit for std(dp_atm)/sigma_patm')
    ap.add_argument('--ratio-cbar-ticks', type=float, nargs='+', default=None,
                    help='explicit panel (d) colorbar ticks; worth setting '
                         'whenever --vmax-ratio is not a round number')
    ap.add_argument('--figsize', type=float, nargs=2, default=None,
                    metavar=('W', 'H'),
                    help='figure size in inches; default is per --panels (see '
                         'PANEL_SETS). Shrinking H tightens the inter-row gap, '
                         'since the equal-aspect maps fill the cell width and '
                         'leave any leftover cell height as whitespace')
    ap.add_argument('--hspace', type=float, default=0.3,
                    help='gridspec row spacing (fraction of mean axes height)')
    ap.add_argument('--wspace', type=float, default=0.15,
                    help='gridspec column spacing (fraction of mean axes width)')
    ap.add_argument('--cbar-decimals', type=int, default=None,
                    help='fix every colorbar tick label to this many decimal '
                         "places (2 -> '-0.50' rather than '-0.5'); 0 stays '0'")
    ap.add_argument('--gl-labels', default=None, choices=('all', 'perimeter'),
                    help="'perimeter' puts lat labels on the left column and "
                         'lon labels on the bottom row only, with no interior '
                         "ticklabels (--panels abcd only); 'all' (default) "
                         'labels every panel, matching the published 3x2')
    ap.add_argument('--patm-iternums', type=int, nargs=2, default=(0, 20),
                    metavar=('FIRST', 'LAST'),
                    help='xx_apressure.effective iterations to read; only LAST '
                         'is used by any panel. Defaults to (0, 20) because '
                         "iter0001 (make_fig10's own default first entry) is no "
                         'longer on /scratch')
    ap.add_argument('--out-name', default=None,
                    help='basename for the output png/pdf (default: '
                         f'{FIG_NAME}, with a _<panels> suffix for subsets)')
    args = ap.parse_args()

    use_latex_times()
    use_embedded_pdf_fonts()
    # Idempotent no-op on matplotlib >= 3.5; required on this env's 3.4.3 if
    # any panel is rasterized, or the PDF's palette-encoded images won't
    # decode. See figs_utils.patch_pdf_indexed_image_bitdepth's docstring.
    patch_pdf_indexed_image_bitdepth()

    sigma = None
    if args.sigma_file is not None:
        from .fig9_patm_unc import load_sigma_patm
        weight_dir, fname = os.path.split(args.sigma_file)
        sigma = load_sigma_patm(fname, weight_dir=weight_dir)

    ds = open_astedataset()
    fig, _ = make_fig10(ds, run_dir=args.run_dir, panels=args.panels,
                        sigma=sigma, patm_iternums=tuple(args.patm_iternums),
                        vmax_misfit=args.vmax_misfit, vmax_ctrl=args.vmax_ctrl,
                        vmax_ratio=args.vmax_ratio,
                        ratio_cbar_ticks=args.ratio_cbar_ticks,
                        cbar_decimals=args.cbar_decimals,
                        gl_labels=args.gl_labels,
                        figsize=tuple(args.figsize) if args.figsize else None,
                        hspace=args.hspace, wspace=args.wspace)

    name = args.out_name or (FIG_NAME if args.panels == 'abcdef'
                             else f'{FIG_NAME}_{args.panels}')
    os.makedirs(OUT_DIR, exist_ok=True)
    for ext in ('png', 'pdf'):
        # Opaque white, not transparent=True -- see fig5_misfit_rmse_skill's
        # __main__ for why (alpha=0 pinholes along the coastlines render as
        # black blobs on any dark ground).
        fig.savefig(os.path.join(OUT_DIR, f'{name}.{ext}'), dpi=300,
                    bbox_inches='tight', facecolor='white', edgecolor='none')
    print(f'wrote {name}.{{png,pdf}} to {OUT_DIR}')
