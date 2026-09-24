"""SMART-cable vs GRACE annual OSSE -- monthly :math:`p_b` skill, side by side.

Port of ``smart_cables/osse/grace_llc4320_year_clean.ipynb`` (cells 42-47, the
cell that writes ``smart_day_skill_grace_mo_skill.png``) onto this package's
figure conventions.

The point of the pair is that the two OSSEs assimilate *different observing
systems over the same year*, and are compared at the **same effective temporal
resolution**:

    (a) **SPNA_cable_annual** -- the cable run assimilates DAILY OBP along the
        cable (``m_bpday``). Its skill map is nevertheless computed from
        MONTHLY MEANS of those daily fields, so that it answers the same
        question panel (b) does: how much of the *month-to-month* OBP
        variability does the OSSE recover? (This is why the figure filename
        says "smart_day_skill": the *assimilation* is daily, the *scoring* is
        monthly. Skill scored on the daily fields is a different, larger
        number and is not what this figure shows.)
    (b) **GRACE_annual** -- the GRACE-equivalent run assimilates MONTHLY OBP
        over the whole domain (``m_bpmon``), and is scored on those monthly
        fields directly.

Skill is ``smartosse.osse._compute_skill``'s definition throughout, unchanged::

    s = 1 - rms(p_b^N - p_b^NR) / rms(p_b^0 - p_b^NR)

per grid point, over the monthly samples, with time means removed -- so a
positive value means the optimized run tracks the nature run's month-to-month
OBP better than the first guess did.

Panel (a) additionally carries the cable's 157 sensor locations (white circles)
and the :math:`f/H = 10^{-7}` contour, exactly as the notebook drew them; panel
(b) carries neither, since the GRACE observing system is the whole domain.

Both panels are now live. The GRACE-equivalent counterpart of the
reanalysis-spread cable run finished on 2026-08-17 and is the `GRACE_RUN_DIR`
below (``..._gracellc4320_spread/2012/fullnatl/``, iterations 0 and 2, 13
``m_bpmon`` records). It is the run that belongs next to this panel (a): same
reanalysis-spread :math:`p_{atm}` uncertainty, same year, same NR -- only the
observing system differs. The older non-spread ``..._gracellc4320/2012/`` is the
one the notebook used and pairs with the older non-spread cable run; pass it via
``--grace-run-dir`` if you want to compare against the notebook's panel (b).
`compute_grace_skill` still returns None, and the module still renders an empty
decorated map, if a run directory has no iteration subdirectories.

Two departures from the notebook, both deliberate
-------------------------------------------------
* **The nature run stops on 2012-11-15, so November is dropped by default.**
  ``phibot_daily`` covers 2011-09-13 to 2012-11-15, while the FM writes 367
  daily records (2012-01-01 .. 2013-01-01). A plain ``resample('1M')`` on each
  side therefore builds a November NR mean from 15 days and a November FM mean
  from 30, and compares them as if they were the same quantity -- which is what
  the notebook did. `complete_months_only=True` (the default here) keeps only
  the months the NR covers in full, i.e. Jan-Oct 2012, ten samples. This is not
  cosmetic: the two skill maps correlate at only 0.84. Pass ``--all-months``
  to reproduce the notebook's exact numbers.
* **``BPReader`` is bypassed** (``load_bp_anom`` from
  ``gen_appendixB_skill_cache``, ``load_bpmon_anom`` here): ``BPReader``'s
  constructor reads ``data.ecco``/the weight file out of ``iter0000/``, and the
  spread run's directory holds only ``m_bpday`` + ``costfunction``. The two
  lines that matter -- read the binary, convert to a cm anomaly via
  ``100/9.81 * (x - x.mean('time'))`` -- are reproduced directly. Same
  workaround, and the same reason, as ``gen_appendixB_skill_cache`` and
  ``fig3_bp_std.load_cable_sensor_lonlat``. The cable's sensor lon/lats come
  from `SENSOR_RUN_DIR`, the matching non-spread cable run, which is the
  nearest run that still ships a ``data.ecco`` (the sensor mask is the same
  static ``/work`` binary in both, 157 sensors -- cross-checked against
  ``fig1_global_cables.load_partial_cables()``).

How to run
----------
::

    module load texlive
    conda activate /work2/08381/goldberg/ls6/miniforge3/envs/esmpy_3.10
    cd /work2/08381/goldberg/ls6/smartosse
    python -m smartosse.figures.fig8_smart_grace_mo_skill
    python -m smartosse.figures.fig8_smart_grace_mo_skill --rebuild     # redo cache
    python -m smartosse.figures.fig8_smart_grace_mo_skill --all-months  # notebook's

    # tighter color scale, only the round ticks labelled (both panels):
    python -m smartosse.figures.fig8_smart_grace_mo_skill \
        --vmax 0.075 --ticks -0.05 0 0.05 \
        --fig-name smart_day_skill_grace_mo_skill_vmax075

Writes ``output/smart_day_skill_grace_mo_skill.{png,pdf}`` and the cache
``data/smart_grace_mo_skill.nc``.
"""
import argparse
import os
import re
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cmocean

