"""Sensor-spacing sweep -- pairwise differences of :math:`p_b` skill, 1x3.

Port of ``smart_cables/osse/fullnatl_nthsensors.ipynb`` (cells 22, 24-25, the
cell that writes ``sensor_spacing_pb_skill_70_140_210_diff.png``) onto this
package's figure conventions, pointed at the **new** spacing sweep::

    /scratch/.../osses/runc68v_froman_partialcables_jraspread_spacing/201201/
        70km/{iter0000,iter0010}/
        140km/{iter0000,iter0010}/
        210km/...                      <- not downloaded yet

Each panel is a difference of two skill maps,

    S(p_b^{A km}) - S(p_b^{B km}),   S = 1 - rms(p_b^N - p_b^NR)/rms(p_b^0 - p_b^NR)

over the 31 daily records of January 2012, iterations 0 -> 10, using
``smartosse.osse._compute_skill`` unchanged. **Positive (teal) means the
first-named (finer) spacing did better**; negative (rose) means the coarser
cable of the pair did better. The notebook's own reading of the *old* sweep --
"looks like fewer sensors better!" -- is the negative case, and its warning
still applies to that sweep: the old 70km run had ``xx_apressure`` off, so the
comparison was not apples-to-apples. This sweep is, all spacings sharing the
one ``..._partialcables_jraspread_spacing`` configuration.

Panels, left to right: (a) 70-140, (b) 70-210, (c) 140-210.

Running with 210km missing
--------------------------
This is the state the module was written for. `build_cache` computes and caches
whatever spacings are on disk; `make_fig` renders any panel whose two spacings
are both cached and leaves the rest as empty decorated maps (frame, land and
gridlines, no data), announcing which. So today it draws panel (a) and blanks
(b) and (c). When the 210km run lands, drop it under `RUN_ROOT` as ``210km/``
(any ``210km*`` directory name works -- the notebook's
``210km_71sensors_fullnatl`` style is globbed for too) and re-run with
``--rebuild``: spacings already in the cache are reused, so 70 and 140 are NOT
recomputed -- only 210 is -- and all three panels fill in. Use
``--recompute-all`` if you change the iterations, the month or the run root,
since the cache does not record which of those each spacing came from.

The iteration-0 first guess
---------------------------
``70km/iter0000/`` shipped only ``adm_bpday`` -- no ``m_bpday``, so the 70km
run has no first-guess field of its own to divide by. Iteration 0 is the
unassimilated forward run: same model, same period, same first-guess controls
for every experiment, with the observation set entering the cost and the
gradient but not the iteration-0 trajectory. So the first guess is taken from
elsewhere -- another spacing that shipped one, else `FIRST_GUESS_RUN_DIR` --
and the substitution is printed every time it happens.

That premise is not assumed, it is **measured**: ``140km/iter0000/m_bpday`` is
*bit-identical* (``max|dp_b| = 0.0``) to ``iter0000/m_bpday`` of
``runc68v_froman_partialcables_jraspread/201201/fullnatl``, a run of the same
base configuration assimilating an entirely different observing system (the
full 157-sensor cable). `check_first_guesses` re-runs that comparison across
every candidate on every ``--rebuild`` and prints each ``max|dp_b|``; they
should all be 0. If one ever isn't, the borrowed-iteration-0 panels are invalid
and the run needs its own iteration 0.

``FIRST_GUESS_RUN_DIR`` is the intact full-cable January 2012 run that
`fig5_misfit_rmse_skill` and `si_skill_over_optim` both use, chosen as the
external fallback because it is the one run on ``/scratch`` that has not had
its per-iteration ``m_bpday`` purged.

``BPReader`` is bypassed here for the same reason as elsewhere in this package
(``gen_appendixB_skill_cache``, ``smart_grace_mo_skill``): its constructor
wants a ``data.ecco`` in ``iter0000/``, and these directories hold only the bp
diagnostics. ``load_bp_anom`` from ``gen_appendixB_skill_cache`` is reused
directly -- the same two lines that matter.

No cable scatter is drawn. The notebook's ``plot_skill_diff`` doesn't draw one
either, and it could not draw a single one honestly: each panel differences two
*different* sensor layouts. Those belong in the companion
``sensor_spacing_pb_skill_70_140_210.png`` figure (notebook cell 19), not here.

Rendering conventions (both are bug fixes over the notebook -- see STATUS.md,
2026-08-14, and `fig6_regions_skill_bp_uvbt`, which hit both first)
-------------------------------------------------------------------------
* **Saved on an opaque white background**, not the notebook's
  ``transparent=True``. The Natural Earth land polygons and the regridded ASTE
  field do not tile the map exactly, so a transparent save leaves alpha=0
  pinholes along every coastline, which any viewer compositing onto a dark
  ground (Acrobat dark mode, pdflatex) renders as black speckles behind the
  grey land.
* **`patch_pdf_indexed_image_bitdepth()` is called in ``__main__``**, required
  because the ``contourf`` fills are rasterized (per-collection: matplotlib
  3.4's ``ContourSet`` is not an Artist, so ``rasterized=`` to ``contourf`` is
  dropped) and matplotlib 3.4.3 writes a ``/DecodeParms`` without
  ``/BitsPerComponent`` for palette-encoded rasterized images -- giving a PDF
  that opens blank or "damaged", as though it had not finished being written.
  ``--no-rasterize`` gives fully vector fills instead, at ~9 MB per panel.

How to run
----------
::

    module load texlive
    conda activate /work2/08381/goldberg/ls6/miniforge3/envs/esmpy_3.10
    cd /work2/08381/goldberg/ls6/smartosse
    python -m smartosse.figures.figD1_sensor_spacing_skill_diff --rebuild

    # once 210km/ is in place -- computes only 210km:
    python -m smartosse.figures.figD1_sensor_spacing_skill_diff --rebuild

    # re-render off the cache at a different colour scale:
    python -m smartosse.figures.figD1_sensor_spacing_skill_diff --vmax 0.1

Writes ``output/sensor_spacing_pb_skill_70_140_210_diff.{png,pdf}`` and the
cache ``data/sensor_spacing_skill.nc``.
"""
import argparse
import glob
import os

