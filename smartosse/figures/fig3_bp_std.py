"""Fig. 3 -- synthetic OBP uncertainty map (``fig:bp_std`` in the manuscript).

Reproduces ``smart_cables/osse/fig_sigma_pb.ipynb`` -- the temporal standard
deviation of NR bottom pressure (:math:`\\sigma_{\\phi_{bot}}`, converted to an
equivalent water-height in cm) plotted on the SPNA ``spna()`` map, with black
open circles marking the SPNA cable's sensor locations.

Caption (``smartosse-manuscript/sections/uncertainty.tex``): "Synthetic data
uncertainty $\\sigma_{\\phibot}$ used to weight misfits between synthetic NR
and FM-derived $p_b$ in equivalent cm of water height. Black circles indicate
sensor locations along the SPNA cable system."

This remake's only change from the notebook is thicker, darker gridlines
(meridians/parallels) -- see ``GL_LINEWIDTH``/``GL_COLOR`` below -- since the
default thin light-grey gridlines (``smartosse.plot.region_cartopy``'s
``linewidth=0.8``, color ``'#b0b0b0'``) are hard to see against this figure's
busy rainbow-style ``grace_cmap`` colorbar. Panel content/data/colorbar
range are otherwise unchanged from the notebook.

As with the other figure modules, everything here is a small function taking
already-loaded data and returning ``ax``, so it can be tweaked/re-laid-out
interactively from a notebook. ``make_fig3()`` assembles the full figure as a
starting template.
"""
import os
import re
from pathlib import Path

import numpy as np
import xarray as xr
import matplotlib.pyplot as plt
import cartopy.crs as ccrs

from .. import read_aste_bin
from ..dataset import open_astedataset
from ..cmaps import Colormaps
from ..plot import spna
from .figs_utils import use_latex_times, use_embedded_pdf_fonts

# =============================================================================
# Data locations / constants
# =============================================================================

# Temporal std of spatially bin-averaged daily NR OBP anomaly (sigma_phibot),
# already converted to equivalent cm of water height -- see uncertainty.tex.
BP_STD_DIR = '/work/08381/goldberg/ls6/aste_270x450x180/run_template/input_ecco/smart_phibot/'
BP_STD_FILE = 'bp_var_day_coarse4320_detide16constituent_std_cm.bin'

# Any run directory for the full SPNA cable (SPNA_cable) OSSE -- only used to
# recover the cable's sensor tile/j/i indices (`BPReader.sensor_args`), not
# for any run output.
SENSOR_RUN_DIR = ('/scratch/08381/goldberg/aste_270x450x180/osses/'
                   'runc68v_froman_natl_1month_alldailyxx_noapress/201201/fullnatl/')

# Colorbar range/levels -- matches the original notebook/current manuscript
# render exactly (not re-tuned here).
BP_STD_VMIN = 2
BP_STD_VMAX = 6
BP_STD_NLEV = 21

CABLE_SCATTER_KWARGS = dict(s=10, edgecolor='k', facecolor='none')

# Gridline (meridian/parallel) styling -- the one deliberate change from the
# original notebook, per Matt's request to make them more visible against
# the rainbow `grace_cmap` fill. Default `spna()`/`region_cartopy` styling
# is linewidth=0.8 at cartopy/matplotlib's own default grey (`grid.color`
# rcParam, `'#b0b0b0'`) -- explicitly set to the named color 'gray' here
# (rather than leaving `gl_color` unset) so it doesn't silently drift if
# that rcParam default ever changes, just thickened to 1.0.
GL_LINEWIDTH = 1
GL_COLOR = 'gray'

CBAR_RECT = (0.178, 0., 0.67, 0.04)  # figure-fraction (x0, y0, width, height)
CBAR_LABEL = '[cm]'
CBAR_LABEL_FONTSIZE = 22
CBAR_TICK_LABELSIZE = 20


# =============================================================================
# Loaders
# =============================================================================

def load_bp_std(bp_std_dir=BP_STD_DIR, bp_std_file=BP_STD_FILE):
    """Temporal std of daily NR OBP anomaly, equivalent cm of water height,
    on the native ASTE tile/j/i grid (not yet masked to wet cells)."""
    return read_aste_bin(os.path.join(bp_std_dir, bp_std_file))