from ..utils import read_aste_bin, get_fH
from ..cmaps import Colormaps
from ..osse import NatureRun, _compute_skill
from ..plot import llc_map, spna, retain_only_perimiter_gl_labels
from ..dataset import open_astedataset
from .figs_utils import add_panel_label, add_cable_scatter
from .gen_appendixB_skill_cache import load_bp_anom

# =============================================================================
# Config
# =============================================================================

GRID_DIR = '/work/08381/goldberg/ls6/aste_270x450x180/GRID_noblank_real4/'

# (a) SPNA_cable_annual, reanalysis-spread p_atm uncertainty. Daily m_bpday,
# iterations 0 and 2 (this run stopped at 2 -- see grace_equivalent_osse.tex on
# why 3 iterations is enough, and si_skill_over_optim.py for the evidence).
RUN_DIR_CABLE = ('/scratch/08381/goldberg/aste_270x450x180/osses/'
                 'runc68v_froman_natl_1month_alldailyxx_gracellc4320_sc_spread/'
                 '2012/fullnatl/')
ITERNUMS_CABLE = (0, 2)

# (b) GRACE_annual, the spread counterpart of RUN_DIR_CABLE. Monthly m_bpmon
# (13 records: the 12 months of 2012 plus the FM's trailing partial), iterations
# 0 and 2, matching ITERNUMS_CABLE. The older non-spread run,
# '..._gracellc4320/2012/', is the one the notebook used and can still be passed
# via --grace-run-dir.
GRACE_RUN_DIR = ('/scratch/08381/goldberg/aste_270x450x180/osses/'
                 'runc68v_froman_natl_1month_alldailyxx_gracellc4320_spread/'
                 '2012/fullnatl/')
ITERNUMS_GRACE = (0, 2)

# Sensor locations only -- no run output is read from here. The spread run's
# directory holds no data.ecco; this is the same cable, same gencost input file
# (a symlink into /work, so purge-proof), 157 sensors.
SENSOR_RUN_DIR = ('/scratch/08381/goldberg/aste_270x450x180/osses/'
                  'runc68v_froman_natl_1month_alldailyxx_gracellc4320_sc/2012/')
SENSOR_BAD_VALS = (0., -9999.)

# The FM's own record calendar: 367 daily records, 2012-01-01 .. 2013-01-01
# (the notebook's `start + YearEnd(1) + 1 day`). The NR runs out on 2012-11-15;
# `complete_months_only` is what deals with that, not this range.
YEAR = '2012'

DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
OUT_DIR = os.path.join(os.path.dirname(__file__), 'output')
CACHE = os.path.join(DATA_DIR, 'smart_grace_mo_skill.nc')
FIG_NAME = 'smart_day_skill_grace_mo_skill'