import numpy as np
import pandas as pd
import xarray as xr
import cartopy.crs as ccrs
import cmocean

from ..cmaps import Colormaps
from ..osse import NatureRun, _compute_skill
from ..plot import llc_map, spna, retain_only_perimiter_gl_labels
from ..dataset import open_astedataset
from .figs_utils import add_panel_label
from .gen_appendixB_skill_cache import load_bp_anom

# =============================================================================
# Config
# =============================================================================

GRID_DIR = '/work/08381/goldberg/ls6/aste_270x450x180/GRID_noblank_real4/'

# The new spacing sweep: one subdirectory per sensor spacing, all sharing the
# partial-cables / JRA-spread p_atm uncertainty configuration.
RUN_ROOT = ('/scratch/08381/goldberg/aste_270x450x180/osses/'
            'runc68v_froman_partialcables_jraspread_spacing/201201/')

# Subdirectory glob per spacing. '{spacing}km*' matches both the new bare
# '70km/' layout and the notebook's '70km_157sensors_fullnatl/'.
RUN_SUBDIR_GLOB = '{spacing}km*'

SPACINGS_KM = (70, 140, 210)

# Panels, left to right. Panel (k) shows S(first) - S(second).
COMBOS = ((70, 140), (70, 210), (140, 210))

# First guess -> optimized. This sweep ran 10 iterations.
ITERNUMS = (0, 10)

# External source for iteration 0 when no spacing run has one: the intact
# full-cable Jan 2012 run (fig5_misfit_rmse_skill / si_skill_over_optim's).
# Verified bit-identical to 140km/iter0000 -- see the module docstring.
FIRST_GUESS_RUN_DIR = ('/scratch/08381/goldberg/aste_270x450x180/osses/'
                       'runc68v_froman_partialcables_jraspread/201201/fullnatl/')

