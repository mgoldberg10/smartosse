"""
Fig. 9 (3-panel, spread-only rendition) -- p_atm uncertainty, adjustment, and
attribution, all for the Chaudhuri reanalysis-SPREAD prior only.

This is a slimmed-down sibling of ``fig9_patm_unc.py``'s 2x2 mosaic. Where that
figure showed STD *and* SPREAD side by side (two maps, solid/dashed timeseries
pairs, plain/hatched bar pairs), this one drops the STD half entirely and lays
the three remaining SPREAD panels out in a single row:

    (a) sigma_patm SPREAD spatial field                 [map + cable dots]
        -- same as fig9_patm_unc.py's panel (b), but vmax=2 hPa.
    (b) all 4 partial cables' NORMALIZED adjustment time series, ONE shared
        axes: max over the *whole domain* of |dp_atm(x,t)| / sigma_patm(x),
        SOLID, one curve per cable experiment, with a reference line at 1 and
        the "within 1 sigma" region shaded. ylim = [0, ~1.15].
    (c) per-cable SPREAD relcon, one stacked bar per cable (four stacked bars
        in the legend's own light/mid/dark GREY, no hatch, no STD bar, no
        sigma_patm hatch legend). x labels drop the "_cable" suffix
        (LS/SPG/NS/Nfl).

REVIEWER-DRIVEN REVISION (round 3) -- panels (b) and (c) both changed:

  (b) previously plotted, in [hPa], each cable's max-over-*its own sensors*
      |dp_atm| against a single constant grey band (+/- the mean of the four
      cables' sensor-mean sigma_spread, ~0.65 hPa). The reviewer objected
      that a constant uncertainty is inconsistent with the heterogeneous
      field shown in (a), and asked for the GLOBAL max adjustment. Those two
      requests are coupled: the global max does *not* occur at the cables
      (e.g. the LS experiment's is 2.66 hPa in the Lincoln Sea on Jan 30,
      where sigma_spread is 2.85 hPa), so plotting it against a cable-derived
      constant band would read as a gross violation of the plausibility bound
      when it is nothing of the sort. Normalizing by sigma_patm(x) pointwise
      resolves both at once: sigma enters exactly as it does in the cost
      function (w = sigma^-2), the grey region becomes an exact statement
      rather than an assumption, and the result is strictly stronger -- the
      adjustment never exceeds the local 1-sigma reanalysis spread anywhere
      in the domain on any day (max ratios: LS 0.997, SPG 0.537, NS 0.592,
      Nfl 0.493). Dropping the sign-symmetric band also frees the negative
      half of the axis, which the (magnitude-only) curves never used.
      NB: the *dimensional* numbers should stay in the caption/text so the
      physical magnitude isn't lost -- see the table above.
  (c) previously colored each cable's stack in that cable's own base color
      (3 shades), while the legend key was drawn in neutral grey -- so the
      legend didn't actually match the bars. Per the reviewer, the bars now
      use the legend's greys directly (cable identity is already carried by
      the x labels); no colored border. Cable color still ties (a) to (b).

Row layout: (a) and (b) get similar widths; (c) (the relcon bars) gets the
skinniest column.

Everything reuses ``fig9_patm_unc.py``'s loaders and low-level helpers -- only
the three spread-only plotting variants and the row assembly live here. See
that module's docstring for the data-provenance / data-availability / time-
ordering caveats (they all still apply, unchanged).
"""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from matplotlib.lines import Line2D
import cartopy.crs as ccrs

from .figs_utils import add_panel_label, latex_escape
from .fig9_patm_unc import (
    REGIONS,
    REGION_LABELS,
    REGION_COLORS,
    RELCON_GROUP_ORDER,
    REGION_SHADE_FACTORS,
    RELCON_GROUP_LABELS,
    SIGMA_BAND_LABEL,
    STD_LINE_STYLE,
    RUN_DIR_ROOT_SPREAD,
    _shade_color,
    region_group_colors,
    load_sigma_patm_spread_map,
    load_sigma_patm_spread,
    load_patm_adjustment,
    load_relcon_per_region,
    load_row2_data,
    plot_sigma_patm_map,
    _relcon_shade_legend_handles,
    _style_time_axis,
)

