"""Appendix B -- the day-to-day-std twin of Fig. 9 (``fig9_spread_3panel.py``).

Four panels, deliberately mirroring Fig. 9 panel-for-panel so a reader can flip
between the two figures, plus one new panel carrying the QoI claim:

    (a) sigma_patm, day-to-day std of daily-mean JRA-55 p_atm  [map + cable dots]
        -- same projection / cable dots / colorbar geometry as Fig. 9a, range
        0-20 hPa instead of 0-2. This is the panel that answers R2's original
        complaint directly: it puts the ~8-15 hPa daily-p_atm std they said
        should be there on the page, labelled as a day-to-day std, while Fig. 9a
        is labelled as an inter-reanalysis spread.
    (b) global max |dp_atm| / sigma_patm, one curve per cable -- identical axes,
        shading and ylim (0-1.7) to Fig. 9b, so the eye does the comparison
        without a solid/dashed key.
    (c) paired relative-control-contribution bars, STD (plain) vs SPREAD
        (hatched), one pair per cable. Carries "re-weighting p_atm redistributes
        the attribution between wind and pressure".
    (d) 1:1 scatter of skill, std OSSE (y) against spread OSSE (x), over SPNA
        grid points with the cables pooled, p_b and V_bt as two colors, 1:1 line,
        RMS deviation from that line annotated. This is the panel backing the
        "the QoIs themselves change negligibly" sentence -- everything on the
        diagonal *is* "changes negligibly", stated quantitatively.

ADV_fw is deliberately not in the figure: the std runs archived only
``state_2d_set1`` and ``trsp_3d_set1`` (no ``state_3d_set1``, hence no
salinity), so it isn't computable from them. The cheaper argument belongs in the
text -- Table 4's own p_atm-on/off columns already show that switching the p_atm
control off entirely moves gateway bias reduction by <=0.2 pp.

-----------------------------------------------------------------------------
DATA STATUS as of 2026-08-11 (evening) -- all four panels carry real data
-----------------------------------------------------------------------------
The ``xx.tar.gz`` transfer (extracted 14:37) delivered the ``adxx_*`` gradients
and ``xx_apressure.effective`` for every region, so (b) and (c) both populate.
The placeholder path below is retained for reproducibility, not because
anything is currently missing.

All four cables are in. SPG's final iter0020 landed 2026-08-11 15:31, replacing
the earlier copy whose ``adxx_apressure``/``adxx_uwind``/``adxx_vwind`` were
identically zero. ``valid_gradient_regions()`` still checks that on every
render, and ``STD_EXCLUDE_REGIONS`` remains as a manual override -- a zero
gradient does not blank a bar, it renormalizes the rest into a confident wrong
one, so this stays guarded rather than trusted.

  * (b) reads ``xx_apressure.effective.{iter}.data``
  * (c) reads ``adxx_*.{iter}.data`` -- the plain adjoint gradients, NOT the
        ``xx_*`` controls and NOT the ``.effective`` variants; that is what
        ``smartuq.ctrl.ControlDataset`` reads. The control list, weights and
        data.ctrl come from ``DATA_CTRL_DIR_STD_DAYTODAY``/``WEIGHT_DIR``,
        which are local, so the run's own data.ctrl is not needed.

``make_figB(..., skip_unavailable=True)`` (the default) still draws (b)/(c) as
annotated placeholders if their inputs go missing again; ``False`` raises.

Panel (c) is weighted against ``DATA_CTRL_DIR_STD_DAYTODAY`` (defined below), a
copy of ``data_ctrl_dir_std`` whose ``xx_gentim2d_weight(8)`` names the
day-to-day ``_Pa`` weight the reruns actually used. ``DATA_CTRL_DIR_STD`` still
names the *sub-daily* std file and must not be used here -- the relcon of the
p_atm control is computed against whatever sigma that names, so a mismatch
silently mis-weights (c)'s STD bars.

Panel (a) and the sigma used by (b) both come from the **Pa-corrected** weight
file ``wApressure_jra2012_daytoday_std_Pa.bin`` (see
``gen_patm_daytoday_weight_Pa.py``); the original
``wApressure_jra2012_daytoday_std.bin`` was written in hPa and is what the
*old*, superseded std runs used.

Run as:

    module load texlive
    conda activate /work2/08381/goldberg/ls6/miniforge3/envs/esmpy_3.10
    cd /work2/08381/goldberg/ls6/smartosse
    python -m smartosse.figures.gen_appendixB_skill_cache   # once, ~12 min
    python -m smartosse.figures.figB_patm_std_4panel
"""
import os