MO_STR = '201201'          # 31 daily m_bpday records, January 2012

DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
OUT_DIR = os.path.join(os.path.dirname(__file__), 'output')
CACHE = os.path.join(DATA_DIR, 'sensor_spacing_skill.nc')
FIG_NAME = 'sensor_spacing_pb_skill_70_140_210_diff'

# Color scale -- the notebook's cell 24, shared by all three panels. 20 filled
# levels over +/-0.2, extend='both' for what runs over.
VMAX_DIFF = 0.2
NLEV = 20
CBAR_NTICKS = 5
CBAR_TICKS = None          # None -> CBAR_NTICKS evenly spaced over +/-vmax

# llc_map regrid resolution: 0.25 deg is finer than ASTE-270 in the SPNA, so
# the draw does not smooth the field (as in smart_grace_mo_skill).
REGRID_DX = 0.25

FIGSIZE = (30, 6)
PANEL_LABEL_FONTSIZE = 30
TITLE_FONTSIZE = 30
CBAR_RECT = (0.165, -0.10, 0.70, 0.065)   # figure fraction (x0, y0, w, h)
CBAR_TICK_LABELSIZE = 30


# =============================================================================
# Loaders
# =============================================================================

def month_datetimes(mo_str=MO_STR):
    """The FM's 31 daily record timestamps, 2012-01-01 .. 2012-01-31."""
    start = pd.to_datetime(mo_str, format='%Y%m')
    return pd.date_range(start=start, end=start + pd.offsets.MonthEnd(1), freq='D')


def run_dir(spacing_km, run_root=RUN_ROOT, subdir_glob=RUN_SUBDIR_GLOB):
    """Directory for one spacing, or None when that run isn't on disk yet."""
    matches = sorted(glob.glob(os.path.join(
        run_root, subdir_glob.format(spacing=spacing_km))))
    matches = [m for m in matches if os.path.isdir(m)]
    return matches[0] + '/' if matches else None


def bpday_path(rd, iternum):
    """``m_bpday`` binary inside run directory `rd`, or None if either is absent."""
    if rd is None:
        return None
    path = f'{rd.rstrip("/")}/iter{iternum:04d}/m_bpday.{iternum:010d}.data'
    return path if os.path.exists(path) else None


def available_spacings(spacings=SPACINGS_KM, iternums=ITERNUMS, **kw):
    """Spacings whose OPTIMIZED iteration is on disk.

    Only the last iteration has to be the run's own; iteration 0 may come from
    elsewhere (`first_guess_dir`), which is what lets 70km in at all.
    """
    return tuple(s for s in spacings
                 if bpday_path(run_dir(s, **kw), iternums[-1]) is not None)


def first_guess_dir(spacing_km, spacings=SPACINGS_KM, iternums=ITERNUMS,
                    fallback_run_dir=FIRST_GUESS_RUN_DIR, **kw):
    """Run directory to take iteration 0 from: the spacing's own, else a donor.

    Order: this spacing's own ``iter0000``, then any other spacing's, then
    `fallback_run_dir`. Prints the substitution when it makes one -- this is
    the one place the figure departs from "each panel is that run's own skill",
    so it must never happen silently. Returns None if nothing has one.
    """
    it0 = iternums[0]
    own = bpday_path(run_dir(spacing_km, **kw), it0)
    if own is not None:
        return run_dir(spacing_km, **kw)

    for other in spacings:
        if other == spacing_km:
            continue
        rd = run_dir(other, **kw)
        if bpday_path(rd, it0) is not None:
            print(f'[skill] {spacing_km}km has no iter{it0:04d}/m_bpday -- using '
                  f'{other}km\'s (iteration 0 is the unassimilated forward run; '
                  'see [check] lines above)', flush=True)
            return rd

    if bpday_path(fallback_run_dir, it0) is not None:
        print(f'[skill] {spacing_km}km has no iter{it0:04d}/m_bpday and no '
              f'sibling spacing does either -- using {fallback_run_dir}',
              flush=True)
        return fallback_run_dir

    print(f'[skill] {spacing_km}km has no iter{it0:04d}/m_bpday and no donor '
          '-- skipping', flush=True)
    return None


