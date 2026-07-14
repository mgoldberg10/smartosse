"""
Generate the p_atm uncertainty fields used by Fig. 9 (a)/(b), on their native
JRA55 lat/lon grid -- meant to be plotted directly (contourf + PlateCarree),
unlike the ASTE-gridded `wApressure_*.bin` weight files (`w = sigma^-2`,
regridded onto the ASTE curvilinear grid via MITgcm's EXF) that are what
actually get fed into the OSSEs as control-uncertainty priors. Those don't
make good plots (grid artifacts, sparse regridding). This script instead
reproduces the two fields as computed directly from the reanalysis products,
before ASTE regridding -- same recipe as patm.ipynb (STD) and
test_chaudhuri_uncertainty.ipynb (SPREAD, see also
input_weight/chaudhuri_method/readme.txt).

Run with:
    conda activate /work/08381/goldberg/ls6/miniforge3/envs/esmpy_3.10
    python -m smartosse.figures.gen_patm_uncertainty_fields

Writes sigma_patm_std_<year>.nc and sigma_patm_spread_<year>.nc (both [lat,
lon], units Pa) to OUT_DIR.

IMPORTANT (lon dealiasing -- a correctness fix, not a cosmetic one):
`load_forcing_generic` builds each product's lon coordinate as
`np.sort((lon_raw + 180) % 360 - 180)`. The `%360-180` remap makes the raw
0..360 axis wrap around 180, so it is no longer monotonic; `np.sort()` then
reorders the *coordinate labels* back to ascending order but does NOT
reorder the underlying *data* columns to match, leaving every field from
that loader silently misaligned by a fixed cyclic shift along lon. Rolling
the data (not the coords) by half the lon axis length undoes exactly this,
since the wrap always falls at the grid's antimeridian crossing (lon_raw ==
180), i.e. the midpoint of an even-length axis.

This is the same `.roll(lon=320)` patm.ipynb applies to `jra_daily_std_mean`
right before plotting (Matt: "a weird hack, hardcoded to that value") -- 320
being half of JRA55's 640-point lon axis. Verified empirically here (not just
assumed) two ways:
  - Unrolled JRA55 puts ~1020 hPa over the Tibetan Plateau (impossible at
    ~4500 m elevation) and ~861 hPa over the open mid-Pacific (impossible at
    sea level); rolled gives ~540 hPa and ~1009 hPa respectively -- physically
    sane.
  - Cross-correlating JRA3Q/ERA5 against (rolled) JRA55 over a pure open-
    ocean N. Atlantic box (35-65N, 45-15W, several dates) flips from
    *negative* correlation at roll=0 to ~+0.5 at roll=ny/2.
The same construction bug is in JRA3Q (ny=960, roll=480) and ERA5 (ny=1280,
roll=640) -- confirmed by the correlation test above, not just assumed by
analogy. This dealiasing must happen per-product, on each product's own
native grid, *before* interpolating onto a common grid -- test_chaudhuri_
uncertainty.ipynb's Em/Ev never did this before combining, so anything
computed from it (including input_weight/chaudhuri_method/ev_patm_2012_*.nc,
which also predates this fix, plus its em_ counterpart is actually corrupt on
disk -- `file` reports it as generic "data", not netCDF) should be treated as
unverified and superseded by the sigma_patm_spread_<year>.nc this script
writes.
"""
import os
import time
from itertools import combinations

import numpy as np
import xarray as xr

from ..patm import load_forcing_generic

OUT_DIR = os.path.join(os.path.dirname(__file__), 'data')

JRA55_DIR = '/work/08381/goldberg/ls6/jra55/'
JRA3Q_DIR = '/work/08381/goldberg/ls6/jra3q/'
ERA5_DIR = '/work2/08381/goldberg/ls6/era5/'
YEAR = 2012