# -----------------------------------------------------------------------------
# Panel styling constants -- edit these (not the make_fig9() body) to retune.
# -----------------------------------------------------------------------------

# (a): vmax=2 hPa (was 0-3 shared with the STD panel in the 2x2 layout).
SIGMA_MAP_KWARGS = dict(levels=np.linspace(0, 2, 11), extend='max', robust=False)
SIGMA_MAP_CBAR_KWARGS = dict(ticks=[0, 1, 2])

# (b): spread curves solid (STD_LINE_STYLE is the solid one in fig9_patm_unc.py).
SPREAD_SOLID_STYLE = dict(**STD_LINE_STYLE)

# (b), normalized rendition: axis label and the "within 1 sigma" reference.
# Subscript is (i,j), not a bold x: the paper introduces i and j as the
# horizontal grid indices before this figure, so the max is written over the
# indices the reader already has rather than over a vector symbol defined
# nowhere. Changed 2026-08-11 at Matt's request. NB this constant is shared with
# Appendix B's figB_patm_std_4panel panel (b) -- deliberately, the two panels are
# meant to be flipped between -- so **Fig. 9's saved PDF is now stale and must be
# regenerated** (`python -m smartosse.figures.fig9_spread_3panel`) for the two to
# agree.
RATIO_YLABEL = r'$\max_{i,j}\,|\delta p_{\mathrm{atm}}|\,/\,\sigma_{p_{\mathrm{atm}}}$'
RATIO_BAND_LABEL = r'within $1\sigma_{p_{\mathrm{atm}}}$'
RATIO_REF_LINE_STYLE = dict(color='k', ls=(0, (1, 1)), lw=1.6)  # densely dotted, at ratio = 1

# (b): legend fontsize, and the ylim headroom above the ratio=1 reference line
# that the legend has to fit inside. The two are coupled -- the legend is now
# 3 rows (see make_fig9) at a bigger fontsize than the old 2-row version, so
# the empty strip above the reference line was raised to match.
RATIO_LEGEND_FONTSIZE = 18
RATIO_YLIM = (0, 1.7)

# (c): the neutral grey the relcon shade legend is drawn in
# (_relcon_shade_legend_handles' `neutral` default) -- the bars now use the
# same greys, so the legend is literally the key.
RELCON_NEUTRAL_GREY = '0.55'

PANEL_LABEL_FONTSIZE = 40


# =============================================================================
# Loaders
# =============================================================================

def load_global_ratio_series(
    sigma_spread=None,
    regions=REGIONS,
    mo_str='201201',
    iternum=20,
    run_dir_root=RUN_DIR_ROOT_SPREAD,
    reverse_time=True,
    ocean_mask=None,
):
    """{region: (time, ratio)} -- panel (b)'s global normalized adjustment.

    For each partial-cable experiment, `ratio[t] = max_x |dp_atm(x, t)| /
    sigma_patm(x)`, the maximum taken over the **entire model domain**, not
    just that cable's sensors (the reviewer's "GLOBAL max"), and normalized
    pointwise by the same reanalysis-spread sigma that weights the control in
    the cost function (w = sigma^-2).

    `sigma_spread` is the ASTE-gridded sigma [Pa] from
    ``fig9_patm_unc.load_sigma_patm_spread()`` -- the *weight-file* field, not
    the lat/lon plotting field of panel (a), since it has to be divided into
    the adjustment on the model's own grid. That field is already NaN wherever
    the weight is zero (land / unconstrained points), so `np.nanmax` masks the
    domain for free; passing an explicit boolean `ocean_mask` (e.g.
    ``ds.hFacC.isel(k=0) > 0``) is supported but was verified on 2026-08-05 to
    give bit-identical maxima for all four cables, so it's off by default.

    Returns {region: (DatetimeIndex, np.ndarray)}; the ratio is dimensionless.
    """
    sigma_spread = sigma_spread if sigma_spread is not None else load_sigma_patm_spread()

    start = pd.to_datetime(mo_str, format='%Y%m')
    datetimes = pd.date_range(start=start, end=start + pd.offsets.MonthEnd(1), freq='D')

    sig = np.asarray(sigma_spread)
    if ocean_mask is not None:
        sig = np.where(np.asarray(ocean_mask), sig, np.nan)

    out = {}
    for region in regions:
        adj = load_patm_adjustment(run_dir_root, region, iternum=iternum,
                                   datetimes=datetimes, reverse_time=reverse_time)
        ratio = np.abs(np.asarray(adj)) / sig[None]           # (time, tile, j, i)
        out[region] = (datetimes, np.nanmax(ratio.reshape(len(datetimes), -1), axis=1))
    return out