def check_first_guesses(spacings=SPACINGS_KM, iternums=ITERNUMS, datetimes=None,
                        fallback_run_dir=FIRST_GUESS_RUN_DIR, **kw):
    """Print ``max|dp_b|`` between every iteration-0 field available.

    The premise `first_guess_dir` leans on, made falsifiable: every candidate
    donor is compared against the first one. Expected 0.0 throughout -- see the
    module docstring. Anything else means the runs did not share a first guess
    and any panel whose iteration 0 was borrowed is invalid.
    """
    datetimes = month_datetimes() if datetimes is None else datetimes
    it0 = iternums[0]

    donors = [(f'{s}km', run_dir(s, **kw)) for s in spacings]
    donors.append(('fullnatl (fallback)', fallback_run_dir))
    donors = [(n, d) for n, d in donors if bpday_path(d, it0) is not None]

    if len(donors) < 2:
        print(f'[check] {len(donors)} iter{it0:04d} field(s) available -- '
              'first-guess identity not testable', flush=True)
        return

    def load(rd):
        return load_bp_anom(rd, iternums=(it0,), datetimes=datetimes).isel(ioptim=0)

    ref_name, ref_dir = donors[0]
    ref = load(ref_dir).compute()
    for name, rd in donors[1:]:
        dmax = float(abs(load(rd).compute() - ref).max())
        flag = '' if dmax == 0 else '   <-- NOT identical, see module docstring'
        print(f'[check] iter{it0:04d} {ref_name} vs {name}: '
              f'max|dp_b| = {dmax:.3e} cm{flag}', flush=True)


# =============================================================================
# Skill
# =============================================================================

def compute_skill(spacing_km, nr=None, datetimes=None, spacings=SPACINGS_KM,
                  iternums=ITERNUMS, **kw):
    """Daily :math:`p_b` skill map for one spacing, or None if unavailable.

    ``m_bpday`` at iteration 0 (possibly from a donor run) and at the last
    iteration, each converted to a cm anomaly, scored against the NR's daily
    means.
    """
    datetimes = month_datetimes() if datetimes is None else datetimes
    rd = run_dir(spacing_km, **kw)
    if bpday_path(rd, iternums[-1]) is None:
        print(f'[skill] {spacing_km}km: no iter{iternums[-1]:04d}/m_bpday '
              '-- not computed', flush=True)
        return None

    fg_dir = first_guess_dir(spacing_km, spacings=spacings, iternums=iternums, **kw)
    if fg_dir is None:
        return None

    nr = NatureRun(fld_type='bp') if nr is None else nr
    nr_fld = (nr.fld_full
              .sel(time=slice(datetimes[0], datetimes[-1]))
              .resample(time='1D').mean())

    # Load the two iterations separately so the first guess can come from a
    # different run directory than the optimized field, then stack them on
    # ioptim in (before, after) order -- what _compute_skill expects.
    before = load_bp_anom(fg_dir, iternums=iternums[:1], datetimes=datetimes)
    after = load_bp_anom(rd, iternums=iternums[-1:], datetimes=datetimes)
    fm_fld = xr.concat([before, after], dim='ioptim')
    return _compute_skill(fm_fld, nr_fld)