import numpy as np
import xarray as xr
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import cartopy.crs as ccrs

from .figs_utils import add_panel_label
from .fig9_patm_unc import (
    REGIONS,
    REGION_COLORS,
    REGION_LABELS,
    WEIGHT_DIR,
    RUN_DIR_ROOT_STD,
    RUN_DIR_ROOT_SPREAD,
    DATA_CTRL_DIR_STD,
    DATA_CTRL_DIR_SPREAD,
    load_sigma_patm,
    load_sigma_patm_std_map,
    load_relcon_per_region,
    get_cable_sensor_args,
    get_cable_lonlat,
    plot_sigma_patm_map,
    plot_relcon_bars_grouped,
    _relcon_shade_legend_handles,
    _relcon_hatch_legend_handles,
)
from .fig9_spread_3panel import (
    RATIO_LEGEND_FONTSIZE,
    load_global_ratio_series,
    plot_patm_adjustment_ratio,
)
from .gen_appendixB_skill_cache import SKILL_CACHE, available_regions

# -----------------------------------------------------------------------------
# Panel styling constants -- edit these (not the make_figB() body) to retune.
# -----------------------------------------------------------------------------

# The Pa-corrected day-to-day-std weight file. NOT fig9_patm_unc.SIGMA_STD_FNAME,
# which still names the hPa-valued original (kept there so the superseded runs
# stay reproducible).
SIGMA_STD_PA_FNAME = 'wApressure_jra2012_daytoday_std_Pa.bin'

# (c): the data.ctrl panel (c)'s STD bars are weighted against. NOT
# fig9_patm_unc.DATA_CTRL_DIR_STD, whose data.ctrl:66 names
# `wApressure_ASTE270_EXFpress_std_new.bin` -- the *sub-daily* std weight, not
# the day-to-day one these reruns were built around. Feeding that to
# ControlDataset silently divides the p_atm gradient by the wrong sigma and so
# mis-weights the p_atm bar against the wind bars.
#
# This is a NEW directory rather than an edit to the existing one:
# `data_ctrl_dir_std/data.ctrl` is a symlink into the live run template
# (`input_weight/data.ctrl_jrastd`), which is what actual model runs are
# launched from -- repointing it to serve a figure would change how a future
# run is configured. The new dir holds a real copy differing in exactly the one
# `xx_gentim2d_weight(8)` line; verified 8 controls <-> 8 weights, correctly
# paired, by `smartosse.utils.grep_ctrl`.
DATA_CTRL_DIR_STD_DAYTODAY = WEIGHT_DIR + 'data_ctrl_dir_std_daytoday/'

# Cables held out of every std-derived panel -- (b), (c) and (d). Empty since
# 2026-08-11 (evening): SPG's final iter0020 landed (files dated 15:31) and its
# adjoint gradients are no longer identically zero, so all four cables are back.
# Kept as a switch rather than deleted: `valid_gradient_regions()` is the
# automatic guard against a broken run, this is the manual one for a run that is
# merely not final.
STD_EXCLUDE_REGIONS = ()

# (a): 0-20 hPa, an order of magnitude above Fig. 9a's 0-2 -- the whole point of
# the panel. SPNA-window values run 1.8-22 hPa (median 9.5).
SIGMA_MAP_KWARGS = dict(levels=np.linspace(0, 20, 11), extend='max', robust=False)
SIGMA_MAP_CBAR_KWARGS = dict(ticks=[0, 10, 20])

# (d): the SPNA window, matching smartosse.plot.spna()'s defaults (kept in sync
# by hand, as fig9_spread_3panel.make_fig9 does for the projection center).
SPNA_LON = (-80., 10.)
SPNA_LAT = (40., 80.)

# (d): fields scattered, their colors and their display labels. p_b in the
# GRACE-ish blue-grey and V_bt in a warm tone -- deliberately NOT REGION_COLORS,
# since here the color encodes the *field*, not the cable (the cables are
# pooled).
SCATTER_FLDS = ('bp', 'Vbt')
SCATTER_COLORS = {'bp': '#1b6ca8', 'Vbt': '#d1495b'}
SCATTER_LABELS = {'bp': r'$p_b$', 'Vbt': r'$V_{bt}$'}
# Symmetric and much tighter than skill's nominal (-inf, 1] range: over the SPNA
# window the 1st-99th percentiles are about [-0.5, +0.4] for both fields, so
# (-0.6, 0.6) leaves <1% of points outside the view (0.07% p_b, 0.76% V_bt)
# while keeping the 1:1 line on the box diagonal. The annotated RMS is computed
# on every point regardless.
# Widened from (-0.6, 0.6) on 2026-08-11: at 0.6 the "(d)" panel letter and the
# two RMS annotation lines were crowding each other in the top-left corner.
# Zooming out buys blank space there without hiding anything -- it only ever
# clipped <1% of points, and at 0.7 that drops further.
SCATTER_LIM = (-0.7, 0.7)
SCATTER_KWARGS = dict(s=1.5, alpha=0.12, linewidths=0, rasterized=True)

