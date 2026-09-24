"""
Inverted-barometer control-frequency sweep (``inverted_barometer_ctrl_freqs``).

Ports ``smart_cables/osse/lookat_ib_assim.ipynb`` (cells 15/17/22) into the
package, in two renderings of the *same* numbers:

    (1) ``make_line_figure()``  -- the notebook's original line plot, restyled
        from its red/blue/black onto the fig-9 / appendix-B relcon greys.
        Saved as ``inverted_barometer_ctrl_freqs.{png,pdf}``.

    (2) ``make_stacked_figure()`` -- the same three grouped contributions as
        100%-stacked bars, i.e. relative contributions shown as the partition
        of unity they actually are.
        Saved as ``inverted_barometer_ctrl_freqs_stacked.{png,pdf}``.

THE ARGUMENT: as the control-adjustment interval lengthens, p_atm loses its
grip on the bottom-pressure misfit (0.64 -> 0.19 from a 1-day to a 4-day
interval) and the winds take over (0.34 -> 0.76). At sub-daily-to-daily
adjustment the inverse-barometer response is the cheapest way for the
optimization to explain a p_b misfit; stretch the knots far enough apart and
that pathway is no longer available, so the adjustment has to go through wind
stress instead.

DATA. The metric is asteoptim's control relative contribution,

    stdcost[c,t] = || adxx_c(t) * prior_c ||_2 ,   prior_c = weight_c ** -0.5
    relcon[c,t]  = stdcost[c,t] / sum_c stdcost[c,t]

time-averaged per run. It reads the ADJOINT gradients (``adxx_*``), NOT the
``xx_*`` control fields -- see ``tar_ib_adxx.sh`` in this directory, which
stages exactly the ~450 MB this module needs out of a 58 GB run archive.

TWO THINGS THAT BIT AND ARE NOW HANDLED:

* **240 hr is excluded** (``HOURS`` stops at 96). That run survives only a
  single adjoint record (nt=1) and its relcon is degenerate -- uwind, vwind
  and apressure all come back *exactly* 0.0 while swdown takes 0.76. It is
  not a 10-day data point, it is an empty one. Dropping it leaves lags
  1.0-4.0 days, which is the range the published figure already showed (the
  notebook reached it a different way, by slicing ``[:-2]`` off a 24-120 hr
  sweep).

* **Record count falls with the adjustment interval** -- nt = 8, 6, 5, 4, 4,
  3, 3 across the seven frequencies, since a fixed assimilation window holds
  fewer knots as the knots get further apart. The time-mean therefore averages
  fewer records at the long-lag end. This is the caveat the notebook flagged
  in its own markdown (cell 18) and it is inherited here deliberately, so the
  figure matches the published one; ``load_relcon_sweep`` returns ``nrec`` as
  a coord if it ever needs to be weighted or annotated.
"""
import os

import numpy as np
import xarray as xr
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from matplotlib.lines import Line2D

# Single source of truth for the relcon grouping/shade conventions -- these
# are the same constants that drive fig 9's panel (d) and appendix B's bars.
from .fig9_patm_unc import (
    RELCON_GROUP_ORDER,
    RELCON_GROUP_LABELS,
    REGION_SHADE_FACTORS,
    _shade_color,
)
from .figB_patm_std_4panel import RELCON_BAR_GREY

OUT_DIR = os.path.join(os.path.dirname(__file__), 'output')
DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
CACHE = os.path.join(DATA_DIR, 'ib_ctrl_freqs.nc')

RUN_DIR_ROOT = ('/scratch/08381/goldberg/aste_270x450x180/osses/'
                'runc68v_froman_ib_freq2/201201/')
# The standard ASTE-270 grid used across these OSSEs. Only supplies the XC
# metadata template (dims/dtype) that the weight .bin files are read through.
GRID_DIR = '/work2/08381/goldberg/ls6/aste_270x450x180/GRID_noblank_real4/'

# Control-adjustment intervals, hours. See the 240 hr note in the docstring.
HOURS = (24, 36, 48, 60, 72, 84, 96)

# The fig-9/appendix-B relcon greys: one neutral base shaded three ways, so
# 'other' is lightest and p_atm darkest (darkest = headline result). Same
# _shade_color()/REGION_SHADE_FACTORS machinery as fig 9's per-cable palette,
# just anchored on appendix B's neutral grey instead of a cable color.
RELCON_GREYS = {g: _shade_color(RELCON_BAR_GREY, REGION_SHADE_FACTORS[g])
                for g in RELCON_GROUP_ORDER}

# Line styles for the line variant. Three greys alone are thin encoding at
# print size (the 'other' shade is very light), so shade and dash pattern
# both carry the series identity.
LINE_STYLES = {'patm': '-', 'winds': '--', 'other': ':'}