# =============================================================================
# Spread-only plotting variants
# =============================================================================

def _reduce_over_sensors(da, how):
    """Collapse a cable's (time, sensor) |dp_atm| [hPa] over its sensors.

    `how` is 'mean' (the cable-mean adjustment) or 'max' (the largest-magnitude
    sensor at each time, i.e. abs(dpatm).max('sensor')/100 -- shows the worst-
    case cable point rather than the average). No-op if there's no sensor dim.
    """
    da = np.abs(da) / 100.
    sensor_dim = 'sensor' if 'sensor' in da.dims else None
    if sensor_dim is None:
        return da
    return da.max(sensor_dim) if how == 'max' else da.mean(sensor_dim)


def plot_patm_adjustment_spread(
    ax,
    row2_data,
    regions=REGIONS,
    region_labels=None,
    region_colors=None,
    sigma_band_hpa=None,
    sensor_reduce='mean',
    yticks=(-1, 0, 1),
    ylim=(-1.2, 1.2),
    tick_labelsize=16,
    ytick_fontsize=None,
    ylabel='[hPa]',
    ylabel_fontsize=20,
    legend=True,
    legend_kwargs=None,
    band_kwargs=None,
    line_kwargs=None,
):
    """Panel (b): all 4 cables' SPREAD |dp_atm| on one shared axes.

    SPREAD-only rendition of ``fig9_patm_unc.plot_patm_adjustment_combined``:
    drops the STD curves and the P&D 2003 line, and draws the remaining
    (spread) curves SOLID instead of dashed. The shared +/-sigma_spread
    envelope is kept. Color = cable identity (REGION_COLORS), matching (a)'s
    map dots and (c)'s bars; cable identity is carried by a traditional legend
    (`legend=True`) rather than end-of-line labels.

    `sensor_reduce` picks how each cable's sensors are collapsed to one curve:
    'mean' (cable-mean adjustment) or 'max' (abs(dpatm).max('sensor')/100, the
    worst-case sensor at each time).
    """
    region_labels = region_labels or REGION_LABELS
    region_colors = region_colors or REGION_COLORS

    time = np.asarray(row2_data[regions[0]]['time'])

    if sigma_band_hpa is None:
        sigma_band_hpa = float(np.mean([row2_data[r]['sigma_band_hpa'] for r in regions]))

    line_style = dict(**SPREAD_SOLID_STYLE)
    line_style.update(line_kwargs or {})

    for region in regions:
        d = row2_data[region]
        color = region_colors.get(region, 'k')
        vals = np.asarray(_reduce_over_sensors(d['adj_spread'], sensor_reduce))
        ax.plot(time, vals, color=color, label=region_labels[region], **line_style)

    # Shared +/-sigma_spread envelope (mean of the 4 cables' bands), un-colored.
    bk = dict(color='0.5', alpha=0.3, edgecolor='none', label=SIGMA_BAND_LABEL, zorder=0)
    bk.update(band_kwargs or {})
    ax.fill_between(time, -sigma_band_hpa, sigma_band_hpa, **bk)

    _style_time_axis(ax, time, yticks=yticks, ylim=ylim, tick_labelsize=tick_labelsize)

    ytick_fontsize = tick_labelsize if ytick_fontsize is None else ytick_fontsize
    ax.set_ylabel(ylabel, fontsize=ylabel_fontsize)
    ax.tick_params(axis='y', labelsize=ytick_fontsize)

    if legend:
        handles = [Line2D([0], [0], color=region_colors.get(r, 'k'),
                          label=region_labels[r], **line_style) for r in regions]
        handles.append(Patch(facecolor='0.5', alpha=0.3, edgecolor='none', label=SIGMA_BAND_LABEL))
        lk = dict(fontsize=14, frameon=False, loc='upper left', ncol=1)
        lk.update(legend_kwargs or {})
        ax.legend(handles=handles, **lk)

    return ax