# (b): NOT Fig. 9b's ylim. The original plan was to match it exactly (0-1.7) so
# the eye could compare the two figures without a solid/dashed key -- that is no
# longer tenable, and the reason is the result itself. Under the day-to-day
# prior the whole-domain max |dp_atm|/sigma reaches 4.3 / 3.0 / 5.0 / 3.6
# (LS/SPG/NS/Nfl) and sits above 1 sigma on 3-39% of days, where under the
# spread prior it never exceeds 1.00 on any day for any cable. Clipping at 1.7
# would run every curve off the top of the panel for a quarter of January.
# The 1-sigma reference line and its shading are kept, so the cross-figure
# comparison survives as "Fig. 9b lives entirely inside the grey band; this
# panel does not".
RATIO_YLIM_STD = (0, 5.3)
RATIO_YTICKS_STD = (0, 1, 2, 3, 4, 5)

# (b): left edge of the legend, in axes fraction (Matt, 2026-08-11 -- moved from
# upper right). Inset far enough to clear the "(b)" panel letter at x=0.02; the
# curves' own tall excursions are late-January, on the right, so the left half of
# the top strip is the emptier one.
RATIO_LEGEND_X = 0.13

# (c): all bars a single neutral grey rather than one hue per cable (Matt,
# 2026-08-11). Cable identity is already carried by the x tick labels, so the
# colour was redundant -- and spending it on cable identity meant the only
# encoding left for the control group (the actual result) was a shade ramp
# within each hue. Grey frees the light/mid/dark ramp to mean one thing:
# other / winds / p_atm. This is also the value `_relcon_shade_legend_handles()`
# already uses for its neutral swatches, so the legend now shows the exact
# greys that appear in the bars instead of a stand-in.
RELCON_BAR_GREY = '0.55'

# (c): headroom above the stacked bars (which sum to 1.0). The bars stop at 1.0
# and the band above it holds the panel letter AND both legends (Matt asked for
# them inside that strip at a readable size), so it is much taller than the 1.18
# that fitted a letter alone.
#
# The two legends are STACKED, not side by side. At fontsize 16 the shade key
# (3 entries) and the hatch key (2 entries) are together about as wide as the
# whole axes, so laid out in one row they overlapped in the middle ("winds" ran
# through the STD swatch) -- the same collision that forced fontsize down to
# 11.5 when they sat above the axes. Stacking spends the headroom, which is
# free, instead of the font size, which is what was asked for.
RELCON_YLIM_TOP = 1.75
RELCON_LEGEND_FONTSIZE = 16
RELCON_LEGEND_TITLE_FONTSIZE = 17
# Left edge of both legends, in axes fraction -- clear of the "(c)" panel letter
# at x=0.02.
RELCON_LEGEND_X = 0.24
# Vertical gap between the two stacked legends, in axes fraction.
RELCON_LEGEND_DY = 0.185

PANEL_LABEL_FONTSIZE = 40
PLACEHOLDER_FONTSIZE = 15


# =============================================================================
# Loaders
# =============================================================================

def load_sigma_patm_std_pa(weight_dir=WEIGHT_DIR, fname=SIGMA_STD_PA_FNAME):
    """ASTE-gridded day-to-day-std sigma_patm [Pa], from the Pa-corrected weight.

    Panel (b) divides the adjustment by this pointwise, exactly as the cost
    function does (w = sigma^-2), so it has to be the weight the OSSEs actually
    ran with -- not the lat/lon plotting field panel (a) shows.
    """
    return load_sigma_patm(fname, weight_dir=weight_dir)


def load_cable_lonlat(ds, regions=REGIONS, mo_str='201201'):
    """{region: (lons, lats)} for (a)'s sensor dots, straight from the synthetic
    p_b binaries.

    ``fig9_spread_3panel`` gets these out of ``load_row2_data``, which also loads
    each run's xx_apressure -- unavailable here (see the module docstring), and
    unnecessary for dots.
    """
    return {region: get_cable_lonlat(ds, get_cable_sensor_args(region, mo_str=mo_str))
            for region in regions}