def _drop_last_if_err(ds, check_var='apressure'):
    """Drop a trailing all-zero adjoint record.

    The last adxx record comes back identically zero when the adjoint run
    stopped short of filling it; carrying it into the time-mean would drag
    every group toward its share of a meaningless all-zero partition. Straight
    port of the notebook's ``drop_last_if_err`` (cell 14).
    """
    if ds[f'adxx_{check_var}'][-1].sum().values == 0.:
        return ds.isel(time=slice(0, -1))
    return ds


def _group_relcon(da):
    """Collapse the 8-control ``ictrl`` axis into winds / patm / other.

    Mirrors ``fig9_patm_unc._group_ctrl``, but keyed on asteoptim's bare
    ``ictrl`` names ('uwind', 'apressure', ...) rather than smartuq's
    ``xx_``-prefixed ``ctrl`` coord.
    """
    group = xr.DataArray(
        np.select(
            [da.ictrl.isin(['uwind', 'vwind']), da.ictrl == 'apressure'],
            ['winds', 'patm'],
            default='other',
        ),
        dims='ictrl',
        coords={'ictrl': da.ictrl},
        name='group',
    )
    return da.groupby(group).sum(dim='ictrl')


def load_relcon_sweep(hours=HOURS, run_dir_root=RUN_DIR_ROOT, grid_dir=GRID_DIR,
                      iternum=0, cache=CACHE, use_cache=True):
    """Time-mean grouped relcon for each control-adjustment interval.

    Returns a DataArray with dims ``(hour, group)`` summing to 1 along
    ``group``, plus a ``lag_days`` coord (hour/24) and an ``nrec`` coord
    holding each run's surviving adjoint-record count.

    Reads ~430 MB of ``adxx_*`` off scratch, so the result is cached to
    `cache` as netCDF; pass ``use_cache=False`` to force a recompute.
    """
    if use_cache and cache is not None and os.path.exists(cache):
        return xr.open_dataarray(cache)

    import xmitgcm
    import asteoptim as xs

    em = xmitgcm.utils.get_extra_metadata(domain='aste', nx=270)

    means, nrec = [], []
    for hour in hours:
        run_dir = f'{run_dir_root}{hour}hr/iter{iternum:04d}/'
        relcon, _, _, _ = xs.ctrl_utils.get_ctrl_relative_contributions(
            run_dir, grid_dir, iternum=iternum, aste_extra_metadata=em,
            transforms=[_drop_last_if_err],
        )
        nrec.append(relcon.sizes['time'])
        means.append(_group_relcon(relcon.mean('time')))

    da = xr.concat(means, dim='hour').assign_coords(
        hour=list(hours),
        lag_days=('hour', np.asarray(hours) / 24.),
        nrec=('hour', nrec),
    )
    da = da.sel(group=list(RELCON_GROUP_ORDER))
    da.name = 'relcon'

    if cache is not None:
        os.makedirs(os.path.dirname(cache), exist_ok=True)
        da.to_netcdf(cache)
    return da


def make_line_figure(relcon, figsize=(5, 3), greys=None, label_fontsize=16,
                     tick_labelsize=14, legend_fontsize=12):
    """The notebook's line plot, on the relcon greys.

    Geometry (figsize, linewidth/markersize, axis limits, font sizes) is kept
    as the notebook had it so this drops into the manuscript in place of the
    old red/blue/black version.
    """
    greys = greys or RELCON_GREYS
    lag = relcon.lag_days.values

    fig, ax = plt.subplots(figsize=figsize)
    lks = dict(linewidth=.9, markersize=4, marker='o')

    # Drawn dark-to-light so the light 'other' markers sit on top rather than
    # being overdrawn by the heavier series.
    for group in ('patm', 'winds', 'other'):
        ax.plot(lag, relcon.sel(group=group).values,
                color=greys[group], linestyle=LINE_STYLES[group],
                markerfacecolor=greys[group],
                # Light fills need an outline to read at print size.
                markeredgecolor='0.25', markeredgewidth=.5,
                label=RELCON_GROUP_LABELS[group], **lks)

    ax.set_xlim([.75, 4.25])
    ax.set_ylim([-.05, 1.1])
    # Tick every sampled lag rather than matplotlib's default integers, which
    # would hide that the sweep runs in half-day steps -- and keeps this axis
    # identical to the stacked variant's, since they plot the same points.
    ax.set_xticks(lag)
    ax.set_xlabel('Lag [days]', fontsize=label_fontsize)
    ax.set_ylabel('Relative Control\nContribution', fontsize=label_fontsize)
    ax.grid(True, alpha=0.3)
    ax.tick_params(labelsize=tick_labelsize)

    # Legend order follows the stack (p_atm first), not the draw order.
    handles = [Line2D([0], [0], color=greys[g], linestyle=LINE_STYLES[g],
                      marker='o', markerfacecolor=greys[g],
                      markeredgecolor='0.25', markeredgewidth=.5, **{
                          k: v for k, v in lks.items() if k != 'marker'})
               for g in reversed(RELCON_GROUP_ORDER)]
    labels = [RELCON_GROUP_LABELS[g] for g in reversed(RELCON_GROUP_ORDER)]
    ax.legend(handles, labels, ncol=3, loc='upper center',
              fontsize=legend_fontsize)

    fig.tight_layout()
    return fig, ax