def plot_patm_adjustment_ratio(
    ax,
    ratio_data,          # {region: (time, ratio)} from load_global_ratio_series()
    regions=REGIONS,
    region_labels=None,
    region_colors=None,
    yticks=(0, 0.5, 1),
    # Headroom above `ref_level` on purpose: every curve is <= 1 by
    # construction of the result, so the strip above the reference line is
    # guaranteed-empty space for the legend to sit in without colliding with
    # anything (the LS spike touches 1.0 on Jan 30). It also stops the
    # "within 1 sigma" shading from filling the entire panel, which reads as a
    # grey background rather than as a bounded acceptable region.
    ylim=RATIO_YLIM,
    ref_level=1.,
    shade_below_ref=True,
    tick_labelsize=16,
    ytick_fontsize=None,
    ylabel=RATIO_YLABEL,
    ylabel_fontsize=20,
    legend=True,
    legend_kwargs=None,
    legend_handle_order=None,
    band_kwargs=None,
    ref_line_kwargs=None,
    line_kwargs=None,
):
    """Panel (b): global max |dp_atm| / sigma_patm, one curve per cable experiment.

    Replaces ``plot_patm_adjustment_spread`` (kept below/above as the previous
    [hPa]-units rendition) -- see this module's docstring for why the switch to
    a pointwise-normalized, whole-domain maximum answers both halves of the
    reviewer's panel-(b) comment. Color = cable identity (REGION_COLORS),
    matching (a)'s map dots; (c)'s bars are now grey, so this and (a) are where
    the cable palette lives.

    The grey shading is the ``ratio <= ref_level`` region ("within 1 sigma"),
    an exact statement about the plotted quantity rather than an assumed
    constant uncertainty, and `ref_level` is drawn as a black dotted line on
    top of it. Curves are magnitudes, so the axis starts at 0 (the old
    +/-band rendition wasted the negative half).

    `legend_handle_order` reorders the ``[*cables, band]`` handle list before
    it's handed to ``ax.legend``. Needed because matplotlib fills legend cells
    COLUMN-major, so handle order != on-screen reading order for any ncol > 1
    layout -- see make_fig9() for the 3-row x 2-col arrangement this figure
    uses and the permutation that produces it.
    """
    region_labels = region_labels or REGION_LABELS
    region_colors = region_colors or REGION_COLORS

    line_style = dict(**SPREAD_SOLID_STYLE)
    line_style.update(line_kwargs or {})

    time = np.asarray(ratio_data[regions[0]][0])

    if shade_below_ref:
        bk = dict(color='0.5', alpha=0.22, edgecolor='none', label=RATIO_BAND_LABEL, zorder=0)
        bk.update(band_kwargs or {})
        ax.fill_between(time, 0., ref_level, **bk)

    rk = dict(zorder=1, **RATIO_REF_LINE_STYLE)
    rk.update(ref_line_kwargs or {})
    ax.axhline(ref_level, **rk)

    for region in regions:
        t, vals = ratio_data[region]
        ax.plot(np.asarray(t), np.asarray(vals), color=region_colors.get(region, 'k'),
                label=region_labels[region], zorder=2, **line_style)

    _style_time_axis(ax, time, yticks=yticks, ylim=ylim, tick_labelsize=tick_labelsize)

    ytick_fontsize = tick_labelsize if ytick_fontsize is None else ytick_fontsize
    ax.set_ylabel(ylabel, fontsize=ylabel_fontsize)
    ax.tick_params(axis='y', labelsize=ytick_fontsize)

    if legend:
        handles = [Line2D([0], [0], color=region_colors.get(r, 'k'),
                          label=region_labels[r], **line_style) for r in regions]
        if shade_below_ref:
            handles.append(Patch(facecolor='0.5', alpha=0.3, edgecolor='none',
                                 label=RATIO_BAND_LABEL))
        if legend_handle_order is not None:
            handles = [handles[i] for i in legend_handle_order]
        lk = dict(fontsize=14, frameon=False, loc='upper left', ncol=1)
        lk.update(legend_kwargs or {})
        ax.legend(handles=handles, **lk)

    return ax