def has_patm_adjustment(run_dir_root=RUN_DIR_ROOT_STD, regions=REGIONS, iternum=20):
    """True if every region has the xx_apressure.effective file panel (b) reads."""
    regions = available_regions(run_dir_root, regions, iternums=(iternum,))
    if not regions:
        return False
    return all(os.path.isfile(f'{run_dir_root.rstrip("/")}/{region}/iter{iternum:04d}/'
                              f'xx_apressure.effective.{iternum:010d}.data')
               for region in regions)


def has_control_set(run_dir_root=RUN_DIR_ROOT_STD, regions=REGIONS, iternum=20):
    """True if every region has the ``adxx_*`` gradient set panel (c) reads.

    What ``smartuq.ctrl.ControlDataset`` actually reads out of the iteration
    directory is ``ad{ctrl}.{iter}.data`` for each control named in data.ctrl --
    i.e. the plain ``adxx_*`` adjoint gradients, *not* ``xx_*`` and *not* the
    ``.effective`` variants. The control list and the weight filenames come from
    ``data_ctrl_dir``/``weight_dir``, which ``load_relcon_grouped`` passes
    explicitly (``DATA_CTRL_DIR_STD`` / ``WEIGHT_DIR``, both local to this
    machine), so the run's *own* data.ctrl is never opened and its absence does
    not block the panel. Probing for it -- as this function used to -- reported
    the panel unbuildable for the wrong reason and would have kept reporting so
    even after the gradients arrived.
    """
    regions = available_regions(run_dir_root, regions, iternums=(iternum,))
    if not regions:
        return False
    for region in regions:
        iter_dir = f'{run_dir_root.rstrip("/")}/{region}/iter{iternum:04d}/'
        for ctrl in ('adxx_uwind', 'adxx_vwind', 'adxx_apressure'):
            if not os.path.isfile(iter_dir + f'{ctrl}.{iternum:010d}.data'):
                return False
    return True


def valid_gradient_regions(run_dir_root=RUN_DIR_ROOT_STD, regions=REGIONS, iternum=20,
                           ctrls=('adxx_apressure', 'adxx_uwind', 'adxx_vwind'),
                           verbose=True):
    """Regions whose ``adxx_*`` gradients are actually usable, not just present.

    Existence is not enough. In the 2026-08-11 gradient transfer ``subgyre``'s
    ``adxx_apressure`` / ``adxx_uwind`` / ``adxx_vwind`` are **identically zero**
    over all 4 691 648 elements, and its remaining gradients are ~8 orders of
    magnitude smaller than the other cables' (``adxx_atemp`` absmax 1.2e-01 vs
    1.7e+08 for labsea). Its forward controls (``xx_*.effective``) are healthy,
    and its files are dated 2026-08-11 13:24 against 2026-08-08/10 for the other
    three -- so the run itself is fine and only its adjoint output is bad.

    A zero gradient is not a benign missing value here: ``ControlDataset`` forms
    ``std_cost = sum((adxx*unc)^2)^0.5`` and then normalizes by its sum over
    controls, so zero p_atm and wind gradients do not blank those bars -- they
    silently renormalize the *remaining* controls to 1.0, and subgyre plots as a
    confident, entirely wrong ``other = 1.00`` bar. That is worse than a gap,
    hence this check rather than trusting file presence.
    """
    from ..utils import read_aste_bin

    out = []
    for region in regions:
        iter_dir = f'{run_dir_root.rstrip("/")}/{region}/iter{iternum:04d}/'
        ok = True
        for ctrl in ctrls:
            fname = f'{iter_dir}{ctrl}.{iternum:010d}.data'
            if not os.path.isfile(fname):
                ok = False
                break
            if float(np.nanmax(np.abs(read_aste_bin(fname).values))) == 0.:
                ok = False
                if verbose:
                    print(f'[figB] {region}: {ctrl} is identically zero -- '
                          f'excluded from panel (c)')
                break
        if ok:
            out.append(region)
    return out


