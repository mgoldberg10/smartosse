"""Fig. 1 -- global SMART cable network + SPNA partial-cable inset
(``fig:global_smart_cables`` in the manuscript).

Cartopy/matplotlib port of ``smart_cables/osse/
smart_cable_and_partial_cables_eomaps.ipynb``. Layout:

    (left)  Global Mollweide map -- gray dots: representative candidate
            cable network; red dots: funded/in-development systems (Azores
            loop, Vanuatu-New Caledonia). The full ASTE domain is filled in
            blue (matching Fig. 2's ``Blues`` bathymetry) and outlined;
            ocean outside ASTE is white, land is silver. A black
            quadrilateral (the SPNA lon/lat box, drawn under PlateCarree so
            it bends correctly on Mollweide) marks the region zoomed on the
            right, joined by a dashed line.
    (right) SPNA inset in this codebase's standard ``spna()`` view -- the 4
            partial cables (Labrador Sea / Subpolar Gyre / North Sea /
            Newfoundland) colored per ``fig9_patm_unc.REGION_COLORS`` with a
            single-column legend to the right, over the representative
            network in translucent black.

Every function takes already-loaded data and returns ``ax``, so panels can
be tweaked from a notebook; ``make_fig1()`` assembles the 2-panel layout.
"""
import os

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import cartopy.crs as ccrs
import cartopy.feature as cf
import cartopy.util as cutil

from smartosse.dataset import open_astedataset
from smartosse.plot import spna, llc_map
from smartosse.figures.fig9_patm_unc import REGION_COLORS
from smartosse.figures.figs_utils import latex_escape, use_latex_times, use_embedded_pdf_fonts

# =============================================================================
# Data locations / constants
# =============================================================================