def plot_relcon_bars_spread(
    ax,
    relcon_per_region,   # {'std': {...}, 'spread': {region: DataArray[group]}}
    regions=REGIONS,
    region_labels=None,
    region_colors=None,
    shade_factors=None,
    group_order=RELCON_GROUP_ORDER,
    bar_width=0.6,
    grey=True,
    neutral=RELCON_NEUTRAL_GREY,
    xtick_fontsize=16,
    ytick_fontsize=16,
    rotation=0,
    ylabel_fontsize=20,
    ylabel='relative contribution',
):
    """Panel (c): SPREAD-only per-cable relcon -- one stacked bar per cable.

    SPREAD-only rendition of ``fig9_patm_unc.plot_relcon_bars_grouped``: drops
    the STD bar of each cable's pair (so it's four solid bars, one per cable,
    not four hatched/plain pairs) and drops the hatch entirely (no STD/SPREAD
    distinction to encode). x labels use the bare region codes
    (LS/SPG/NS/Nfl) -- no "_cable" suffix.

    `grey=True` (the default, per the round-3 reviewer request) draws every
    cable's stack in the same light/mid/dark shades of `neutral` that
    ``_relcon_shade_legend_handles`` uses, so the legend is literally the key
    and the panel reads as a straight cross-cable comparison of the p_atm
    fraction; cable identity is carried by the x labels (and by (a)/(b)'s
    colors). Pass `grey=False` for the previous behavior -- color = cable
    identity via ``region_group_colors()``'s shades of that cable's own base
    color -- which is still what the 2x2 ``fig9_patm_unc.py`` figure uses.
    """
    region_labels = region_labels or REGION_LABELS
    region_colors = region_colors or REGION_COLORS
    shade_factors = shade_factors or REGION_SHADE_FACTORS

    x = np.arange(len(regions))
    for xi, region in zip(x, regions):
        if grey:
            colors = {g: _shade_color(neutral, shade_factors[g]) for g in group_order}
        else:
            colors = region_group_colors(region, region_colors, shade_factors)
        bottom = 0.
        da = relcon_per_region['spread'][region]
        for group in group_order:
            val = float(da.sel(group=group))
            ax.bar(xi, val, bar_width, bottom=bottom, color=colors[group],
                   edgecolor='k', linewidth=0.5)
            bottom += val

    ax.set_xticks(x)
    xticklabels = [latex_escape(region_labels[r]) for r in regions]
    if rotation:
        ax.set_xticklabels(xticklabels, fontsize=xtick_fontsize, rotation=rotation,
                           ha='right', rotation_mode='anchor')
    else:
        ax.set_xticklabels(xticklabels, fontsize=xtick_fontsize)
    ax.set_ylim(0, 1)
    ax.set_yticks([0, 0.5, 1])
    ax.tick_params(axis='y', labelsize=ytick_fontsize)
    ax.set_ylabel(ylabel, fontsize=ylabel_fontsize)
    ax.grid(axis='y', alpha=0.3)
    ax.set_axisbelow(True)
    for spine in ('top', 'right'):
        ax.spines[spine].set_visible(False)

    return ax


