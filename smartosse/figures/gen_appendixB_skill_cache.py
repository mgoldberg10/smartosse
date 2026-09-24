"""Precompute the p_b / V_bt skill maps that Appendix B's panel (d) scatters.

Panel (d) of ``figB_patm_std_4panel.py`` is a 1:1 scatter of skill in the
day-to-day-std OSSE against skill in the reanalysis-spread OSSE, over SPNA
grid points, cables pooled. Computing those maps means reading a full month of
``trsp_3d_set1`` (3D, all 6 ASTE tiles, two iterations) per experiment -- ~85 s
each for V_bt and ~30 s each for p_b, so ~12 min for the full 2 runs x 4 cables
x 2 fields sweep. This script does that once and writes the result to
``figures/data/appendixB_skill_maps.nc``; the figure module only reads the cache.

Run as (texlive not needed -- no plotting here):

    conda activate /work2/08381/goldberg/ls6/miniforge3/envs/esmpy_3.10
    cd /work2/08381/goldberg/ls6/smartosse
    python -m smartosse.figures.gen_appendixB_skill_cache

Pass ``--regions labsea northsea`` to redo a subset (the cache is merged with
whatever is already on disk, so re-running for one region leaves the rest
alone -- that is how SPG gets filled in once its rerun lands).

Two deliberate departures from ``smartosse.osse``'s normal path, both forced by
what the reruns actually shipped:

* **p_b is loaded without ``BPReader``.** ``ForecastModel._load_fm_bp`` builds
  one, and ``BPReader.__post_init__`` unconditionally calls ``read_weight()``,
  which needs a ``data.ecco`` in ``iter0000/`` -- the jrastd_daytoday reruns
  have none (they shipped only the bp/diags output, no run-config files). The
  weight is used solely for the cost diagnostics, which skill does not touch,
  so ``load_bp_anom()`` below reproduces the two lines of ``_load_fm_bp`` that
  matter (``m_bpday`` -> anomaly in cm, ``100/9.81 * (x - x.mean('time'))``)
  and skips the reader entirely. Same workaround shape as
  ``fig3_bp_std.load_cable_sensor_lonlat()``, and for the same reason.
* **V_bt, not |V_bt| or U_bt.** Fig. 5 of the manuscript plots the *meridional*
  barotropic velocity skill ("zonal ... not shown but are quantitatively
  comparable"), so panel (d) uses the same component -- ``OSSE.toggle_uv('V')``,
  i.e. ``fldUV[1]``, the north component out of ``UEVNfromUXVY``.

NB the skill here is at **iteration 20**, matching Fig. 9's ``iternum=20``
convention and the only non-zero iteration the std reruns contain. Fig. 5 in
the manuscript is iteration 10. Both axes of panel (d) use iteration 20, so the
comparison is internally consistent; it is just not the same number as Fig. 5.
"""
import argparse
import os
import time

import numpy as np
import pandas as pd
import xarray as xr

from ..utils import read_aste_bin
from ..osse import NatureRun, ForecastModel, OSSE, _compute_skill
from .fig9_patm_unc import REGIONS, RUN_DIR_ROOT_STD, RUN_DIR_ROOT_SPREAD

# The barotropic-velocity nature run (ASTE-tiled U_bt.nc/V_bt.nc). NatureRun's
# own default nr_dir is the phibot_daily directory, which has no *_bt.nc.
NR_BT_DIR = '/work2/08381/goldberg/ls6/aste_270x450x180/NR_baro_vel/'

DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
SKILL_CACHE = os.path.join(DATA_DIR, 'appendixB_skill_maps.nc')

RUN_ROOTS = {'std': RUN_DIR_ROOT_STD, 'spread': RUN_DIR_ROOT_SPREAD}
FLDS = ('bp', 'Vbt')
ITERNUMS = (0, 20)
MO_STR = '201201'


def month_datetimes(mo_str=MO_STR):
    start = pd.to_datetime(mo_str, format='%Y%m')
    return pd.date_range(start=start, end=start + pd.offsets.MonthEnd(1), freq='D')


def available_regions(run_root, regions=REGIONS, iternums=ITERNUMS):
    """Regions under `run_root` that have every iteration directory present.

    The jrastd_daytoday rerun set is missing `subgyre/` entirely (as of
    2026-08-11), so the sweep has to skip what isn't there rather than crash.
    """
    out = []
    for region in regions:
        if all(os.path.isdir(f'{run_root.rstrip("/")}/{region}/iter{it:04d}')
               for it in iternums):
            out.append(region)
    return out


def load_bp_anom(run_dir, iternums=ITERNUMS, datetimes=None):
    """m_bpday anomaly [cm], dims (ioptim, time, tile, j, i) -- BPReader-free.

    Equivalent to ``ForecastModel(fld_type='bp').fld`` (see module docstring for
    why that path can't be used on the std reruns).
    """
    datetimes = month_datetimes() if datetimes is None else datetimes
    das = []
    for it in iternums:
        fname = f'{run_dir.rstrip("/")}/iter{it:04d}/m_bpday.{it:010d}.data'
        da = read_aste_bin(fname, var_name='m_bpday').rename({'k': 'time'})
        das.append(da.isel(time=slice(0, len(datetimes))))
    da = xr.concat(das, dim='ioptim')
    da = da.assign_coords(time=('time', pd.DatetimeIndex(datetimes)))
    return 100 / 9.81 * (da - da.mean('time'))