def build_cache(out_path=CACHE, run_root=RUN_ROOT, spacings=SPACINGS_KM,
                iternums=ITERNUMS, mo_str=MO_STR, check_first_guess=True,
                reuse_cached=True):
    """Compute the skill map for every available spacing and merge into `out_path`.

    One variable, ``skill``, with dims (spacing, tile, j, i). A spacing already
    in `out_path` is reused rather than recomputed (`reuse_cached`, the
    default), and the result is merged with what was there, so re-running once
    210km lands costs one skill map, not three. Pass ``reuse_cached=False``
    (``--recompute-all``) after changing `iternums`, the month or the run root.
    """
    kw = dict(run_root=run_root)
    datetimes = month_datetimes(mo_str)

    old = None
    if os.path.exists(out_path):
        with xr.open_dataset(out_path) as _old:
            old = _old.load()

    present = available_spacings(spacings, iternums=iternums, **kw)
    missing = [s for s in spacings if s not in present]
    if missing:
        print('[skill] NOT on disk (panels using them will be blank): '
              + ', '.join(f'{s}km' for s in missing), flush=True)
    if not present:
        raise SystemExit(f'no spacing runs found under {run_root}')

    if check_first_guess:
        check_first_guesses(spacings, iternums=iternums, datetimes=datetimes, **kw)

    todo = present
    if reuse_cached and old is not None:
        cached = [s for s in present if get_skill(old, s) is not None]
        if cached:
            print('[skill] reusing cached map(s): '
                  + ', '.join(f'{s}km' for s in cached)
                  + '  (--recompute-all to redo)', flush=True)
        todo = tuple(s for s in present if s not in cached)
    if not todo:
        print('[skill] nothing to compute', flush=True)
        return old

    nr = NatureRun(fld_type='bp')          # loaded once, used by every spacing

    maps = {}
    for spacing in todo:
        skill = compute_skill(spacing, nr=nr, datetimes=datetimes,
                              spacings=spacings, iternums=iternums, **kw)
        if skill is None:
            continue
        maps[spacing] = skill.reset_coords(drop=True).compute()
        print(f'[skill] {spacing}km  mean={float(maps[spacing].mean()):+.4f}  '
              f'median={float(maps[spacing].median()):+.4f}', flush=True)

    ds = xr.Dataset({'skill': xr.concat(
        [maps[s] for s in maps], dim=pd.Index(list(maps), name='spacing'))})

    if old is not None:
        # Outer-join on spacing, preferring this call's values where they are
        # not NaN -- so a new spacing extends the cache instead of replacing it
        # (same pattern as gen_appendixB_skill_cache).
        ds = ds.combine_first(old)

    ds.attrs.update(
        note=('skill = 1 - rms_after/rms_before on time-mean-removed DAILY p_b '
              '(smartosse.osse._compute_skill); spacing is the cable sensor '
              'spacing in km'),
        run_root=run_root,
        iternums=str(list(iternums)),
        mo_str=mo_str,
    )
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    ds.to_netcdf(out_path)
    print('wrote', out_path, flush=True)
    return ds


def get_skill(cache, spacing_km):
    """One spacing's map out of the cache, or None when it isn't there."""
    if 'skill' not in cache or spacing_km not in cache.spacing.values:
        return None
    da = cache['skill'].sel(spacing=spacing_km)
    return None if bool(da.isnull().all()) else da


# =============================================================================
# Plotting
# =============================================================================

def skill_cmap(nlev=NLEV):
    """White-centered ``cmocean curl_r``, the package's standard skill map."""
    return Colormaps(nlev).custom_div_cmap(template_cmap=cmocean.cm.curl_r)


def draw_diff_map(ax, field2d, lon2d, lat2d, vmax=VMAX_DIFF, nlev=NLEV, cmap=None,
                  rasterize=True):
    """Filled-contour one regridded skill-difference map onto a decorated GeoAxes."""
    cmap = skill_cmap(nlev) if cmap is None else cmap
    cs = ax.contourf(lon2d, lat2d, field2d,
                     levels=np.linspace(-vmax, vmax, nlev),
                     cmap=cmap, vmin=-vmax, vmax=vmax, extend='both',
                     transform=ccrs.PlateCarree(), transform_first=True,
                     zorder=0)
    if rasterize:
        # Per-collection: matplotlib 3.4's ContourSet is not an Artist, so a
        # `rasterized=` kwarg handed to contourf is silently dropped. Requires
        # patch_pdf_indexed_image_bitdepth() at save time -- see the docstring.
        for coll in cs.collections:
            coll.set_rasterized(True)
    return cs