def make_stacked_figure(relcon, figsize=(5, 3), greys=None, width=0.35,
                        label_fontsize=16, tick_labelsize=14,
                        legend_fontsize=12, annotate_patm=False):
    """The same numbers as 100%-stacked bars.

    Stacking order is ``RELCON_GROUP_ORDER`` (other -> winds -> patm, bottom to
    top), identical to fig 9 panel (d) and appendix B, so a reader who has seen
    those bars reads this one the same way. Putting p_atm on top makes the
    winds/p_atm interface a single moving boundary, which is the result.

    Bars sit at their true lag in days (the intervals are evenly spaced at
    0.5 d), so the x-axis stays quantitative and comparable to the line
    variant rather than becoming categorical.

    `annotate_patm` overlays the p_atm percentage on each top segment. Off by
    default -- Matt asked for the bars clean (2026-08-12); the y-axis already
    carries the magnitude.
    """
    greys = greys or RELCON_GREYS
    lag = relcon.lag_days.values

    fig, ax = plt.subplots(figsize=figsize)

    bottom = np.zeros(relcon.sizes['hour'])
    for group in RELCON_GROUP_ORDER:
        vals = relcon.sel(group=group).values
        ax.bar(lag, vals, bottom=bottom, width=width, color=greys[group],
               edgecolor='black', linewidth=.6,
               label=RELCON_GROUP_LABELS[group], zorder=2)
        bottom = bottom + vals

    if annotate_patm:
        patm = relcon.sel(group='patm').values
        for x, top, v in zip(lag, bottom, patm):
            # Centered in the p_atm segment, which runs from (top - v) to top.
            ax.text(x, top - v / 2., f'{100 * v:.0f}', ha='center', va='center',
                    fontsize=8, color='white', zorder=3)

    ax.set_xlim([.75, 4.25])
    ax.set_ylim([0, 1])
    ax.set_xticks(lag)
    # Sparse y-axis (Matt, 2026-08-12): endpoints plus midpoint, tenths only.
    ax.set_yticks([0., .5, 1.])
    ax.set_yticklabels(['0.0', '0.5', '1.0'])
    ax.set_xlabel('Lag [days]', fontsize=label_fontsize)
    ax.set_ylabel('Relative Control\nContribution', fontsize=label_fontsize)
    ax.tick_params(labelsize=tick_labelsize)
    ax.grid(True, axis='y', alpha=0.3, zorder=0)
    ax.set_axisbelow(True)

    handles = [Patch(facecolor=greys[g], edgecolor='black',
                     label=RELCON_GROUP_LABELS[g])
               for g in reversed(RELCON_GROUP_ORDER)]
    labels = [RELCON_GROUP_LABELS[g] for g in reversed(RELCON_GROUP_ORDER)]
    # Legend above the axes -- the bars fill the frame to y=1, so there is no
    # in-axes whitespace to drop it into (unlike the line variant).
    ax.legend(handles, labels, ncol=3, loc='lower center',
              bbox_to_anchor=(0.5, 1.01), frameon=False,
              fontsize=legend_fontsize)

    fig.tight_layout()
    return fig, ax


def _save(fig, stem, out_dir=OUT_DIR):
    os.makedirs(out_dir, exist_ok=True)
    fig.savefig(os.path.join(out_dir, stem + '.png'), dpi=300,
                bbox_inches='tight')
    fig.savefig(os.path.join(out_dir, stem + '.pdf'), bbox_inches='tight')


if __name__ == '__main__':
    from .figs_utils import use_latex_times, use_embedded_pdf_fonts

    use_latex_times()
    use_embedded_pdf_fonts()

    relcon = load_relcon_sweep()

    print('lag[d]  ' + '  '.join(f'{g:>7s}' for g in RELCON_GROUP_ORDER) + '   nrec')
    for h in relcon.hour.values:
        r = relcon.sel(hour=h)
        print(f'{float(r.lag_days):5.1f}   '
              + '  '.join(f'{float(r.sel(group=g)):7.4f}' for g in RELCON_GROUP_ORDER)
              + f'   {int(r.nrec):4d}')

    fig, _ = make_line_figure(relcon)
    _save(fig, 'inverted_barometer_ctrl_freqs')

    fig, _ = make_stacked_figure(relcon)
    _save(fig, 'inverted_barometer_ctrl_freqs_stacked')

    print(f'\nwrote 4 files to {OUT_DIR}')