# Color scale -- the notebook's, unchanged, and shared by both panels (that is
# the whole point of the pair, so it is not a per-panel knob). 18 filled levels
# over +/-0.1 with contourf's extend='both' showing what runs over.
VMAX_SKILL = 0.1
NLEV = 18
CBAR_NTICKS = 5
# Explicit colorbar ticks; None means CBAR_NTICKS evenly spaced over +/-vmax.
# Set (or pass --ticks) when the round numbers you want to label are not the
# ones a linspace over vmax lands on -- e.g. the vmax=0.075 variant labels only
# -0.05, 0, 0.05, since +/-0.075 is not a number worth printing.
CBAR_TICKS = None

# f/H contour on panel (a): the single 1e-7 s^-1 m^-1 line, the notebook's
# `fH_levels = [1e-7]`. Drawn from the RAW f/H, i.e. with Depth = 0 on land
# giving f/H = inf, which is why the contour also traces coastlines -- that is
# how the published panel looks and it is left alone here.
FH_LEVELS = (1e-7,)
FH_LINEWIDTH = 1
FH_COLOR = 'k'

CABLE_SCATTER_KWARGS = dict(s=10, edgecolor='k', facecolor='w')

# llc_map regrid resolution: 0.25 deg is finer than ASTE-270 in the SPNA, so
# the draw does not smooth the field (as in advfw_skill_maps/si_skill_over_optim).
REGRID_DX = 0.25

FIGSIZE = (20, 6)
PANEL_LABEL_FONTSIZE = 30
CBAR_RECT = (0.165, -0.10, 0.70, 0.065)   # figure fraction (x0, y0, w, h)
CBAR_TICK_LABELSIZE = 30


# =============================================================================
# Loaders
# =============================================================================

def year_datetimes(year=YEAR):
    """The FM's 367 daily record timestamps, 2012-01-01 .. 2013-01-01.

    Reproduces the notebook's ``start + YearEnd(1) + 1 day`` end date, which is
    what makes the count match ``m_bpday``'s ``nrecords = 367``.
    """
    start = pd.to_datetime(year, format='%Y')
    end = start + pd.offsets.YearEnd(1) + pd.Timedelta(days=1)
    return pd.date_range(start=start, end=end, freq='D')


def load_bpmon_anom(run_dir, iternums=ITERNUMS_GRACE, datetimes=None):
    """``m_bpmon`` anomaly [cm], dims (ioptim, time, tile, j, i) -- BPReader-free.

    The monthly analogue of ``gen_appendixB_skill_cache.load_bp_anom``, and the
    same two lines the notebook's cell 3 spells out: read the binary, rename its
    record axis to ``time``, convert to an equivalent-water-height anomaly in cm.

    `datetimes` are the month labels; if None they are taken as the month ENDS
    of `YEAR`, matching what ``resample(time='1M')`` produces on the cable side
    so the two are directly comparable.
    """
    if datetimes is None:
        datetimes = pd.date_range(start=f'{YEAR}-01-01', periods=12, freq='M')
    das = []
    for it in iternums:
        fname = f'{run_dir.rstrip("/")}/iter{it:04d}/m_bpmon.{it:010d}.data'
        da = read_aste_bin(fname, var_name='m_bpmon').rename({'k': 'time'})
        das.append(da.isel(time=slice(0, len(datetimes))))
    da = xr.concat(das, dim='ioptim')
    da = da.assign_coords(time=('time', pd.DatetimeIndex(datetimes)))
    return 100 / 9.81 * (da - da.mean('time'))


def load_cable_sensor_lonlat(ds, run_dir=SENSOR_RUN_DIR, iternum=0,
                             bad_vals=SENSOR_BAD_VALS):
    """Cable sensor lon/lat from the OSSE's ``gencost_datafile(1)`` binary.

    Same recovery as ``fig3_bp_std.load_cable_sensor_lonlat`` (and the same
    reason for not building a ``BPReader``), but that one hardcodes a run dir
    whose gencost file is the 31-record January mask; this reads the annual
    run's own 370-record file. The sensor mask is constant in time, so record 0
    is enough. Returns 157 points for the full SPNA cable.
    """
    iter_dir = Path(run_dir) / f'iter{iternum:04d}'
    data_ecco = iter_dir / 'data.ecco'
    match = re.search(r"gencost_datafile\s*\(\s*1\s*\)\s*=\s*'([^']+)'",
                      data_ecco.read_text())
    if match is None:
        raise ValueError(f'Could not find gencost_datafile(1) in {data_ecco}')

    da = read_aste_bin(str(iter_dir / match.group(1)))[0]
    tile, j, i = np.where(~np.isin(da.values, bad_vals))
    sensor_args = {d: xr.DataArray(v, dims='sensor')
                   for d, v in zip(('tile', 'j', 'i'), (tile, j, i))}
    lons, lats = (ds[coord].isel(sensor_args).values for coord in ('XC', 'YC'))
    return lons, lats