def diff_title(pair):
    """``S(p_b^{70 km}) - S(p_b^{140 km})`` as mathtext/LaTeX."""
    a, b = pair
    return (rf'$\mathcal{{S}}(p_b^{{{a}\,\mathrm{{km}}}})'
            rf' - \mathcal{{S}}(p_b^{{{b}\,\mathrm{{km}}}})$')


def make_fig(cache, ds, lm=None, combos=COMBOS, vmax=VMAX_DIFF, nlev=NLEV,
             figsize=FIGSIZE, ticks=CBAR_TICKS, cbar_rect=CBAR_RECT,
             titles=False, rasterize=True, verbose=True):
    """The 1x3 figure of pairwise skill differences.

    A panel whose pair is not both in `cache` is left as an empty decorated map
    -- frame, land and gridlines, no data -- rather than raising, which is what
    makes the module usable before the 210km run arrives.

    `titles` (``--titles``) writes ``S(p_b^{70 km}) - S(p_b^{140 km})`` over
    each panel. Off by default, as in the notebook (which had them commented
    out) and as Matt asked on 2026-08-19 -- which pair each panel shows belongs
    in the caption.
    """
    lm = lm or llc_map(ds, dx=REGRID_DX, dy=REGRID_DX)
    lon2d, lat2d = lm.new_grid_lon, lm.new_grid_lat

    fig, axes, gl_list = spna(1, len(combos), figsize=figsize, return_gl=True)

    mesh = None
    drawn = []
    for ax, pair, letter in zip(axes, combos, 'abcdefg'):
        a, b = (get_skill(cache, s) for s in pair)
        if a is not None and b is not None:
            cs = draw_diff_map(ax, lm.regrid(a - b), lon2d, lat2d,
                               vmax=vmax, nlev=nlev, rasterize=rasterize)
            mesh = mesh or cs
            drawn.append((pair, (a - b)))
        else:
            absent = ', '.join(f'{s}km' for s, v in zip(pair, (a, b)) if v is None)
            print(f'[fig] ({letter}) {pair[0]}-{pair[1]}: BLANK (no {absent})',
                  flush=True)
        if titles:
            ax.set_title(diff_title(pair), fontsize=TITLE_FONTSIZE)
        add_panel_label(ax, letter, fontsize=PANEL_LABEL_FONTSIZE, x=0.02, y=0.97)

    # Latitude labels on the leftmost panel only.
    fig.canvas.draw()
    retain_only_perimiter_gl_labels(np.array([axes]), gl_list)

    if mesh is not None:
        ticks = (np.linspace(-vmax, vmax, CBAR_NTICKS) if ticks is None
                 else np.asarray(ticks, float))
        cb = fig.colorbar(mesh, cax=fig.add_axes(list(cbar_rect)),
                          orientation='horizontal')
        cb.set_ticks(ticks)
        cb.set_ticklabels([f'{t:.2f}' for t in ticks])
        cb.ax.tick_params(labelsize=CBAR_TICK_LABELSIZE, length=10, width=2)
    else:
        print('[fig] no panel had data -- no colorbar drawn', flush=True)

    if verbose:
        # Wet points only. ~35% of the ASTE-270 array is land, where the skill
        # is an exact 0 that _compute_skill never touched; averaging those in
        # drags every statistic toward zero. Printout only -- the plotted
        # field is untouched. Note this is the whole ASTE domain, not just the
        # SPNA window the panels show.
        wet = (ds['Depth'] > 0).values
        for pair, dda in drawn:
            v = np.asarray(dda.values, float)
            v = v[wet & np.isfinite(v)]
            print(f'[fig] {pair[0]}-{pair[1]}: mean={v.mean():+.4f} '
                  f'median={np.median(v):+.4f} '
                  f'p98|d|={np.quantile(np.abs(v), 0.98):.3f} '
                  f'{100 * np.mean(v > 0):.0f}% of wet points favour '
                  f'{pair[0]}km, {100 * np.mean(np.abs(v) > vmax):.1f}% beyond '
                  f'+/-{vmax}', flush=True)

    return fig, axes