def load_skill_scatter(
    ds,
    cache_path=SKILL_CACHE,
    regions=REGIONS,
    flds=SCATTER_FLDS,
    spna_lon=SPNA_LON,
    spna_lat=SPNA_LAT,
):
    """{fld: (spread_skill, std_skill)} -- flat arrays of paired SPNA grid points.

    Reads the cache written by ``gen_appendixB_skill_cache.py`` (skill maps with
    dims (run, region, tile, j, i)), restricts to the SPNA window that
    ``plot.spna()`` draws, drops points where either run is NaN (land, or a
    region whose run is missing), and pools the cables into one flat pair of
    arrays per field.

    Pairing is per grid point *within* a cable experiment: point k of the LS
    spread run is matched to point k of the LS std run. Pooling across cables is
    just concatenation of those pairs.
    """
    with xr.open_dataset(cache_path) as cache:
        cache = cache.load()

    in_spna = ((ds.XC >= spna_lon[0]) & (ds.XC <= spna_lon[1])
               & (ds.YC >= spna_lat[0]) & (ds.YC <= spna_lat[1]))

    out = {}
    for fld in flds:
        var = cache[f'skill_{fld}']
        xs, ys = [], []
        for region in regions:
            if region not in list(cache.region.values):
                continue
            spread = var.sel(run='spread', region=region).where(in_spna)
            std = var.sel(run='std', region=region).where(in_spna)
            both = np.isfinite(spread.values) & np.isfinite(std.values)
            xs.append(spread.values[both])
            ys.append(std.values[both])
        out[fld] = (np.concatenate(xs), np.concatenate(ys)) if xs else (np.array([]), np.array([]))
    return out


# =============================================================================
# Panel (d)
# =============================================================================

def plot_skill_scatter(
    ax,
    skill_data,          # {fld: (spread, std)} from load_skill_scatter()
    flds=SCATTER_FLDS,
    colors=None,
    labels=None,
    lim=SCATTER_LIM,
    scatter_kwargs=None,
    rms_in_legend=True,
    annotate=False,
    annotate_fontsize=16,
    annotate_xy=(0.04, 0.87),   # clears the "(d)" panel label at (0.02, 0.98)
    tick_labelsize=20,
    label_fontsize=22,
    legend=True,
    legend_fontsize=None,
):
    """Panel (d): std-OSSE skill against spread-OSSE skill, 1:1 line, RMS deviation.

    One point per SPNA grid cell per cable experiment, cables pooled, colored by
    field. The claim the panel makes is geometric: points on the diagonal are
    grid cells whose skill is unchanged by swapping the p_atm prior, and the
    RMS deviation from that diagonal is how far off it they sit on average.

    `rms_in_legend` (default) folds each field's RMS into its legend entry, so
    the field names appear once rather than once in a corner annotation and
    again in the legend swatches. Setting it False and `annotate=True` restores
    the older split layout.

    `lim` clips the view (skill is unbounded below -- 1 - rms_after/rms_before
    goes to -inf as rms_before -> 0), so the fraction of points falling outside
    is reported alongside the RMS, which is computed on **all** points, clipped
    or not.
    """
    colors = colors or SCATTER_COLORS
    labels = labels or SCATTER_LABELS
    sk = dict(**SCATTER_KWARGS)
    sk.update(scatter_kwargs or {})

    ax.axline((0, 0), slope=1, color='k', lw=1.4, ls=(0, (1, 1)), zorder=3)

    lines = []
    for fld in flds:
        x, y = skill_data[fld]
        ax.scatter(x, y, color=colors[fld], zorder=2, **sk)
        lines.append(f'{labels[fld]}: RMS $=${_rms_deviation(x, y):.3f}')

    if annotate and lines:
        ax.text(*annotate_xy, '\n'.join(lines), transform=ax.transAxes,
                va='top', ha='left', fontsize=annotate_fontsize)

    ax.set_xlim(*lim)
    ax.set_ylim(*lim)
    ax.set_aspect('equal', adjustable='box')
    ax.tick_params(labelsize=tick_labelsize)
    ax.set_xlabel(r'skill, $\sigma_{p_{\mathrm{atm}}}^{\mathrm{spread}}$ OSSE',
                  fontsize=label_fontsize)
    ax.set_ylabel(r'skill, $\sigma_{p_{\mathrm{atm}}}^{\mathrm{std}}$ OSSE',
                  fontsize=label_fontsize)
    ax.grid(alpha=0.3)
    ax.set_axisbelow(True)

    if legend:
        # Proxy handles at full opacity -- the scattered points are alpha~0.1,
        # which is illegible at legend-swatch size. Labels carry the RMS unless
        # it has been put in a separate annotation instead.
        legend_labels = lines if rms_in_legend else [labels[f] for f in flds]
        handles = [Line2D([0], [0], marker='o', ls='none', color=colors[f],
                          markersize=9, label=lab)
                   for f, lab in zip(flds, legend_labels)]
        ax.legend(handles=handles, fontsize=legend_fontsize or (tick_labelsize - 2),
                  frameon=False, loc='lower right')
    return ax