# =============================================================================
# Skill
# =============================================================================

def nr_monthly(nr, datetimes, complete_months_only=True, min_days=28):
    """NR OBP resampled to monthly means, with the short tail month optional.

    Returns ``(nr_mo, ndays)`` where `ndays` counts the NR daily samples that
    went into each monthly mean. ``phibot_daily`` ends 2012-11-15, so the last
    month is built from 15 days; comparing that against a full-month FM mean is
    comparing two different quantities, hence `complete_months_only`. See the
    module docstring for why the default is True and what it costs.
    """
    daily = (nr.fld_full
             .sel(time=slice(datetimes[0], datetimes[-1]))
             .resample(time='1D').mean())
    nr_mo = daily.resample(time='1M').mean('time').compute()

    # Count on a single column: the NR has no per-cell time gaps, only the
    # domain-wide truncation at 2012-11-15.
    ndays = (daily.isel(tile=0, j=0, i=0).notnull()
             .resample(time='1M').sum().compute())
    ndays = xr.DataArray(np.asarray(ndays.values), dims='time',
                         coords={'time': nr_mo.time})

    if complete_months_only:
        keep = ndays >= min_days
        dropped = nr_mo.time.values[~keep.values]
        if len(dropped):
            print('[skill] dropping partial NR month(s): '
                  + ', '.join(f'{pd.Timestamp(t):%Y-%m} ({int(n)} d)'
                              for t, n in zip(dropped, ndays.values[~keep.values])),
                  flush=True)
        nr_mo = nr_mo.sel(time=keep)
        ndays = ndays.sel(time=keep)

    return nr_mo, ndays


def compute_cable_skill(run_dir=RUN_DIR_CABLE, iternums=ITERNUMS_CABLE, nr=None,
                        datetimes=None, complete_months_only=True):
    """Panel (a): monthly-mean skill of the daily-assimilating cable OSSE.

    Daily ``m_bpday`` anomalies are averaged to months FIRST, then scored --
    this is the notebook's cells 42-43 and the reason the panel is comparable to
    the monthly GRACE panel at all.
    """
    datetimes = year_datetimes() if datetimes is None else datetimes
    nr = NatureRun(fld_type='bp') if nr is None else nr

    nr_mo, _ = nr_monthly(nr, datetimes, complete_months_only=complete_months_only)
    fm_mo = (load_bp_anom(run_dir, iternums=iternums, datetimes=datetimes)
             .resample(time='1M').mean('time').compute())
    return _compute_skill(fm_mo.sel(time=nr_mo.time), nr_mo)


def compute_grace_skill(run_dir=GRACE_RUN_DIR, iternums=ITERNUMS_GRACE, nr=None,
                        datetimes=None, complete_months_only=True):
    """Panel (b): monthly skill of the GRACE-equivalent OSSE, or None.

    Returns None (and says so) when `run_dir` has no iteration directories, so
    that a run dir that is not there yet degrades to a blank panel rather than
    an error. Otherwise this is the notebook's cell 40: read ``m_bpmon`` for the
    first and last iteration, label its records with the NR's month ends, score
    against the NR monthly means.
    """
    datetimes = year_datetimes() if datetimes is None else datetimes

    missing = [it for it in iternums
               if not os.path.isdir(f'{run_dir.rstrip("/")}/iter{it:04d}')]
    if missing:
        print(f'[skill] GRACE run not available ({run_dir}): no iter'
              f'{missing[0]:04d}/ -- panel (b) will be blank', flush=True)
        return None

    nr = NatureRun(fld_type='bp') if nr is None else nr
    nr_mo, _ = nr_monthly(nr, datetimes, complete_months_only=complete_months_only)

    # m_bpmon's records are month means in FM order; label them with the FULL
    # month-end calendar, then select the NR's months -- so dropping the NR's
    # partial month drops the same month here rather than shifting the labels.
    all_months = pd.date_range(start=datetimes[0], end=datetimes[-1], freq='M')
    fm_mo = load_bpmon_anom(run_dir, iternums=iternums, datetimes=all_months)
    return _compute_skill(fm_mo.sel(time=nr_mo.time), nr_mo)