def save_fig(fig, name, out_dir=OUT_DIR, exts=('png', 'pdf')):
    """Save on an **opaque white** background, not ``transparent=True``.

    Same as ``fig6_regions_skill_bp_uvbt.save_fig``: the land feature and the
    regridded field don't tile the map exactly, so a transparent save leaves
    alpha=0 pinholes along every coastline, which a viewer compositing onto a
    dark ground renders as black speckles behind the grey land. STATUS.md,
    2026-08-14.
    """
    os.makedirs(out_dir, exist_ok=True)
    for ext in exts:
        fig.savefig(os.path.join(out_dir, f'{name}.{ext}'), dpi=300,
                    bbox_inches='tight', facecolor='white', edgecolor='none')
    print(f'wrote {name}.{{{",".join(exts)}}} to {out_dir}', flush=True)


# =============================================================================
if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--run-root', default=RUN_ROOT,
                    help='directory holding one subdirectory per spacing')
    ap.add_argument('--spacings', type=int, nargs='+', default=list(SPACINGS_KM),
                    help=f'sensor spacings in km (default {list(SPACINGS_KM)})')
    ap.add_argument('--iters', type=int, nargs='+', default=list(ITERNUMS),
                    help='iterations to score, first=guess last=optimized '
                         f'(default {list(ITERNUMS)})')
    ap.add_argument('--month', default=MO_STR, help=f'YYYYMM (default {MO_STR})')
    ap.add_argument('--rebuild', action='store_true',
                    help='refresh the cache (spacings already cached are reused '
                         'unless --recompute-all)')
    ap.add_argument('--recompute-all', action='store_true',
                    help='recompute every spacing, ignoring what is cached')
    ap.add_argument('--out', default=CACHE)
    ap.add_argument('--vmax', type=float, default=VMAX_DIFF,
                    help='color-scale half-range, shared by all panels '
                         f'(default {VMAX_DIFF})')
    ap.add_argument('--ticks', type=float, nargs='+', default=CBAR_TICKS,
                    help=f'explicit colorbar ticks; default {CBAR_NTICKS} '
                         'evenly spaced over +/-vmax')
    ap.add_argument('--titles', action='store_true',
                    help='write the per-panel S(a)-S(b) titles (off by default, '
                         'as in the notebook)')
    ap.add_argument('--no-rasterize', action='store_true',
                    help='fully vector contourf fills (much larger PDF)')
    ap.add_argument('--fig-name', default=FIG_NAME,
                    help=f'output basename, no extension (default {FIG_NAME})')
    args = ap.parse_args()

    from .figs_utils import (use_latex_times, use_embedded_pdf_fonts,
                             patch_pdf_indexed_image_bitdepth)

    use_latex_times()
    use_embedded_pdf_fonts()
    # Required whenever the fills are rasterized (the default) on matplotlib
    # < 3.5, or the PDF's palette-encoded panels are undecodable.
    patch_pdf_indexed_image_bitdepth()

    if args.rebuild or args.recompute_all or not os.path.exists(args.out):
        cache = build_cache(out_path=args.out, run_root=args.run_root,
                            spacings=tuple(args.spacings),
                            iternums=tuple(args.iters), mo_str=args.month,
                            reuse_cached=not args.recompute_all)
    else:
        cache = xr.open_dataset(args.out).load()
        print(f'loaded cache {args.out} (--rebuild to recompute)', flush=True)

    ds = open_astedataset(GRID_DIR, grid_dir=GRID_DIR, iters=None)
    fig, axes = make_fig(cache, ds, vmax=args.vmax, ticks=args.ticks,
                         titles=args.titles, rasterize=not args.no_rasterize)

    save_fig(fig, args.fig_name)