def _rms_deviation(x, y):
    """RMS distance from the 1:1 line, i.e. rms(y - x)."""
    if len(x) == 0:
        return np.nan
    return float(np.sqrt(np.mean((np.asarray(y) - np.asarray(x)) ** 2)))


def skill_scatter_summary(skill_data, flds=SCATTER_FLDS, lim=SCATTER_LIM):
    """Printable per-field stats for the caption -- n, RMS deviation, medians."""
    rows = []
    for fld in flds:
        x, y = skill_data[fld]
        if len(x) == 0:
            rows.append(f'{fld}: no data')
            continue
        outside = np.mean((x < lim[0]) | (x > lim[1]) | (y < lim[0]) | (y > lim[1]))
        rows.append(
            f'{fld}: n={len(x)}  rms(std-spread)={_rms_deviation(x, y):.4f}  '
            f'median spread={np.median(x):+.4f}  median std={np.median(y):+.4f}  '
            f'median diff={np.median(y - x):+.4f}  outside view={100 * outside:.2f}%'
        )
    return '\n'.join(rows)


# =============================================================================
# Placeholder for panels whose inputs the rerun hasn't shipped yet
# =============================================================================

def _pending_panel(ax, text, fontsize=PLACEHOLDER_FONTSIZE):
    """Blank framed axes carrying an explanation, for a panel that can't be built.

    Deliberately not silently omitted -- keeping the box means the preliminary
    render has the final layout, and the reason is on the figure rather than
    only in a log line.
    """
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_edgecolor('0.7')
        spine.set_linestyle((0, (4, 4)))
    ax.text(0.5, 0.5, text, transform=ax.transAxes, ha='center', va='center',
            fontsize=fontsize, color='0.35', linespacing=1.5)
    return ax


# =============================================================================
# Full-figure assembly
# =============================================================================