def _dealias_lon(da):
    """Undo load_forcing_generic's lon sort-vs-data misalignment (see module
    docstring). `da` must have a full, native 'lon' dim (not yet interpolated
    onto another grid)."""
    n = da.sizes['lon']
    return da.roll(lon=n // 2, roll_coords=False)


def compute_sigma_std(forcing_dir=JRA55_DIR, year=YEAR):
    """Sub-daily std of JRA55 p_atm, time-mean over the year -- the main-run
    prior (what wApressure_ASTE270_EXFpress_std_new.bin is regridded from).
    Reproduces patm.ipynb's `jra_daily_std_mean`. Returns [lat, lon], Pa.
    """
    jra = load_forcing_generic(forcing_dir, year=year, fld='pres', dataset='jra55')
    jra = _dealias_lon(jra)
    daily_std = jra.resample(time='1d').std('time')
    sigma = daily_std.mean('time')
    sigma.name = 'sigma_patm_std'
    sigma.attrs.update(
        units='Pa',
        long_name='Sub-daily std of JRA55 surface pressure, time-mean over year',
        source=f'{forcing_dir} pres {year}',
    )
    return sigma


def compute_sigma_spread(jra55_dir=JRA55_DIR, jra3q_dir=JRA3Q_DIR, era5_dir=ERA5_DIR, year=YEAR):
    """Chaudhuri-style reanalysis spread: max-over-pairs temporal std of the
    DIFFERENCE between JRA55/JRA3Q/ERA5 p_atm (Ponte-consistent). Reproduces
    test_chaudhuri_uncertainty.ipynb's `Ev`, but with each product's own lon
    dealiased on its native grid before interpolation (see module docstring
    -- the notebook version skipped this and is not trustworthy). Returns
    [lat, lon], Pa, on the JRA55 grid.
    """
    jra55 = _dealias_lon(load_forcing_generic(jra55_dir, year=year, fld='pres', dataset='jra55'))

    jra3q = _dealias_lon(load_forcing_generic(jra3q_dir, year=year, fld='pres', dataset='jra3q'))
    jra3q = jra3q.resample(time='3h').mean().interp(lat=jra55.lat, lon=jra55.lon)

    era5 = _dealias_lon(load_forcing_generic(era5_dir, year=year, fld='pres', dataset='ERA5'))
    era5 = era5.resample(time='3h').mean().interp(lat=jra55.lat, lon=jra55.lon)

    datasets = {'jra55': jra55, 'jra3q': jra3q, 'era5': era5}
    ev_list = [
        (datasets[a] - datasets[b]).std(dim='time')
        for a, b in combinations(datasets, 2)
    ]
    ev = xr.concat(ev_list, dim='pair').max('pair')
    ev.name = 'sigma_patm_spread'
    ev.attrs.update(
        units='Pa',
        long_name=('Max-over-pairs temporal std of JRA55/JRA3Q/ERA5 p_atm '
                    'differences (Chaudhuri spread, Ponte-consistent)'),
        source=f'{jra55_dir}, {jra3q_dir}, {era5_dir}, pres {year}',
    )
    return ev


def main(out_dir=OUT_DIR, year=YEAR):
    os.makedirs(out_dir, exist_ok=True)

    t0 = time.time()
    print('Computing sigma_patm STD field (JRA55 sub-daily std)...')
    sigma_std = compute_sigma_std(year=year)
    std_path = os.path.join(out_dir, f'sigma_patm_std_{year}.nc')
    sigma_std.to_netcdf(std_path)
    print(f'  wrote {std_path}  ({time.time() - t0:.0f}s)')

    t1 = time.time()
    print('Computing sigma_patm SPREAD field (Chaudhuri, JRA55/JRA3Q/ERA5)...')
    sigma_spread = compute_sigma_spread(year=year)
    spread_path = os.path.join(out_dir, f'sigma_patm_spread_{year}.nc')
    sigma_spread.to_netcdf(spread_path)
    print(f'  wrote {spread_path}  ({time.time() - t1:.0f}s)')

    print(f'Done. Total {time.time() - t0:.0f}s.')


if __name__ == '__main__':
    main()