def build_cache(out_path=CACHE, run_dir=RUN_DIR_CABLE, grace_run_dir=GRACE_RUN_DIR,
                iternums_cable=ITERNUMS_CABLE, iternums_grace=ITERNUMS_GRACE,
                complete_months_only=True):
    """Compute both skill maps once and cache them.

    Variables: ``skill_cable`` always, ``skill_grace`` only when the GRACE run
    exists -- so a later rebuild, once it does, adds the second panel without
    touching the first.
    """
    datetimes = year_datetimes()
    nr = NatureRun(fld_type='bp')   # loaded once, used by both panels

    data_vars = {}
    cable = compute_cable_skill(run_dir=run_dir, iternums=iternums_cable, nr=nr,
                                datetimes=datetimes,
                                complete_months_only=complete_months_only)
    data_vars['skill_cable'] = cable.reset_coords(drop=True)
    print(f'[skill] cable  mean={float(cable.mean()):+.4f}  '
          f'median={float(cable.median()):+.4f}', flush=True)

    grace = compute_grace_skill(run_dir=grace_run_dir, iternums=iternums_grace,
                                nr=nr, datetimes=datetimes,
                                complete_months_only=complete_months_only)
    if grace is not None:
        data_vars['skill_grace'] = grace.reset_coords(drop=True)
        print(f'[skill] grace  mean={float(grace.mean()):+.4f}  '
              f'median={float(grace.median()):+.4f}', flush=True)

    ds = xr.Dataset(data_vars)
    ds.attrs.update(
        note=('skill = 1 - rms_after/rms_before on time-mean-removed MONTHLY '
              'series (smartosse.osse._compute_skill); the cable OSSE '
              'assimilates daily OBP but is scored on monthly means'),
        run_dir_cable=run_dir,
        grace_run_dir=grace_run_dir,
        iternums_cable=str(list(iternums_cable)),
        iternums_grace=str(list(iternums_grace)),
        complete_months_only=str(complete_months_only),
    )
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    ds.to_netcdf(out_path)
    print('wrote', out_path, flush=True)
    return ds


# =============================================================================
# Plotting
# =============================================================================

def skill_cmap(nlev=NLEV):
    """The package's standard skill colormap: white-centered ``cmocean curl_r``.

    Same construction as ``osse._plot_skill`` and ``si_skill_over_optim``, so
    these panels sit directly next to manuscript Fig. 5's.
    """
    return Colormaps(nlev).custom_div_cmap(template_cmap=cmocean.cm.curl_r)


def draw_skill_map(ax, field2d, lon2d, lat2d, vmax=VMAX_SKILL, nlev=NLEV, cmap=None):
    """Filled-contour one regridded skill map onto a decorated GeoAxes."""
    cmap = skill_cmap(nlev) if cmap is None else cmap
    cs = ax.contourf(lon2d, lat2d, field2d,
                     levels=np.linspace(-vmax, vmax, nlev),
                     cmap=cmap, vmin=-vmax, vmax=vmax, extend='both',
                     transform=ccrs.PlateCarree(), transform_first=True,
                     zorder=0)
    # Rasterize the fill: a 1440x720 filled-contour field is ~9 MB of vector
    # output per panel for a dense colour field with no line art in it.
    # Per-collection because matplotlib 3.4's ContourSet is not an Artist, so
    # `rasterized=` passed to contourf is silently dropped (as in
    # si_skill_over_optim.draw_skill_map / advfw_skill_maps.draw_map).
    for coll in cs.collections:
        coll.set_rasterized(True)
    return cs


