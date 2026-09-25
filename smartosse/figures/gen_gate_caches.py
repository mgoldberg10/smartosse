#!/usr/bin/env python
"""Generate every Davis-Strait / gateway cache for one OSSE run, in a single pass.

Previously the caches existed only for ``runc68v_froman_partialcables_jrastd``.
Table 4's "$p_{atm}$ on" column is actually ``jraspread``, so the corrected
(signed, section-normal) recompute needs that run's caches too -- see
``DavisStrait_fw_decompisition_plan.md``, objective A.

Reading the raw MITgcm 3-D binaries (50 levels x 31 days x 6 tiles x 2 iters,
for both ``trsp_3d_set1`` and ``state_3d_set1``) is the slow step, so everything
that needs them is computed here once and cached:

  1. <RUN_DIR>/advfw_fm_cache_<date>_iters<i>_<j>.nc
       ADVe_FW, ADVn_FW  -- as before, so ``smartosse.osse`` still loads it
       ADVx_FW, ADVy_FW  -- NEW: the staggered components, which the old cache
                            threw away. Required for the signed maskW/maskS
                            section-normal transport at all four gateways.
  2. output/davis_strait/davis_strait_fields_cache_<tag>.nc
       the four (velocity, salinity) ADV_fw pairings + the two barotropic
       transports, rotated to true north and clipped to the Davis Strait box.
  3. output/davis_strait/advfw_hybrid_staggered_<tag>.nc
       staggered ADVx/ADVy for the two *hybrid* pairings, full domain, so the
       V'/S' attribution can also be done on the correct signed gate.
  4. output/davis_strait/davis_strait_section3d_cache_<tag>.nc
       January-mean 3-D northward velocity and salinity in the box.

Naming: ``v{X}s{Y}`` = velocity from iteration index X, salinity from index Y,
with 0 = FM (iter0000, first guess) and 1 = OSSE (iter0020, assimilated).

Run (on any configured site -- see smartosse/paths.py and config/sites.yml;
run e.g. `SMARTOSSE_SITE=pfe` or export SMARTOSSE_RUN_ROOT/SMARTOSSE_GRID_DIR
directly to override):
  python -m smartosse.figures.gen_gate_caches [run_tag]   # default run_tag: jraspread
"""
import os
import sys
import time
import warnings

import numpy as np
import xarray as xr
import pandas as pd

from ..llc_grid import get_llc_grid, UEVNfromUXVY
from ..dataset import open_astedataset, open_asteoptimdataset
from ..paths import run_root, grid_dir

warnings.filterwarnings("ignore")

# --------------------------------------------------------------------------- #
# Config -- kept deliberately identical to davis_strait_fw_decomposition.py
# --------------------------------------------------------------------------- #
RUN_TAG = sys.argv[1] if len(sys.argv) > 1 else "jraspread"
RUN_DIR = os.path.join(run_root(),
                        f"runc68v_froman_partialcables_{RUN_TAG}", "201201", "labsea") + "/"
GRID_DIR = grid_dir() + "/"

SREF = 34.8  # reference salinity used to build ADV_fw (matches NR construction)
ITERS = [0, 20]  # iter0000 = FM (first guess), iter0020 = OSSE (assimilated)
START = pd.to_datetime("201201", format="%Y%m")
DATETIMES = pd.date_range(START, START + pd.offsets.MonthEnd(1), freq="D")

# Box (on the single tile the strait sits on) the section-level caches clip to.
BOX_TILE = 4
BOX_J = slice(180, 235)
BOX_I = slice(5, 50)

OUTDIR = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                      "output", "davis_strait")
os.makedirs(OUTDIR, exist_ok=True)

FIELDS_CACHE = os.path.join(OUTDIR, f"davis_strait_fields_cache_{RUN_TAG}.nc")
HYBRID_CACHE = os.path.join(OUTDIR, f"advfw_hybrid_staggered_{RUN_TAG}.nc")
SECTION3D_CACHE = os.path.join(OUTDIR, f"davis_strait_section3d_cache_{RUN_TAG}.nc")

_iter_str = "_".join(str(i) for i in ITERS)
RUNDIR_CACHE = os.path.join(
    RUN_DIR, f"advfw_fm_cache_{DATETIMES[0]:%Y%m%d}_iters{_iter_str}.nc")

GRID_DS = None
GRID_OBJ = None
T0 = time.time()


def log(msg):
    print(f"[{time.time() - T0:7.1f}s] {msg}", flush=True)


def _bare(da):
    """Drop non-dimension coordinates so the array cleanly rides the grid ds."""
    return da.reset_coords(drop=True)


def rotate_to_EN(u_x, v_y):
    """Rotate a staggered (x, y) vector to true (east, north) at cell centres."""
    return UEVNfromUXVY(_bare(u_x), _bare(v_y), GRID_DS, GRID_OBJ)


def clip_box(da):
    """Clip a full-domain field to the Davis Strait working box."""
    return da.isel(tile=BOX_TILE, j=BOX_J, i=BOX_I)


def advfw_staggered(trsp, salt):
    """Depth-integrated staggered FW transport components for a (v, S) pairing.

    Matches ``ForecastModel._load_fm_fwflx`` (smartosse/osse.py) exactly:
    salinity is interpolated onto the velocity faces before the (Sref - S)/Sref
    weighting, and the vertical sum is over the full column.
    """
    s_u = GRID_OBJ.interp(_bare(salt), "X", padding="extend")
    s_v = GRID_OBJ.interp(_bare(salt), "Y", padding="extend")
    advx = (trsp.UVELMASS * trsp.dyG * trsp.drF * (SREF - s_u) / SREF).sum("k")
    advy = (trsp.VVELMASS * trsp.dxG * trsp.drF * (SREF - s_v) / SREF).sum("k")
    return advx.compute(), advy.compute()