# =============================================================================
# Full-figure assembly
# =============================================================================

def make_fig9(
    ds,
    sigma_spread_map=None,
    sigma_spread=None,
    relcon_per_region=None,
    ratio_data=None,
    row2_data=None,
    figsize=(18, 5.5),
    cable_lonlat=None,
    landfacecolor='white',
    width_ratios=(1.0, 1.0, 0.62),
):
    """Assemble the 1x3 spread-only figure: (a) map, (b) timeseries, (c) bars.

    Pass in already-loaded pieces (sigma_spread_map/sigma_spread/
    relcon_per_region/ratio_data, from ``fig9_patm_unc.py``'s and this module's
    load_* functions) so a notebook can load once and iterate on layout/styling
    quickly; any left as None is loaded here.

    `ratio_data` (from ``load_global_ratio_series()``) drives panel (b).
    `row2_data` (``fig9_patm_unc.load_row2_data``) is now needed only for the
    cable sensor lon/lats that (a)'s dots use -- panel (b) no longer subsamples
    at the sensors -- so pass `cable_lonlat` directly to skip that load
    entirely.

    (a) and (b) get similar widths; (c) (relcon bars) gets the skinniest column
    (`width_ratios`, default (1, 1, 0.62)).
    """
    sigma_spread_map = sigma_spread_map if sigma_spread_map is not None else load_sigma_patm_spread_map()
    sigma_spread = sigma_spread if sigma_spread is not None else load_sigma_patm_spread()
    relcon_per_region = relcon_per_region if relcon_per_region is not None else load_relcon_per_region()
    ratio_data = ratio_data if ratio_data is not None else load_global_ratio_series(sigma_spread)

    if cable_lonlat is None:
        row2_data = row2_data if row2_data is not None else load_row2_data(ds, sigma_spread)
        cable_lonlat = {r: (row2_data[r]['lons'], row2_data[r]['lats']) for r in REGIONS}

    # SPNA projection center, matching smartosse.plot.spna()'s defaults
    # (xmin=-80, xmax=10 -> central_longitude=-35; ymin=40, ymax=80 ->
    # central_latitude=60). Kept in sync by hand -- if spna()'s defaults
    # change, update here too.
    spna_proj = ccrs.LambertConformal(central_longitude=-35, central_latitude=60)

    fig = plt.figure(figsize=figsize)
    gs = fig.add_gridspec(1, 3, width_ratios=list(width_ratios), wspace=0.35)

    ax_a = fig.add_subplot(gs[0, 0], projection=spna_proj)
    ax_b = fig.add_subplot(gs[0, 1])
    ax_c = fig.add_subplot(gs[0, 2])

    # (a) spread map + cable dots, own horizontal colorbar beneath (dropped
    # lower via a larger `pad`; tick + axis-label fonts bumped up well past
    # plot_sigma_patm_map's built-in defaults, overridden on the returned cb).
    from .fig9_patm_unc import spna  # spna(ax=...) decorates an existing GeoAxes
    _, ax_a = spna(ax=ax_a, landfacecolor=landfacecolor)
    _, cb_a, _ = plot_sigma_patm_map(
        sigma_spread_map, ax=ax_a, cable_lonlat=cable_lonlat,
        add_colorbar=True,
        cbar_kwargs=dict(orientation='horizontal', shrink=0.85, pad=0.11, **SIGMA_MAP_CBAR_KWARGS),
        **SIGMA_MAP_KWARGS,
    )
    cb_a.ax.tick_params(labelsize=22)
    cb_a.ax.set_xlabel('[hPa]', fontsize=24)
    add_panel_label(ax_a, 'a', fontsize=PANEL_LABEL_FONTSIZE)

    # (b) global max |dp_atm|/sigma_patm -- whole-domain max, normalized
    # pointwise (see module docstring). Curves are magnitudes so the axis
    # starts at 0; the grey region is "within 1 sigma" with a dotted line at 1.
    # 3-row x 2-col legend (was 2x3), at a larger fontsize: the 4 cables fill
    # the top two rows in reading order (LS SPG / NS Nfl) and the grey band
    # swatch sits alone on the bottom row. matplotlib fills legend cells
    # COLUMN-major, so getting that on screen means handing it the columns --
    # col 1 = [LS, NS, band], col 2 = [SPG, Nfl] -- i.e. the permutation
    # (0, 2, 4, 1, 3) of the natural [LS, SPG, NS, Nfl, band] order.
    # It sits in the strip above the ratio=1 reference line, which no curve
    # can enter (see the ylim comment in plot_patm_adjustment_ratio), and is
    # right-anchored so it clears the (b) panel letter in the top-left corner.
    plot_patm_adjustment_ratio(ax_b, ratio_data, ytick_fontsize=20, ylabel_fontsize=22,
                               legend=True,
                               legend_handle_order=(0, 2, 4, 1, 3),
                               legend_kwargs=dict(fontsize=RATIO_LEGEND_FONTSIZE,
                                                  loc='upper right',
                                                  bbox_to_anchor=(1.0, 1.0), ncol=2,
                                                  columnspacing=1.0, handlelength=1.4,
                                                  labelspacing=0.35))
    add_panel_label(ax_b, 'b', fontsize=PANEL_LABEL_FONTSIZE, x=0.02, y=0.98)

    # (c) spread-only relcon bars (four stacked bars in the legend's greys,
    # no hatch), + control shade key.
    plot_relcon_bars_spread(ax_c, relcon_per_region, xtick_fontsize=15, ytick_fontsize=20,
                            rotation=0, ylabel_fontsize=22)
    # (c)'s bars stack to 1.0, so there's no blank interior corner for the
    # panel letter -- it sits in the right margin, above the control-shade
    # legend (legend nudged down so the two don't collide).
    add_panel_label(ax_c, 'c', fontsize=PANEL_LABEL_FONTSIZE, x=1.03, y=1.0)
    ax_c.legend(handles=_relcon_shade_legend_handles(), fontsize=19, frameon=False,
                loc='upper left', bbox_to_anchor=(1.02, 0.80), title='control',
                title_fontsize=21)

    return fig, dict(a=ax_a, b=ax_b, c=ax_c)


if __name__ == '__main__':
    # Run as: module load texlive && conda activate .../esmpy_3.10 &&
    #         python -m smartosse.figures.fig9_spread_3panel
    # (texlive in the *same* shell -- use_latex_times() needs `latex` on PATH.)
    import os
    from ..dataset import open_astedataset
    from .figs_utils import use_latex_times, use_embedded_pdf_fonts

    use_latex_times()
    use_embedded_pdf_fonts()

    ds = open_astedataset()
    fig, axes = make_fig9(ds)

    # Written next to the module (not under output/) because
    # smartosse/tex/sections/controls.tex includes it as
    # figures/fig9_spread_3panel_test.png, and tex/figures symlinks here.
    out_base = os.path.join(os.path.dirname(__file__), 'fig9_spread_3panel_test')
    fig.savefig(out_base + '.png', dpi=300, bbox_inches='tight')
    fig.savefig(out_base + '.pdf', bbox_inches='tight')
    print('wrote', out_base + '.png', 'and', out_base + '.pdf')