def load_cable_sensor_lonlat(ds, run_dir=SENSOR_RUN_DIR, iternum=0, bad_vals=(0., -9999.)):
    """SPNA cable sensor lon/lat, recovered directly from the OSSE's
    `data.ecco` ``gencost_datafile(1)`` binary (the same sensor mask/logic
    as ``BPReader.get_sensors``'s data.ecco fallback path, reproduced here
    directly rather than via a full `BPReader(...)` construction). `BPReader`
    also tries to load each iteration's ``bpdatanom_*``/``m_bpday`` output
    fields, which are frequently purged from ``/scratch`` on this machine
    (same purge issue noted in ``fig1_global_cables.py``) well before the
    static sensor-mask input file (which lives under ``/work``, not purged)
    would be. The sensor mask needs only that one static file, so this
    sidesteps the purge issue entirely. Cross-checked against
    ``fig1_global_cables.load_partial_cables()``: the 4 partial-cable
    coordinate files (labsea/subgyre/northsea/newfoundland) sum to exactly
    157 sensors, matching the count this mask finds for the full SPNA cable.
    """
    iter_dir = Path(run_dir) / f'iter{iternum:04d}'
    data_ecco = iter_dir / 'data.ecco'
    match = re.search(r"gencost_datafile\s*\(\s*1\s*\)\s*=\s*'([^']+)'", data_ecco.read_text())
    if match is None:
        raise ValueError(f"Could not find gencost_datafile(1) in {data_ecco}")
    binpath = iter_dir / match.group(1)

    da = read_aste_bin(str(binpath))[0]
    mask = ~np.isin(da.values, bad_vals)
    tile, j, i = np.where(mask)
    sensor_args = dict(
        tile=xr.DataArray(tile, dims='sensor'),
        j=xr.DataArray(j, dims='sensor'),
        i=xr.DataArray(i, dims='sensor'),
    )
    lons, lats = (ds[coord].isel(sensor_args).values for coord in ['XC', 'YC'])
    return lons, lats


# =============================================================================
# Plot pieces
# =============================================================================

def plot_bp_std_map(ax, ds, da, cable_lons, cable_lats,
                     vmin=BP_STD_VMIN, vmax=BP_STD_VMAX, nlev=BP_STD_NLEV,
                     cable_scatter_kwargs=None):
    """Fill `ax` (an `spna()` axes) with the sigma_phibot contourf field and
    scatter the cable sensor locations on top.

    Returns
    -------
    p : the contourf mappable, for building a colorbar from.
    """
    cmap = Colormaps(nlev).grace_cmap()
    levels = np.linspace(vmin, vmax, nlev)

    da_masked = da.where(ds.hFacC[0])
    _, ax, _, p = ds.plotpc(da_masked, ax=ax, vmin=vmin, vmax=vmax, levels=levels,
                             cmap=cmap, plot_type='contourf', show_cbar=False)

    scatter_kwargs = dict(CABLE_SCATTER_KWARGS)
    scatter_kwargs.update(cable_scatter_kwargs or {})
    ax.scatter(cable_lons, cable_lats, transform=ccrs.PlateCarree(), **scatter_kwargs)

    return p


def add_bp_std_colorbar(fig, p, rect=CBAR_RECT, label=CBAR_LABEL,
                         label_fontsize=CBAR_LABEL_FONTSIZE,
                         tick_labelsize=CBAR_TICK_LABELSIZE):
    """Manual horizontal colorbar in its own figure-fraction axes (rather
    than `fig.colorbar(ax=...)`, which would resize/reposition the map
    axes) -- matches the original notebook's placement exactly."""
    cb = fig.colorbar(p, cax=fig.add_axes(list(rect)), orientation='horizontal', extend='both')
    cb.ax.set_xlabel(label, fontsize=label_fontsize)
    cb.ax.tick_params(axis='both', which='major', labelsize=tick_labelsize)
    return cb


# =============================================================================
# Assembly
# =============================================================================

def make_fig3(ds=None, gl_linewidth=GL_LINEWIDTH, gl_color=GL_COLOR, use_latex=True):
    """Assemble the full Fig. 3 (sigma_phibot map + cable sensors + colorbar).

    `ds` may be passed in (e.g. already open in a notebook) to avoid
    re-opening the ASTE grid; defaults to a fresh `open_astedataset()` call.

    Returns
    -------
    fig, ax
    """
    if use_latex:
        # module load texlive first, in the same shell -- see figs_utils.
        use_latex_times()
        use_embedded_pdf_fonts()

    if ds is None:
        ds = open_astedataset()

    da = load_bp_std()
    cable_lons, cable_lats = load_cable_sensor_lonlat(ds)

    fig, ax = spna(gl_linewidth=gl_linewidth, gl_color=gl_color)
    p = plot_bp_std_map(ax, ds, da, cable_lons, cable_lats)
    add_bp_std_colorbar(fig, p)

    return fig, ax


if __name__ == '__main__':
    fig, ax = make_fig3()
    out_dir = os.path.join(os.path.dirname(__file__), 'output')
    os.makedirs(out_dir, exist_ok=True)
    fig.savefig(os.path.join(out_dir, 'fig3_bp_std.png'), dpi=300,
                bbox_inches='tight', transparent=True)
    fig.savefig(os.path.join(out_dir, 'fig3_bp_std.pdf'),
                bbox_inches='tight', transparent=True)