def draw_fH_contour(ax, fH2d, lon2d, lat2d, levels=FH_LEVELS,
                    color=FH_COLOR, linewidth=FH_LINEWIDTH):
    """The f/H = 1e-7 line over panel (a). NOT rasterized -- it is line art."""
    return ax.contour(lon2d, lat2d, fH2d, levels=list(levels), colors=color,
                      linewidths=linewidth, transform=ccrs.PlateCarree(),
                      transform_first=True, zorder=3)


def make_fig(cache, ds, lm=None, vmax=VMAX_SKILL, nlev=NLEV, figsize=FIGSIZE,
             cable_lonlat=None, show_fH=True, placeholder_text=None,
             ticks=CBAR_TICKS,
             cbar_rect=CBAR_RECT, verbose=True):
    """The 1x2 figure: (a) cable monthly skill, (b) GRACE monthly skill.

    `cache` is `build_cache`'s Dataset; a missing ``skill_grace`` renders panel
    (b) as an empty decorated map (its frame, land and gridlines only), which is
    now only a fallback for a cache built without a GRACE run.
    `placeholder_text`, if given, is written across that empty panel -- left
    None so the panel is genuinely blank, since anything drawn there would have
    to be removed again before the figure goes in the manuscript.

    Everything is a small function over already-loaded data, so a notebook can
    load the cache once and iterate on layout.
    """
    lm = lm or llc_map(ds, dx=REGRID_DX, dy=REGRID_DX)
    lon2d, lat2d = lm.new_grid_lon, lm.new_grid_lat

    fig, axes, gl_list = spna(1, 2, figsize=figsize, return_gl=True)

    # -- (a) cable ------------------------------------------------------------
    ax = axes[0]
    mesh = draw_skill_map(ax, lm.regrid(cache['skill_cable']), lon2d, lat2d,
                          vmax=vmax, nlev=nlev)
    if show_fH:
        f, H = get_fH(ds)
        draw_fH_contour(ax, lm.regrid(f / H), lon2d, lat2d)
    if cable_lonlat is None:
        cable_lonlat = load_cable_sensor_lonlat(ds)
    add_cable_scatter(ax, *cable_lonlat, zorder=4, **CABLE_SCATTER_KWARGS)

    # -- (b) GRACE ------------------------------------------------------------
    ax = axes[1]
    if 'skill_grace' in cache:
        draw_skill_map(ax, lm.regrid(cache['skill_grace']), lon2d, lat2d,
                       vmax=vmax, nlev=nlev)
    elif placeholder_text:
        ax.text(0.5, 0.5, placeholder_text, transform=ax.transAxes, ha='center',
                va='center', fontsize=22, color='0.35', style='italic', zorder=5)

    for ax, letter in zip(axes, 'ab'):
        add_panel_label(ax, letter, fontsize=PANEL_LABEL_FONTSIZE, x=0.02, y=0.97)

    # Latitude labels on the left panel only (the notebook hid the 'N' labels on
    # axes[1] by hand; this is the package's general version of that).
    fig.canvas.draw()
    retain_only_perimiter_gl_labels(np.array([axes]), gl_list)

    ticks = (np.linspace(-vmax, vmax, CBAR_NTICKS) if ticks is None
             else np.asarray(ticks, float))
    cb = fig.colorbar(mesh, cax=fig.add_axes(list(cbar_rect)),
                      orientation='horizontal')
    cb.set_ticks(ticks)
    cb.set_ticklabels([f'{t:.2f}' for t in ticks])
    cb.ax.tick_params(labelsize=CBAR_TICK_LABELSIZE, length=10, width=2)

    if verbose:
        # Wet points only. ~35% of the ASTE-270 array is land, where the skill
        # is an exact 0 that _compute_skill never touched; averaging those in
        # pulls every statistic toward zero and makes the two panels look
        # weaker (and more alike) than they are. The plotted field is
        # unaffected -- this is the printout only.
        wet = (ds['Depth'] > 0).values
        for name, label in (('skill_cable', 'cable'), ('skill_grace', 'grace')):
            if name not in cache:
                print(f'[fig] {label}: BLANK (no data)', flush=True)
                continue
            v = np.asarray(cache[name].values, float)
            v = v[wet & np.isfinite(v)]
            frac = float(np.mean(np.abs(v) > vmax))
            print(f'[fig] {label}: mean={v.mean():+.4f} '
                  f'median={np.median(v):+.4f} '
                  f'p98|s|={np.quantile(np.abs(v), 0.98):.3f} '
                  f'{100 * np.mean(v > 0):.0f}% of wet points improved, '
                  f'{100 * frac:.1f}% beyond +/-{vmax}', flush=True)

    return fig, axes