def make_figB(
    ds,
    sigma_std_map=None,
    sigma_std=None,
    relcon_per_region=None,
    ratio_data=None,
    skill_data=None,
    cable_lonlat=None,
    regions=REGIONS,
    figsize=(15, 12),
    landfacecolor='white',
    skip_unavailable=True,
    verbose=True,
):
    """Assemble the 2x2 appendix figure: (a) map, (b) ratio, (c) bars, (d) scatter.

    Pass in already-loaded pieces so a notebook can load once and iterate on
    layout quickly; anything left as None is loaded here.

    `skip_unavailable=True` (default) renders (b)/(c) as annotated placeholders
    when the std runs lack the control files they need, instead of raising --
    see the module docstring. `regions` is intersected with what the std run set
    actually contains, so the missing SPG experiment drops out of (b)/(c)/(d)
    while (a) keeps all four cables' sensor dots.
    """
    run_regions = [r for r in available_regions(RUN_DIR_ROOT_STD, regions)
                   if r not in STD_EXCLUDE_REGIONS]
    dropped = [r for r in regions if r not in run_regions]
    if dropped and verbose:
        print(f'[figB] excluded from the std side: {", ".join(dropped)} -- '
              f'(b)/(c)/(d) cover {", ".join(run_regions)}')

    sigma_std_map = sigma_std_map if sigma_std_map is not None else load_sigma_patm_std_map()
    if cable_lonlat is None:
        cable_lonlat = load_cable_lonlat(ds, regions=regions)

    spna_proj = ccrs.LambertConformal(central_longitude=-35, central_latitude=60)

    fig = plt.figure(figsize=figsize)
    # hspace kept modest: (a) is a cartopy axes at its projection's own aspect,
    # so it can't fill its cell horizontally, and a large row gap on top of that
    # reads as a hole in the middle of the figure.
    gs = fig.add_gridspec(2, 2, width_ratios=[1.0, 1.0], height_ratios=[1.0, 1.0],
                          wspace=0.28, hspace=0.22)

    ax_a = fig.add_subplot(gs[0, 0], projection=spna_proj)
    ax_b = fig.add_subplot(gs[0, 1])
    ax_c = fig.add_subplot(gs[1, 0])
    ax_d = fig.add_subplot(gs[1, 1])

    # ------------------------------------------------------------------ (a)
    # Same construction as fig9_spread_3panel's (a) -- decorate a bare GeoAxes
    # with spna(), then contourf the lat/lon sigma field over it -- only the
    # levels/ticks differ (0-20 hPa vs 0-2).
    from .fig9_patm_unc import spna
    _, ax_a = spna(ax=ax_a, landfacecolor=landfacecolor)
    _, cb_a, _ = plot_sigma_patm_map(
        sigma_std_map, ax=ax_a, cable_lonlat=cable_lonlat,
        add_colorbar=True,
        cbar_kwargs=dict(orientation='horizontal', shrink=0.85, pad=0.11,
                         **SIGMA_MAP_CBAR_KWARGS),
        **SIGMA_MAP_KWARGS,
    )
    cb_a.ax.tick_params(labelsize=18)
    cb_a.ax.set_xlabel('[hPa]', fontsize=20)
    add_panel_label(ax_a, 'a', fontsize=PANEL_LABEL_FONTSIZE)

    # ------------------------------------------------------------------ (b)
    if ratio_data is None and run_regions and has_patm_adjustment(regions=run_regions):
        sigma_std = sigma_std if sigma_std is not None else load_sigma_patm_std_pa()
        ratio_data = load_global_ratio_series(sigma_std, regions=run_regions,
                                              run_dir_root=RUN_DIR_ROOT_STD)
    if ratio_data is not None:
        plot_patm_adjustment_ratio(
            ax_b, ratio_data, regions=list(ratio_data), ytick_fontsize=18,
            ylabel_fontsize=20, legend=True,
            ylim=RATIO_YLIM_STD, yticks=RATIO_YTICKS_STD,
            # Upper LEFT, but inset to RATIO_LEGEND_X rather than flush at 0.0:
            # the "(b)" panel letter sits at x=0.02 and is fontsize 40, so a
            # flush-left legend runs straight through it.
            legend_kwargs=dict(fontsize=RATIO_LEGEND_FONTSIZE, loc='upper left',
                               bbox_to_anchor=(RATIO_LEGEND_X, 1.0), ncol=2,
                               columnspacing=1.0,
                               handlelength=1.4, labelspacing=0.35))
        if verbose:
            for region, (_, v) in ratio_data.items():
                print(f'[figB] (b) {region:14s} max |dp_atm|/sigma: min={v.min():.2f} '
                      f'med={np.median(v):.2f} max={v.max():.2f} '
                      f'days>1sigma={100 * np.mean(v > 1):.0f}%')
    elif skip_unavailable:
        _pending_panel(ax_b, 'panel (b) pending\n\n'
                             r'needs $\mathtt{xx\_apressure.effective}$ from the'
                             '\ncorrected-weight std reruns\n(not in the 2026-08-11 transfer)')
    else:
        raise FileNotFoundError('panel (b): no xx_apressure.effective under '
                                f'{RUN_DIR_ROOT_STD}')
    add_panel_label(ax_b, 'b', fontsize=PANEL_LABEL_FONTSIZE, x=0.02, y=0.98)

    # ------------------------------------------------------------------ (c)
    # Not `run_regions`: presence of the gradient files is not enough, they also
    # have to be non-zero (see valid_gradient_regions -- subgyre's are not, and a
    # zero gradient renormalizes into a confident wrong bar rather than a gap).
    relcon_regions = (valid_gradient_regions(regions=run_regions, verbose=verbose)
                      if run_regions and has_control_set(regions=run_regions) else [])
    if relcon_per_region is None and relcon_regions:
        relcon_per_region = load_relcon_per_region(
            run_dir_root_std=RUN_DIR_ROOT_STD, run_dir_root_spread=RUN_DIR_ROOT_SPREAD,
            regions=relcon_regions, data_ctrl_dir_std=DATA_CTRL_DIR_STD_DAYTODAY,
            data_ctrl_dir_spread=DATA_CTRL_DIR_SPREAD)
    if relcon_per_region is not None:
        plot_relcon_bars_grouped(
            ax_c, relcon_per_region, regions=relcon_regions,
            # One neutral grey for every cable -- see RELCON_BAR_GREY.
            region_colors={r: RELCON_BAR_GREY for r in relcon_regions},
            xtick_fontsize=16, ytick_fontsize=18, ylabel_fontsize=20)
        # The bars stack to exactly 1.0, so everything above y=1 is blank canvas
        # (yticks stay 0/0.5/1 -- the strip is headroom, not extra range). Both
        # legends now live INSIDE it rather than above the axes, which is what
        # lets them run at fontsize 16 instead of the 11.5 they needed when they
        # had to share the narrow strip between the two figure rows.
        ax_c.set_ylim(0, RELCON_YLIM_TOP)
        # y=1.0 in data units, as an axes fraction, is the top of the bars --
        # anchoring both legends there keeps them off the bars no matter how
        # RELCON_YLIM_TOP is retuned.
        bar_top = 1.0 / RELCON_YLIM_TOP
        # Stacked, both anchored at the same left edge: the shade key (3 entries)
        # sits RELCON_LEGEND_DY above the hatch key (2 entries), which itself
        # sits on the bar tops. Side by side at this font size they overlap.
        shade_legend = ax_c.legend(
            handles=_relcon_shade_legend_handles(), fontsize=RELCON_LEGEND_FONTSIZE,
            frameon=False, loc='lower left',
            bbox_to_anchor=(RELCON_LEGEND_X, bar_top + RELCON_LEGEND_DY),
            ncol=3, title='control', title_fontsize=RELCON_LEGEND_TITLE_FONTSIZE,
            handlelength=1.3, columnspacing=1.0, handletextpad=0.5)
        ax_c.add_artist(shade_legend)   # else the second legend() replaces it
        ax_c.legend(
            handles=_relcon_hatch_legend_handles(), fontsize=RELCON_LEGEND_FONTSIZE,
            frameon=False, loc='lower left',
            bbox_to_anchor=(RELCON_LEGEND_X, bar_top),
            ncol=2, title=r'$\sigma_{p_{\mathrm{atm}}}$',
            title_fontsize=RELCON_LEGEND_TITLE_FONTSIZE,
            handlelength=1.3, columnspacing=1.0, handletextpad=0.5)
        # Compare against the full `regions`, not run_regions, so a cable held
        # out upstream by STD_EXCLUDE_REGIONS is still declared on the figure.
        excluded = [r for r in regions if r not in relcon_regions]
        if excluded:
            # Into the headroom strip, not the axes interior: the bars span the
            # full x range and stack to 1.0, so anything placed inside overlaps
            # them (a centred note at y=0.015 sat on top of the NS bars).
            # RELCON_YLIM_TOP puts the bar tops at 1/RELCON_YLIM_TOP in axes
            # fraction, leaving the band above ~0.87 free; right-aligned so it
            # clears the panel letter at x=0.02.
            ax_c.text(0.98, 0.97,
                      ', '.join(REGION_LABELS[r] for r in excluded)
                      + ' omitted (iter 20 not final)',
                      transform=ax_c.transAxes, ha='right', va='top',
                      fontsize=11, color='0.35')
        if verbose:
            for run_name in ('std', 'spread'):
                for region in relcon_regions:
                    da = relcon_per_region[run_name][region]
                    vals = '  '.join(f'{g}={float(da.sel(group=g)):.3f}'
                                     for g in da.group.values)
                    print(f'[figB] (c) {run_name:6s} {region:14s} {vals}')
    elif skip_unavailable:
        _pending_panel(ax_c, 'panel (c) pending\n\n'
                             r'needs the $\mathtt{adxx\_*}$ gradients'
                             '\nfrom the corrected-weight std reruns\n'
                             '(not in the 2026-08-11 transfer)')
    else:
        raise FileNotFoundError(f'panel (c): no control set under {RUN_DIR_ROOT_STD}')
    add_panel_label(ax_c, 'c', fontsize=PANEL_LABEL_FONTSIZE, x=0.02, y=0.98)

    # ------------------------------------------------------------------ (d)
    if skill_data is None:
        skill_data = load_skill_scatter(ds, regions=run_regions)
    plot_skill_scatter(ax_d, skill_data)
    if verbose:
        print(skill_scatter_summary(skill_data))
    add_panel_label(ax_d, 'd', fontsize=PANEL_LABEL_FONTSIZE, x=0.02, y=0.98)

    return fig, dict(a=ax_a, b=ax_b, c=ax_c, d=ax_d)


if __name__ == '__main__':
    from ..dataset import open_astedataset
    from .figs_utils import use_latex_times, use_embedded_pdf_fonts

    use_latex_times()
    use_embedded_pdf_fonts()

    ds = open_astedataset()
    fig, axes = make_figB(ds)

    out_base = os.path.join(os.path.dirname(__file__), 'output', 'figB_patm_std_4panel')
    os.makedirs(os.path.dirname(out_base), exist_ok=True)
    fig.savefig(out_base + '.png', dpi=300, bbox_inches='tight')
    fig.savefig(out_base + '.pdf', bbox_inches='tight')
    print('wrote', out_base + '.png', 'and', out_base + '.pdf')