# Global candidate + funded-system coordinates; both files carry plain
# Longitude/Latitude columns. These SHIP WITH THE PACKAGE (see
# cable_data/README.md) -- they are figure inputs, not model output, and they
# total ~92 KB, so Tier 0 should not need a site path for them. Copied from
# /nobackup/mgoldbe1/cable_data_new/ on pfe, which is the same set previously
# read from /work2/08381/goldberg/ls6/cable_data_new/ at TACC.
# SMARTOSSE_CABLE_DATA_DIR overrides, per smartosse/paths.py's convention that
# an env var always beats a default.
CABLE_DATA_DIR = os.environ.get(
    'SMARTOSSE_CABLE_DATA_DIR',
    os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cable_data'))
GLOBAL_CABLE_FILE_REPRESENTATIVE = 'smart_cables_may2024.csv'
GLOBAL_CABLE_FILE_ALL = 'global_total_coord.csv'

# SPNA partial-cable coordinates, one (data_variable, Longitude, Latitude)
# csv per region. Mirrored into this package from the original OSSE run
# directory on /scratch, which is subject to TACC's purge policy.
# These live under cable_data/, NOT under data/: data/ is gitignored (it holds
# the large regenerable .nc caches), so coordinates placed there would never
# ship and Fig. 1 would silently drop its inset for anyone but the author.
PARTIAL_CABLE_DIR = os.environ.get(
    'SMARTOSSE_PARTIAL_CABLE_DIR',
    os.path.join(os.path.dirname(os.path.abspath(__file__)),
                 'cable_data', 'partial_cable_coords'))
PARTIAL_CABLE_REGIONS = ('labsea', 'subgyre', 'northsea', 'newfoundland')

# Inset legend labels: experiment code + region name (per the R1 revision plan).
REGION_LABELS = {
    'subgyre': 'SPG_cable (Subpolar Gyre)',
    'newfoundland': 'Nfl_cable (Newfoundland)',
    'labsea': 'LS_cable (Labrador Sea)',
    'northsea': 'NS_cable (North Sea)',
}

# "Funded" system boxes carving the two red clusters out of the global network.
AZORES_LON, AZORES_LAT = (-32, -8), (30, 42)
VNC_LON, VNC_LAT = (160, 190), (-25, -12)
# global_total_coord.csv concatenates many cable routes end to end, so the
# Azores lon/lat box alone also catches transatlantic routes passing through
# it; this contiguous row block is just the actual Azores loop.
AZORES_ROW_SLICE = slice(2000, 3000)

# SPNA inset extent -- matches spna()'s own default box (smartosse/plot.py).
SPNA_XMIN, SPNA_XMAX, SPNA_YMIN, SPNA_YMAX = -80, 10, 40, 80

MOLLWEIDE_CENTRAL_LON = 40

# Inset region-legend fontsize.
LEGEND_FONTSIZE = 32

# `plot_spna_inset`'s `legend_multiline=True` labelspacing -- tuned by sweep
# so the legend box's rendered height matches the inset axes' height at
# LEGEND_FONTSIZE=32 (leg_h=465.3px vs inset_h=465.0px). Since the legend is
# anchored at the inset's vertical center, matching the height also matches
# the top/bottom edges.
INSET_MULTILINE_LEGEND_LABELSPACING = 0.6

REPRESENTATIVE_COLOR = 'dimgray'
FUNDED_COLOR = 'r'

# Land: `smartosse.plot.region_cartopy`'s default `landfacecolor`, used on
# both panels. Ocean: blue inside the ASTE domain (`Blues` at 0.45), white
# outside it, so the domain reads as the figure's subject.
LAND_COLOR = 'silver'
ASTE_OCEAN_COLOR = '#7fb9da'
NONASTE_OCEAN_COLOR = '#ffffff'
# The inset lies entirely inside ASTE, so its ocean uses the same blue.
OCEAN_COLOR = ASTE_OCEAN_COLOR

ASTE_OUTLINE_COLOR = 'k'
ASTE_OUTLINE_LW = 0.6

# Natural Earth scale for the land/ocean fills, per panel. Both features on a
# panel MUST come from the same scale: the two datasets are only exactly
# complementary within a scale, so a coarse land polygon over a finer ocean
# polygon (or vice versa) leaves uncovered slivers along convoluted coasts,
# which show as white speckles. `cf.LAND`/`cf.OCEAN` can't be trusted to
# match -- cartopy resolves their scale at draw time from the axes extent, so
# the inset's `cf.OCEAN` came out 50m against `region_cartopy`'s hardcoded
# 110m land. Hence explicit scales here and `show_land=False` on the inset's
# `spna()` call, drawing both features ourselves. 50m for the regional inset
# (finer coastlines at that zoom), 110m for the global panel.
GLOBAL_FEATURE_SCALE = '110m'
INSET_FEATURE_SCALE = '50m'

# Thin black outline on the inset's partial-cable markers (map + legend key),
# to separate them from the blue ocean. Kept hairline-thin: at the sizes this
# figure is reproduced/zoomed out to, a heavier edge eats the marker's fill
# and the whole cable reads as a black line (Matt, 2026-08-12) -- hence 0.2
# here and the larger `partial_size`.
PARTIAL_EDGE_COLOR = 'k'
PARTIAL_EDGE_LW = 0.2


# =============================================================================
# Loaders
# =============================================================================

def load_global_cables(cable_dir=CABLE_DATA_DIR):
    """Global candidate cable network, split into "representative" (gray)
    and "funded" (red) subsets.

    Returns
    -------
    df_repr, df_funded : pd.DataFrame
        Each with columns ``Longitude``, ``Latitude``.
    """
    df1 = pd.read_csv(os.path.join(cable_dir, GLOBAL_CABLE_FILE_REPRESENTATIVE))
    df2 = pd.read_csv(os.path.join(cable_dir, GLOBAL_CABLE_FILE_ALL))

    def in_box(df, lon_rng, lat_rng):
        return df.Longitude.between(*lon_rng) & df.Latitude.between(*lat_rng)

    az_block = df2.iloc[AZORES_ROW_SLICE]
    mask_az_block = in_box(az_block, AZORES_LON, AZORES_LAT)
    df_az = az_block[mask_az_block]

    mask_vn1 = in_box(df1, VNC_LON, VNC_LAT)
    mask_vn2 = in_box(df2, VNC_LON, VNC_LAT)

    df_funded = pd.concat([df_az, df1[mask_vn1], df2[mask_vn2]], ignore_index=True)

    mask_az2_full = pd.Series(False, index=df2.index)
    mask_az2_full.loc[az_block.index] = mask_az_block.values
    df1_repr = df1[~mask_vn1]
    df2_repr = df2[~(mask_az2_full | mask_vn2)]
    df_repr = pd.concat([df1_repr, df2_repr], ignore_index=True)

    return df_repr, df_funded


def load_aste_domain_mask():
    """Surface (k=0) wet-cell mask for the full ASTE domain, on the native
    LLC tile/j/i grid -- 1 where ASTE has ocean, 0 elsewhere. Feeds
    `plot_aste_domain`'s regrid step.
    """
    ds = open_astedataset()
    return ds.hFacC.isel(k=0)


def load_partial_cables(partial_cable_dir=PARTIAL_CABLE_DIR, regions=PARTIAL_CABLE_REGIONS):
    """One (Longitude, Latitude) DataFrame per SPNA partial-cable region."""
    out = {}
    for region in regions:
        path = os.path.join(partial_cable_dir, f'{region}_cable_coords.csv')
        df = pd.read_csv(path, header=None, names=['data_variable', 'Longitude', 'Latitude'])
        out[region] = df[['Longitude', 'Latitude']]
    return out


# =============================================================================
# Plot pieces
# =============================================================================

def _box_path_lonlat(xmin, xmax, ymin, ymax, npts=50):
    """Densely sampled (lon, lat) perimeter of a lon/lat rectangle, so the
    box renders as a smooth curve once projected (same construction as
    `region_cartopy`'s `aoi` Path in smartosse/plot.py).
    """
    lons = np.concatenate([
        np.linspace(xmin, xmax, npts),
        np.full(npts, xmax),
        np.linspace(xmax, xmin, npts),
        np.full(npts, xmin),
    ])
    lats = np.concatenate([
        np.full(npts, ymin),
        np.linspace(ymin, ymax, npts),
        np.full(npts, ymax),
        np.linspace(ymax, ymin, npts),
    ])
    return lons, lats


def plot_aste_domain(ax, mask, dx=0.5, dy=0.5, color=ASTE_OCEAN_COLOR,
                      outline=True, outline_color=ASTE_OUTLINE_COLOR,
                      outline_lw=ASTE_OUTLINE_LW, zorder=0.5):
    """Fill the full ASTE domain on a global (cyclic-longitude) panel with a
    single flat color, plus an optional thin boundary outline.

    Regridding reuses `llc_map.regrid`, but the draw deliberately bypasses
    ``ds.plotpc``/``llc_map.__call__``: that path always builds a multi-level
    colormap and raises ``ValueError: Filled contours require at least 2
    levels`` on a binary mask, which isn't a field to color-map anyway.

    Parameters
    ----------
    ax : GeoAxes
        Must already have a global (e.g. Mollweide) projection.
    mask : xr.DataArray
        Output of :func:`load_aste_domain_mask` (surface hFacC, tile/j/i).
    dx, dy : float
        Regrid resolution in degrees -- coarser than `llc_map`'s 0.25 default
        since this is a binary domain edge, not a field needing gradients.
    """
    lm = llc_map(mask.to_dataset(name='mask'), dx=dx, dy=dy)
    field = lm.regrid(mask)
    # `field_nan` (1/NaN) so the fill leaves non-ASTE cells untouched;
    # `field_binary` (1/0) so the outline contour has finite values on both
    # sides of the domain edge (a contour level can't be traced against NaN).
    field_nan = np.where(field == 1, 1.0, np.nan)
    field_binary = np.where(field == 1, 1.0, 0.0)

    lon2d, lat2d = lm.new_grid_lon, lm.new_grid_lat
    cfield_nan, clon2d, clat2d = cutil.add_cyclic(field_nan, lon2d, lat2d)
    cfield_binary = cutil.add_cyclic(field_binary, lon2d, lat2d)[0]

    ax.contourf(clon2d, clat2d, cfield_nan, levels=[0.5, 1.5], colors=[color],
                transform=ccrs.PlateCarree(), zorder=zorder)

    if outline:
        ax.contour(clon2d, clat2d, cfield_binary, levels=[0.5], colors=outline_color,
                   linewidths=outline_lw, transform=ccrs.PlateCarree(), zorder=zorder + 0.1)

    return ax


def plot_global_panel(ax, df_repr, df_funded, aste_mask=None,
                       box=(SPNA_XMIN, SPNA_XMAX, SPNA_YMIN, SPNA_YMAX),
                       repr_size=3, funded_size=4, box_lw=2.5, aste_kwargs=None):
    """Global Mollweide panel: ASTE-domain patch, representative + funded
    cable dots, and the SPNA-inset indicator box.

    Parameters
    ----------
    ax : GeoAxes
        Must already have a Mollweide projection.
    df_repr, df_funded : pd.DataFrame
        Output of :func:`load_global_cables`.
    aste_mask : xr.DataArray, optional
        Output of :func:`load_aste_domain_mask`. If given, the full ASTE
        domain is filled/outlined (see `plot_aste_domain`) before anything
        else, so cable dots and the box sit on top of it.
    box : (xmin, xmax, ymin, ymax)
        Lon/lat extent of the SPNA inset, drawn as an outline on this panel.
    """
    ax.add_feature(cf.NaturalEarthFeature('physical', 'ocean', GLOBAL_FEATURE_SCALE),
                   facecolor=NONASTE_OCEAN_COLOR, edgecolor='face', zorder=0)
    ax.set_global()

    if aste_mask is not None:
        plot_aste_domain(ax, aste_mask, **(aste_kwargs or {}))

    # Land at zorder 1, above both ocean fills (0) and the ASTE patch/outline
    # (~0.5/0.6), so it isn't tinted by any regrid bleed at the coast.
    ax.add_feature(cf.NaturalEarthFeature('physical', 'land', GLOBAL_FEATURE_SCALE),
                   facecolor=LAND_COLOR, edgecolor='none', zorder=1)

    ax.scatter(df_repr['Longitude'], df_repr['Latitude'], color=REPRESENTATIVE_COLOR,
               s=repr_size, transform=ccrs.PlateCarree(), zorder=2)
    ax.scatter(df_funded['Longitude'], df_funded['Latitude'], color=FUNDED_COLOR,
               s=funded_size, transform=ccrs.PlateCarree(), zorder=3)

    lons, lats = _box_path_lonlat(*box)
    ax.plot(lons, lats, color='k', lw=box_lw, transform=ccrs.PlateCarree(), zorder=10)

    return ax


# region_cartopy's default gl_label_args is replaced wholesale (not merged) on
# override, so all 4 sides are spelled out: every tick label dropped, with the
# dotted gridlines themselves switched off via show_gl=False below.
INSET_GL_LABEL_ARGS_NONE = {
    'top':    {'hide': True, 'rotate': False, 'pad': 0.0},
    'bottom': {'hide': True, 'rotate': True,  'pad': 0.1, 'threshold': 0.0001},
    'left':   {'hide': True, 'rotate': False, 'pad': 0.0},
    'right':  {'hide': True, 'rotate': False, 'pad': 0.0, 'threshold': 0.2},
    'fontsize': 20,
}


def _region_legend_label(region, multiline=False):
    """`REGION_LABELS[region]`, optionally split onto two lines (code, then
    the parenthetical region name) for `plot_spna_inset`'s multiline variant.
    """
    label = REGION_LABELS[region]
    if multiline:
        label = label.replace(' (', '\n(')
    return latex_escape(label)


def plot_spna_inset(ax, partial_cables, df_repr, partial_size=55, repr_size=3,
                     repr_alpha=0.25, region_legend=True, region_legend_kwargs=None,
                     legend_multiline=False, spna_kwargs=None):
    """SPNA inset panel: the 4 colored partial cables (+ a region legend)
    over the full representative network, in this codebase's standard
    `spna()` view.

    Parameters
    ----------
    ax : GeoAxes
        Must already have a LambertConformal projection centered to match
        `spna()`'s own default (see `make_fig1`).
    partial_cables : dict
        Output of :func:`load_partial_cables` (region -> DataFrame).
    df_repr : pd.DataFrame
        Output of :func:`load_global_cables` -- the full representative
        network, overlaid here restricted (by `ax`'s extent) to the SPNA box.
    legend_multiline : bool
        If True, split each legend entry's code and region name onto two lines.
    """
    # `show_land=False`: region_cartopy's own land is hardcoded to 110m, which
    # can't match the ocean here (see GLOBAL/INSET_FEATURE_SCALE) -- so draw
    # both fills ourselves, at one scale, in region_cartopy's own zorders
    # (ocean below land's 1, both below the gridlines' 2).
    default_spna_kwargs = dict(show_gl=False, show_land=False,
                               gl_label_args=INSET_GL_LABEL_ARGS_NONE)
    default_spna_kwargs.update(spna_kwargs or {})
    spna(ax=ax, landfacecolor=LAND_COLOR, **default_spna_kwargs)
    ax.add_feature(cf.NaturalEarthFeature('physical', 'ocean', INSET_FEATURE_SCALE),
                   facecolor=OCEAN_COLOR, edgecolor='face', zorder=0)
    ax.add_feature(cf.NaturalEarthFeature('physical', 'land', INSET_FEATURE_SCALE),
                   facecolor=LAND_COLOR, edgecolor='none', zorder=1)

    ax.scatter(df_repr['Longitude'], df_repr['Latitude'], color='k', s=repr_size,
               alpha=repr_alpha, transform=ccrs.PlateCarree(), zorder=3)

    for region, df in partial_cables.items():
        color = REGION_COLORS[region]
        ax.scatter(df['Longitude'], df['Latitude'], color=color, s=partial_size,
                   edgecolors=PARTIAL_EDGE_COLOR, linewidths=PARTIAL_EDGE_LW,
                   transform=ccrs.PlateCarree(), zorder=4)

    if region_legend:
        region_legend_kwargs = region_legend_kwargs or {}
        legend_elements = [
            Line2D([0], [0], marker='o', color='w',
                   label=_region_legend_label(region, multiline=legend_multiline),
                   markerfacecolor=REGION_COLORS[region], markersize=14,
                   markeredgecolor=PARTIAL_EDGE_COLOR, markeredgewidth=PARTIAL_EDGE_LW)
            for region in partial_cables
        ]
        # Anchored at the inset's own vertical center just past its right
        # edge, so the height tuning above (multiline case) also lines the
        # legend's top/bottom up with the inset's.
        default_legend_kwargs = dict(
            loc='center left', bbox_to_anchor=(1.05, 0.5), ncol=1, fontsize=LEGEND_FONTSIZE,
            frameon=True, framealpha=0.9, handletextpad=0.5, borderpad=0.5,
        )
        if legend_multiline:
            default_legend_kwargs['labelspacing'] = INSET_MULTILINE_LEGEND_LABELSPACING
        default_legend_kwargs.update(region_legend_kwargs)
        ax.legend(handles=legend_elements, **default_legend_kwargs)

    return ax


def add_inset_indicator_line(fig, ax_global, ax_inset, box=(SPNA_XMIN, SPNA_XMAX, SPNA_YMIN, SPNA_YMAX),
                              corner='upper_right', inset_anchor=(0.0, 0.5), **line_kwargs):
    """Dashed line from one corner of the global-panel indicator box to the
    inset panel's edge, matching eomaps' `add_indicator_line`.

    Must be called after both panels are otherwise fully drawn (needs a
    canvas draw to resolve cartopy's data->display transform).
    """
    xmin, xmax, ymin, ymax = box
    corners = {
        'upper_right': (xmax, ymax), 'upper_left': (xmin, ymax),
        'lower_right': (xmax, ymin), 'lower_left': (xmin, ymin),
    }
    lon, lat = corners[corner]

    fig.canvas.draw()
    display_xy = ax_global.projection.transform_point(lon, lat, ccrs.PlateCarree())
    display_xy = ax_global.transData.transform(display_xy)
    fig_xy0 = fig.transFigure.inverted().transform(display_xy)
    fig_xy1 = fig.transFigure.inverted().transform(ax_inset.transAxes.transform(inset_anchor))

    default_kwargs = dict(color='k', lw=2, linestyle='--', zorder=20)
    default_kwargs.update(line_kwargs)
    line = Line2D([fig_xy0[0], fig_xy1[0]], [fig_xy0[1], fig_xy1[1]],
                  transform=fig.transFigure, **default_kwargs)
    fig.add_artist(line)
    return line


# =============================================================================
# Assembly
# =============================================================================

def make_fig1(figsize=(18, 7), global_rect=(0.0, 0.03, 0.52, 0.94),
              inset_rect=(0.58, 0.1, 0.36, 0.8), use_latex=True, show_aste_domain=True,
              legend_multiline=False):
    """Assemble the full 2-panel Fig. 1 (global map + SPNA inset).

    `global_rect`/`inset_rect` are explicit (x0, y0, width, height) figure-
    fraction axes positions (rather than a gridspec) so the inset's size and
    placement can be tuned directly.

    `show_aste_domain` (default True) loads the ASTE grid and fills/outlines
    the full domain on the global panel -- set False to skip that load (e.g.
    if the grid directory isn't reachable) and leave the ocean flat.

    Returns
    -------
    fig, (ax_global, ax_inset)
    """
    if use_latex:
        # module load texlive first, in the same shell -- see figs_utils.
        use_latex_times()
        use_embedded_pdf_fonts()

    df_repr, df_funded = load_global_cables()
    partial_cables = load_partial_cables()
    aste_mask = load_aste_domain_mask() if show_aste_domain else None

    spna_central_lon = (SPNA_XMIN + SPNA_XMAX) / 2  # -35, matches spna()'s default

    fig = plt.figure(figsize=figsize)
    ax_global = fig.add_axes(global_rect, projection=ccrs.Mollweide(central_longitude=MOLLWEIDE_CENTRAL_LON))
    ax_inset = fig.add_axes(inset_rect, projection=ccrs.LambertConformal(central_longitude=spna_central_lon))

    plot_global_panel(ax_global, df_repr, df_funded, aste_mask=aste_mask)
    plot_spna_inset(ax_inset, partial_cables, df_repr, legend_multiline=legend_multiline)

    add_inset_indicator_line(fig, ax_global, ax_inset)

    return fig, (ax_global, ax_inset)


if __name__ == '__main__':
    fig, axes = make_fig1()
    out_dir = os.path.join(os.path.dirname(__file__), 'output')
    os.makedirs(out_dir, exist_ok=True)
    fig.savefig(os.path.join(out_dir, 'fig1_global_cables.png'), dpi=300,
                bbox_inches='tight', transparent=True)
    fig.savefig(os.path.join(out_dir, 'fig1_global_cables.pdf'),
                bbox_inches='tight', transparent=True)