def vbt_staggered(trsp):
    """Depth-integrated hFac-weighted volume transport -- the Fig. 6f quantity."""
    u = (trsp.UVELMASS * trsp.hFacW * trsp.dyG * trsp.drF).sum("k")
    v = (trsp.VVELMASS * trsp.hFacS * trsp.dxG * trsp.drF).sum("k")
    return u.compute(), v.compute()


def main():
    global GRID_DS, GRID_OBJ

    log(f"run tag       : {RUN_TAG}")
    log(f"run dir       : {RUN_DIR}")
    for p in (RUNDIR_CACHE, FIELDS_CACHE, HYBRID_CACHE, SECTION3D_CACHE):
        log(f"  -> {p}{'   (EXISTS, will overwrite)' if os.path.exists(p) else ''}")

    log("loading grid ...")
    GRID_DS = open_astedataset(GRID_DIR, grid_dir=GRID_DIR, iters=None)
    GRID_OBJ = get_llc_grid(GRID_DS, domain="aste")

    log("opening trsp_3d_set1 / state_3d_set1 ...")
    trsp = open_asteoptimdataset(RUN_DIR, optim_iters=ITERS, grid_dir=GRID_DIR,
                                 prefix=["trsp_3d_set1"])
    state = open_asteoptimdataset(RUN_DIR, optim_iters=ITERS, grid_dir=GRID_DIR,
                                  prefix=["state_3d_set1"])
    n = len(DATETIMES)
    trsp = trsp.isel(time=slice(0, n)).assign_coords(time=DATETIMES)
    state = state.isel(time=slice(0, n)).assign_coords(time=DATETIMES)

    tr = [trsp.isel(ioptim=0), trsp.isel(ioptim=1)]
    sa = [state.isel(ioptim=0).SALT, state.isel(ioptim=1).SALT]

    # ---------------------------------------------------------------- #
    # 1. honest pairings -> run-dir cache (staggered + rotated)
    # ---------------------------------------------------------------- #
    boxed = {}
    honest_x, honest_y, honest_e, honest_n = [], [], [], []
    for i in (0, 1):
        log(f"computing ADV_fw v{i}s{i} (iter{ITERS[i]:04d}) ...")
        ax, ay = advfw_staggered(tr[i], sa[i])
        ae, an = rotate_to_EN(ax, ay)
        honest_x.append(ax)
        honest_y.append(ay)
        honest_e.append(ae)
        honest_n.append(an)
        boxed[f"adv_v{i}s{i}"] = clip_box(an)

    log(f"writing {RUNDIR_CACHE} ...")
    xr.Dataset({
        "ADVe_FW": xr.concat(honest_e, dim="ioptim"),
        "ADVn_FW": xr.concat(honest_n, dim="ioptim"),
        "ADVx_FW": xr.concat(honest_x, dim="ioptim"),
        "ADVy_FW": xr.concat(honest_y, dim="ioptim"),
    }).to_netcdf(RUNDIR_CACHE)
    del honest_e, honest_n
    log("  run-dir cache written (all four gateways can now be recomputed)")

    # ---------------------------------------------------------------- #
    # 2. hybrid pairings -> V'/S' attribution
    # ---------------------------------------------------------------- #
    hyb = {}
    for iv, isal in ((1, 0), (0, 1)):
        tag = f"v{iv}s{isal}"
        log(f"computing ADV_fw {tag} (v=iter{ITERS[iv]:04d}, S=iter{ITERS[isal]:04d}) ...")
        ax, ay = advfw_staggered(tr[iv], sa[isal])
        hyb[f"advx_{tag}"] = ax
        hyb[f"advy_{tag}"] = ay
        _, an = rotate_to_EN(ax, ay)
        boxed[f"adv_{tag}"] = clip_box(an)

    # carry the honest staggered pair along so the attribution is self-contained
    for i in (0, 1):
        hyb[f"advx_v{i}s{i}"] = honest_x[i]
        hyb[f"advy_v{i}s{i}"] = honest_y[i]
    log(f"writing {HYBRID_CACHE} ...")
    xr.Dataset(hyb).to_netcdf(HYBRID_CACHE)
    del hyb, honest_x, honest_y

    # ---------------------------------------------------------------- #
    # 3. barotropic transports (Fig. 6f quantity)
    # ---------------------------------------------------------------- #
    for i in (0, 1):
        log(f"computing V_bt v{i} ...")
        u, v = vbt_staggered(tr[i])
        _, vn = rotate_to_EN(u, v)
        boxed[f"vbt_v{i}"] = clip_box(vn)

    log(f"writing {FIELDS_CACHE} ...")
    xr.Dataset(boxed).to_netcdf(FIELDS_CACHE)
    del boxed

    # ---------------------------------------------------------------- #
    # 4. January-mean 3-D section fields
    # ---------------------------------------------------------------- #
    sec = {}
    for i, tag in enumerate(("v0", "v1")):
        log(f"rotating January-mean 3-D velocity, {tag} ...")
        _, vn = rotate_to_EN(tr[i].UVELMASS.mean("time").compute(),
                             tr[i].VVELMASS.mean("time").compute())
        sec[f"vn_{tag}"] = clip_box(vn)
        sec[f"salt_{tag}"] = clip_box(sa[i].mean("time").compute())

    log(f"writing {SECTION3D_CACHE} ...")
    xr.Dataset(sec).to_netcdf(SECTION3D_CACHE)

    log("done.")
    for p in (RUNDIR_CACHE, FIELDS_CACHE, HYBRID_CACHE, SECTION3D_CACHE):
        log(f"  {os.path.getsize(p) / 1e6:8.1f} MB  {p}")


if __name__ == "__main__":
    main()