def compute_skill_map(run_root, region, fld, nr, datetimes=None, iternums=ITERNUMS):
    """Skill map (tile, j, i) for one experiment and one field."""
    datetimes = month_datetimes() if datetimes is None else datetimes
    run_dir = f'{run_root.rstrip("/")}/{region}/'

    if fld == 'bp':
        fm_fld = load_bp_anom(run_dir, iternums=iternums, datetimes=datetimes)
        nr_fld = (nr.fld_full
                  .sel(time=slice(datetimes[0], datetimes[-1]))
                  .resample(time='1D').mean())
        return _compute_skill(fm_fld, nr_fld)

    if fld == 'Vbt':
        fm = ForecastModel(run_dir, iternums=list(iternums), datetimes=datetimes,
                           fld_type='bt')
        osse = OSSE(fm, nr)
        osse.toggle_uv('V')       # meridional component, as in manuscript Fig. 5
        return osse.fld_skill

    raise ValueError(f'unknown fld {fld!r}')


def build_cache(regions=REGIONS, flds=FLDS, runs=tuple(RUN_ROOTS), out_path=SKILL_CACHE,
                iternums=ITERNUMS, mo_str=MO_STR):
    """Compute every (run, region, fld) skill map and merge into `out_path`.

    Returns the merged Dataset. Variables are named ``skill_<fld>`` with dims
    (run, region, tile, j, i); missing experiments are NaN, so a later run of
    this script for the missing region fills them in without disturbing the rest.
    """
    datetimes = month_datetimes(mo_str)

    # One NatureRun per field, reused across every experiment (this is what
    # MultiOSSE exists for, but its add_forecast_model() goes through
    # ForecastModel for p_b too, which we can't use here).
    nrs = {}
    if 'bp' in flds:
        t0 = time.time()
        nrs['bp'] = NatureRun(fld_type='bp')
        print(f'[NR] bp loaded in {time.time() - t0:.1f}s', flush=True)
    if 'Vbt' in flds:
        t0 = time.time()
        nrs['Vbt'] = NatureRun(fld_type='bt', nr_dir=NR_BT_DIR)
        print(f'[NR] bt loaded in {time.time() - t0:.1f}s', flush=True)

    maps = {fld: {} for fld in flds}
    for run in runs:
        root = RUN_ROOTS[run]
        present = available_regions(root, regions, iternums)
        missing = [r for r in regions if r not in present]
        if missing:
            print(f'[{run}] SKIPPING (no run directory): {", ".join(missing)}', flush=True)
        for region in present:
            for fld in flds:
                t0 = time.time()
                skill = compute_skill_map(root, region, fld, nrs[fld],
                                          datetimes=datetimes, iternums=iternums)
                maps[fld][(run, region)] = skill.compute()
                print(f'[{run}/{region}/{fld}] mean={float(skill.mean()):+.4f} '
                      f'({time.time() - t0:.0f}s)', flush=True)

    ds = _assemble(maps, runs, regions)

    # Merge with whatever is already cached so a one-region re-run doesn't
    # discard the others (see the --regions note in the module docstring).
    if os.path.exists(out_path):
        with xr.open_dataset(out_path) as old:
            old = old.load()
        # combine_first outer-joins on run/region and prefers this run's values
        # wherever they aren't NaN, so a --regions subset extends the cache.
        ds = ds.combine_first(old)

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    ds.attrs.update(
        iternums=str(list(iternums)),
        mo_str=mo_str,
        run_dir_root_std=RUN_DIR_ROOT_STD,
        run_dir_root_spread=RUN_DIR_ROOT_SPREAD,
        nr_bt_dir=NR_BT_DIR,
        note='skill = 1 - rms_after/rms_before, per grid point; Vbt is the '
             'meridional (north) barotropic velocity component',
    )
    ds.to_netcdf(out_path)
    print('wrote', out_path, flush=True)
    return ds


def _assemble(maps, runs, regions):
    """{fld: {(run, region): DataArray}} -> Dataset[skill_<fld>](run, region, tile, j, i)."""
    data_vars = {}
    for fld, entries in maps.items():
        if not entries:
            continue
        template = next(iter(entries.values()))
        # Drop the mds-derived coords (XC/YC/hFacC/...) -- they differ between
        # the bp and bt paths and would collide on merge; the figure module
        # takes the grid from open_astedataset() instead.
        template = template.drop_vars(template.coords, errors='ignore')
        blank = xr.full_like(template, np.nan)

        stacked = []
        for run in runs:
            per_region = []
            for region in regions:
                da = entries.get((run, region))
                da = blank if da is None else da.drop_vars(da.coords, errors='ignore')
                per_region.append(da)
            stacked.append(xr.concat(per_region, dim=xr.DataArray(list(regions), dims='region')))
        data_vars[f'skill_{fld}'] = xr.concat(
            stacked, dim=xr.DataArray(list(runs), dims='run'))
    return xr.Dataset(data_vars)


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--regions', nargs='+', default=list(REGIONS))
    ap.add_argument('--flds', nargs='+', default=list(FLDS), choices=list(FLDS))
    ap.add_argument('--runs', nargs='+', default=list(RUN_ROOTS), choices=list(RUN_ROOTS))
    ap.add_argument('--out', default=SKILL_CACHE)
    args = ap.parse_args()

    build_cache(regions=tuple(args.regions), flds=tuple(args.flds),
                runs=tuple(args.runs), out_path=args.out)