# =============================================================================
if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--run-dir', default=RUN_DIR_CABLE,
                    help='cable OSSE run directory (panel a)')
    ap.add_argument('--grace-run-dir', default=GRACE_RUN_DIR,
                    help='GRACE OSSE run directory (panel b); blank if absent')
    ap.add_argument('--cable-iters', type=int, nargs='+', default=list(ITERNUMS_CABLE),
                    help='cable iterations to score, first=guess last=optimized '
                         f'(default {list(ITERNUMS_CABLE)})')
    ap.add_argument('--grace-iters', type=int, nargs='+', default=list(ITERNUMS_GRACE),
                    help='GRACE iterations to score, first=guess last=optimized '
                         f'(default {list(ITERNUMS_GRACE)})')
    ap.add_argument('--all-months', action='store_true',
                    help="keep the NR's partial final month, as the notebook did")
    ap.add_argument('--rebuild', action='store_true', help='recompute the cache')
    ap.add_argument('--out', default=CACHE)
    ap.add_argument('--vmax', type=float, default=VMAX_SKILL,
                    help='color-scale half-range, shared by both panels '
                         f'(default {VMAX_SKILL})')
    ap.add_argument('--ticks', type=float, nargs='+', default=CBAR_TICKS,
                    help='explicit colorbar ticks; default is '
                         f'{CBAR_NTICKS} evenly spaced over +/-vmax')
    ap.add_argument('--fig-name', default=FIG_NAME,
                    help=f'output basename, no extension (default {FIG_NAME})')
    args = ap.parse_args()

    from .figs_utils import (use_latex_times, use_embedded_pdf_fonts,
                             patch_pdf_indexed_image_bitdepth)

    use_latex_times()
    use_embedded_pdf_fonts()
    # This module rasterizes the contourf fills, so on matplotlib < 3.5 the PDF
    # needs this or its palette-encoded panels are undecodable and the file
    # opens blank/"damaged" (STATUS.md 2026-08-14; fig6_regions_skill_bp_uvbt).
    patch_pdf_indexed_image_bitdepth()

    if args.rebuild or not os.path.exists(args.out):
        cache = build_cache(out_path=args.out, run_dir=args.run_dir,
                            grace_run_dir=args.grace_run_dir,
                            iternums_cable=tuple(args.cable_iters),
                            iternums_grace=tuple(args.grace_iters),
                            complete_months_only=not args.all_months)
    else:
        cache = xr.open_dataset(args.out).load()
        print(f'loaded cache {args.out} (--rebuild to recompute)', flush=True)

    ds = open_astedataset(GRID_DIR, grid_dir=GRID_DIR, iters=None)
    fig, axes = make_fig(cache, ds, vmax=args.vmax, ticks=args.ticks)

    # Opaque white, not transparent=True: the land polygons and the regridded
    # field don't tile the map exactly, and a transparent save leaves alpha=0
    # pinholes along every coastline that composite to black speckles on a dark
    # ground (STATUS.md 2026-08-14; fig6_regions_skill_bp_uvbt.save_fig).
    os.makedirs(OUT_DIR, exist_ok=True)
    for ext in ('png', 'pdf'):
        fig.savefig(os.path.join(OUT_DIR, f'{args.fig_name}.{ext}'), dpi=300,
                    bbox_inches='tight', facecolor='white', edgecolor='none')
    print(f'wrote {args.fig_name}.{{png,pdf}} to {OUT_DIR}')
