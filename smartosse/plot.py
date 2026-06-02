# llc_map is largely lifted from Tim Smith's (timothyas) pych repository
# which borrowed from xgcm/ecco_v4_py plotting, which relies on pyrsample
# to map llc grid onto regular lat-lon before plotting with cartopy
#
# other particular features of region_cartopy are inspired by various
# stackexchang posts, e.g. the set_boundary feature
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import cm, colors
import cartopy.crs as ccrs
import cartopy.feature as cf
from cartopy.mpl.geoaxes import GeoAxesSubplot
import cartopy.util as cutil
import pyresample as pr
from cartopy.mpl.gridliner import LONGITUDE_FORMATTER, LATITUDE_FORMATTER
import matplotlib.ticker as mticker
import matplotlib.path as mpath
import matplotlib.colors as mcolors
import xarray as xr
import copy
from .cmaps import *
import inspect


def plotpc(obj, da=None, am_init_kwargs=None, **am_kwargs):
    """
    Plot a DataArray from irregular grid with lons, lats (XC and YC)
    on a PlateCarree projection.

    Parameters
    ----------
    obj : xr.Dataset or xr.DataArray
        The source dataset or data array.
    da : xr.DataArray, optional
        The variable to plot. Required if `obj` is a Dataset.
        Ignored if `obj` is already a DataArray.
    am_init_kwargs : dict, optional
        Arguments for initializing the llc_map.
    **am_kwargs :
        Arguments passed to the llc_map plotting call.

    Returns
    -------
    fig : matplotlib.figure.Figure or None
        The matplotlib Figure, or None if an axis was provided by the user.
    ax : matplotlib.axes.Axes
        The target axis for the plot.
    cb : matplotlib.colorbar.Colorbar
        The colorbar associated with the plot.
    p : matplotlib.artist.Artist
        The plot artist (e.g., QuadMesh or contour set).

    Notes
    -----
    This function requires the dataset to contain `XC` and `YC`
    coordinates representing longitudes and latitudes. If these
    are missing, a ValueError is raised.

    Examples
    --------
    >>> ds.plotpc(ds.temp)
    >>> ds.temp.plotpc()
    >>> fig, ax = plt.subplots(subplot_kw=dict(projection=ccrs.PlateCarree()))
    >>> ds.temp.plotpc(ax=ax)
    """

    am_init_kwargs = am_init_kwargs or {}

    # --- Handle both Dataset and DataArray inputs ---
    if isinstance(obj, xr.DataArray):
        ds = obj.to_dataset(name=obj.name or "var")
        da = obj
    else:
        ds = obj
        if da is None:
            raise ValueError("When calling on a Dataset, you must provide `da`.")

    # --- Validate dataset structure ---
    required_coords = {"XC", "YC"}
    missing = required_coords - set(ds.coords) - set(ds.data_vars)
    if missing:
        raise ValueError(
            f"plotpc requires the dataset to contain coordinates {required_coords}, "
            f"but the following are missing: {missing}"
        )

    # --- Handle figure/axis logic ---
    ax = am_kwargs.pop("ax", None)
    if ax is None:
        # I choose the spna region to be my default
        # for my own convenience
        fig, ax = spna()
    else:
        fig = None

    # --- Initialize LLC resampler/map ---
    lm = llc_map(ds, **am_init_kwargs)

    # --- Plot the data ---
    ax, cb, p = lm(da, ax=ax, **am_kwargs)

    return fig, ax, cb, p


# Register the method for both Dataset and DataArray
xr.Dataset.plotpc = plotpc
xr.DataArray.plotpc = plotpc

class llc_map:
    # Tim: note that most of this was copied and pasted from the xgcm documentation
    # Because I couldn't write anything fancier

    def __init__(self, ds, dx=0.25, dy=0.25):

        # Extract LLC 2D coordinates
        lons_1d = ds.XC.values.ravel()
        lats_1d = ds.YC.values.ravel()

        # Define original grid
        self.orig_grid = pr.geometry.SwathDefinition(lons=lons_1d, lats=lats_1d)

        # Longitudes latitudes to which we will we interpolate
        lon_tmp = np.arange(-180, 180, dx) + dx / 2
        lat_tmp = np.arange(-35, 90, dy) + dy / 2

        # Define the lat lon points of the two parts.
        self.new_grid_lon, self.new_grid_lat = np.meshgrid(lon_tmp, lat_tmp)
        self.new_grid = pr.geometry.GridDefinition(
            lons=self.new_grid_lon, lats=self.new_grid_lat
        )
        self.ds = ds



    def __call__(
        self,
        da,
        ax=None,
        op=None,
        figsize=(6, 6),
        show_cbar=True,
        cbar_label=None,
        plot_type='contourf',
        grid=None,
        gridline_kwargs={},
        contour_kwargs={},
        quiver_kwargs={},
        cbar_kwargs={},
        cbar_ticks_params={},
        **plt_kwargs,
    ):

        tiledim = "tile" if "face" not in da.dims else "face"
        allowed_dims = {"i", "j", "i_g", "j_g"}
        assert (
            tiledim in da.dims and set(da.dims) - {tiledim} <= allowed_dims and len(set(da.dims) - {tiledim}) > 0
        ), f"da must have dimensions [{tiledim}, and at least one of 'i', 'j', 'i_g', or 'j_g']"
    
        field = self.regrid(da)

        vmin, vmax = compute_vlims(field, **plt_kwargs)
        vmax = plt_kwargs.pop("vmax", vmax)
        vmin = plt_kwargs.pop("vmin", vmin)

        nlev = 20
        nlev = plt_kwargs.pop("nlev", nlev)

        # Handle colorbar and NaN color
        cmap = Colormaps(nlev).custom_div_cmap() if vmax * vmin < 0 else "viridis"
        cmap = plt_kwargs.pop("cmap", cmap)
        if isinstance(cmap,str):
            cmap = plt.cm.get_cmap(cmap)

        x, y = self.new_grid_lon, self.new_grid_lat

        ## Find index where data is splitted for mapping
        cfield, clon2d, clat2d = cutil.add_cyclic(field, x, y)
        levels = np.linspace(vmin, vmax, nlev)
        levels = plt_kwargs.pop('levels', levels)

        transform_first = plt_kwargs.pop('transform_first', True)

        if plot_type == 'pcolormesh':
            pl = ax.pcolormesh(
                clon2d, clat2d, cfield,
                vmax=vmax,
                vmin=vmin,
                cmap=cmap,
                transform=ccrs.PlateCarree(),
                zorder=0,
                **plt_kwargs,
            )
        elif plot_type == 'contourf':
            pl = ax.contourf(
                clon2d, clat2d, cfield,
                vmax=vmax,
                vmin=vmin,
                cmap=cmap,
                levels=levels,
                transform=ccrs.PlateCarree(),
                zorder=0,
                transform_first=True,
                extend='both',
                **plt_kwargs,
            )
        elif plot_type == 'contour':
            pl = ax.contour(
                clon2d, clat2d, cfield,
                transform=ccrs.PlateCarree(),
                levels=levels,
                zorder=0,
                **plt_kwargs,
            )
        elif plot_type is None:
            pl = None
            pass 
        else:
            ValueError('Please provide valid plot_type, such as \'pcolormesh\', \'contour\', or \'contourf\'')

        # Add label from attributes
        if cbar_label is None:
            cbar_label = ""
            if "long_name" in da.attrs:
                cbar_label = cbar_label+da.long_name+" "
            if "units" in da.attrs:
                cbar_label = cbar_label+f"[{da.units}]"

        # Colorbar...
        if show_cbar:
            cbar_kwargs = copy.deepcopy(cbar_kwargs)

            # Ensure vmin and vmax exist in cbar_kwargs or extract from the plotted data
            vmin = cbar_kwargs.get("vmin", pl.norm.vmin)
            vmax = cbar_kwargs.get("vmax", pl.norm.vmax)
            pad = cbar_kwargs.pop("pad", 0.1)
            orientation = cbar_kwargs.pop("orientation", 'horizontal')
            ticklabel_format = cbar_kwargs.pop('ticklabel_format', '{:.2f}')

            default_ticks = np.linspace(vmin, vmax, 5)
            cbar_kwargs.setdefault("ticks", default_ticks)
            cbar_kwargs.setdefault("shrink", .8)

            if "ticks" not in cbar_kwargs:
                cbar_kwargs["ticks"] = default_ticks
        

            cb = plt.colorbar(
                pl,
                ax=ax,
                orientation=orientation,
                pad=pad,
                **cbar_kwargs
            )
            cb.set_label(cbar_label)
            cb.ax.tick_params(**cbar_ticks_params)

            try:
                if 'd' in ticklabel_format:
                    cb.set_ticklabels([ticklabel_format.format(int(round(t))) for t in cbar_kwargs["ticks"]])
                else:
                    cb.set_ticklabels([ticklabel_format.format(t) for t in cbar_kwargs["ticks"]])
            except Exception as e:
                raise ValueError(f"Failed to format tick labels with '{ticklabel_format}': {e}")

        else:
            cb = None
       
        return ax, cb, pl

    def quiver(self, u, v, ax=None, maskW=None, maskS=None, skip=1, ke_threshold=.1, **kwargs):
        # u and v should already be rotated to true E/N 
        # e.g. via EUVNfromUXVY

        ke = np.sqrt(u**2 + v**2)
        max_speed = np.nanmax(ke)
        u = u.where(ke>ke_threshold*ke.max(),np.nan)
        v = v.where(ke>ke_threshold*ke.max(),np.nan)
        
        x, y = self.new_grid_lon, self.new_grid_lat
        u = self.regrid(u)
        v = self.regrid(v)
        
        # downsample
        x, y, u, v = [ff[::skip, ::skip] for ff in [x, y, u, v]]
        q = ax.quiver(x, y, u, v, transform=ccrs.PlateCarree(), **kwargs)
        return q
        
    def regrid(self, xda):
        """regrid xda based on llcmap grid"""
        return pr.kd_tree.resample_nearest(
            self.orig_grid,
            xda.values,
            self.new_grid,
            radius_of_influence=100000,
            fill_value=None,
        )

def compute_vlims(field, pad_frac=0.2, **plt_kwargs):
    """
    Compute vmin and vmax for a diverging red-blue plot, with
    smart rounding and a bit of padding to reduce color saturation.
    """
    vmax = np.nanmax(field)
    vmin = np.nanmin(field)

    # Symmetric diverging
    if vmax * vmin < 0:
        vmax = max(abs(vmax), abs(vmin))
        vmin = -vmax

    # Fractional padding
    if vmax != 0:
        vmax *= (1 + pad_frac)
    if vmin != 0:
        vmin *= (1 + pad_frac) if vmin > 0 else (1 - pad_frac)

    # Nice rounding
    if np.isfinite(vmax) and vmax != 0:
        exp = np.floor(np.log10(abs(vmax)))
        base = 10 ** exp
        nice_levels = np.array([1, 2, 2.5, 5, 10])
        scaled = abs(vmax) / base
        vmax_nice = base * nice_levels[np.searchsorted(nice_levels, scaled, side="right") - 1]
    else:
        vmax_nice = vmax
        base = 1  # <- ensure base is always defined

    if vmin < 0:
        vmin_nice = -vmax_nice
    else:
        vmin_nice = np.floor(vmin / base) * base

    # Override from plt_kwargs if provided
    vmax_nice = plt_kwargs.pop("vmax", vmax_nice)
    vmin_nice = plt_kwargs.pop("vmin", vmin_nice)

    return vmin_nice, vmax_nice

def process_gridline_labels(gl, label_args):
    plt.gcf().canvas.draw()

    labels = gl._labels
    x_positions = [lbl.artist.get_position()[0] for lbl in labels if '°' in lbl.artist.get_text()]
    y_positions = [lbl.artist.get_position()[1] for lbl in labels if '°' in lbl.artist.get_text()]
    max_x = max(x_positions) if x_positions else None
    min_x = min(x_positions) if x_positions else None
    max_y = max(y_positions) if y_positions else None
    min_y = min(y_positions) if y_positions else None

    x_range = (max_x - min_x) if max_x is not None and min_x is not None else 1
    y_range = (max_y - min_y) if max_y is not None and min_y is not None else 1

    for label in labels:
        artist = label.artist
        text = artist.get_text()
        x, y = artist.get_position()

        # First try to determine direction by the text content
        direction = None
        if 'E' in text or 'W' in text:
            # Longitude labels → likely top or bottom
            # Determine if top or bottom by proximity to max_y or min_y
            if max_y is not None and abs(y - max_y) < 0.1 * y_range:
                direction = 'top'
            elif min_y is not None and abs(y - min_y) < 0.1 * y_range:
                direction = 'bottom'
        elif 'N' in text or 'S' in text:
            # Latitude labels → likely left or right
            if max_x is not None and abs(x - max_x) < 0.1 * x_range:
                direction = 'right'
            elif min_x is not None and abs(x - min_x) < 0.1 * x_range:
                direction = 'left'

        # If still no direction from text, fallback to your previous positional logic:
        # Note, this can be troublesome in some edge cases
        # It is possible for a label to meet multiple criteria, in which case the first
        # condition below will determine the direction
        if direction is None:
            threshold = 0.1
            if min_y is not None and abs(y - min_y) < threshold * y_range:
                direction = 'bottom'
            elif max_y is not None and abs(y - max_y) < threshold * y_range:
                direction = 'top'
            elif max_x is not None and abs(x - max_x) < threshold * x_range:
                direction = 'right'
            elif min_x is not None and abs(x - min_x) < threshold * x_range:
                direction = 'left'

        opts = label_args.get(direction, {})
        pad_value = opts.get('pad', 0)  # could be False, 0, or a number
        
        if opts.get('hide', False):
            artist.set_visible(False)
        if opts.get('rotate', False):
            artist.set_rotation(0)
        if pad_value:
            if pad_value is True:
                pad_value = 0.04  # default pad amount
            if direction == 'bottom':
                artist.set_position((x, y - pad_value * abs(y)))
            elif direction == 'top':
                artist.set_position((x, y + pad_value * abs(y)))
            elif direction == 'left':
                artist.set_position((x - pad_value * abs(x), y))
            elif direction == 'right':
                artist.set_position((x + pad_value * abs(x), y))

        artist.set_fontsize(label_args.get('fontsize', 15))


def gl_label_defaults(fontsize=15):
    return {
        'top':    {'hide': False,  'rotate': True,  'pad': 0.0,},
        'bottom': {'hide': False,  'rotate': True,  'pad': 0.0,},
        'left':   {'hide': False,  'rotate': False, 'pad': 0.0,},
        'right':  {'hide': False,  'rotate': False, 'pad': 0.0,},
        'fontsize' : fontsize
    }

def region_cartopy(
                 n=1,
                 m=1,
                 xmin=-100,
                 xmax=30,
                 ymin=0,
                 ymax=80,
                 figsize=None,
                 landfacecolor='silver',
                 manual_remove_gl_labels=True,
                 projection='Mollweide',
                 show_gl=True,
                 show_land=True,
                 npts=20,
                 return_gl=False,
                 gl=None,
                 gl_dlon=20,
                 gl_dlat=20,
                 set_boundary=True,
                 gl_label_args=None,
                 ax=None,
                 ):

    # --- Detect if user explicitly provided n or m ---
    frame = inspect.currentframe()
    args, _, _, values = inspect.getargvalues(frame)
    user_passed = {k for k, v in values.items() if k in ('n', 'm')}
    # If both n/m are defaults (user called with no args),
    # trigger "special single-plot" behavior
    called_explicitly = 'n' in user_passed or 'm' in user_passed
    
    # --- Special-case behavior for bare call region_cartopy() ---
    if not called_explicitly:
        # You can drop in your "fancy" single-plot behavior here
        # For example:
        fig, ax = plt.subplots(subplot_kw={'projection': ccrs.LambertConformal()})
        ax.set_extent([xmin, xmax, ymin, ymax], crs=ccrs.PlateCarree())
        # ... your other decorations, coastlines, etc.
        return fig, ax
    
    # --- Normal behavior for multi-panel call ---
    if figsize is None:
        figsize = (10 * m, 6 * n)
    
    if projection == 'Mollweide':
        subplot_kw = {'projection': ccrs.Mollweide(central_longitude=(xmin + xmax) / 2)}
        extent = [xmin, xmax, ymin, ymax]
    elif projection == 'LambertConformal':
        subplot_kw = {'projection': ccrs.LambertConformal(
            central_longitude=(xmin + xmax) / 2,
            central_latitude=(ymin + ymax) / 2
        )}
        extent = [xmin, xmax, ymin, ymax]
    else:
        raise ValueError(f"projection must be 'Mollweide' or 'LambertConformal'. Received {projection}")
    
    if ax is not None:
        axes = np.array([ax])
        fig = ax.figure
    else:
        fig, axes = plt.subplots(n, m, figsize=figsize, subplot_kw=subplot_kw)
        if n == 1 and m == 1:
            axes = np.array([axes])  # Make iterable

    gl_list = []

    aoi = mpath.Path(
        list(zip(np.linspace(xmin, xmax, npts), np.full(npts, ymax))) +
        list(zip(np.full(npts, xmax), np.linspace(ymax, ymin, npts))) +
        list(zip(np.linspace(xmax, xmin, npts), np.full(npts, ymin))) +
        list(zip(np.full(npts, xmin), np.linspace(ymin, ymax, npts)))
    )

    for ax in axes.ravel():
        if set_boundary:
            ax.set_boundary(aoi, transform=ccrs.PlateCarree())

        if show_land:
            land = cf.NaturalEarthFeature('physical', 'land', scale='110m',
                                          facecolor=landfacecolor, lw=1, linestyle='--', zorder=1)
            ax.add_feature(land)

        ax.set_extent(extent, crs=ccrs.PlateCarree())

        gl = ax.gridlines(draw_labels=True,
                          crs=ccrs.PlateCarree(),
                          x_inline=False,
                          y_inline=False,
                          linestyle=':',
                          alpha=int(show_gl),
                          zorder=2)
        gl.xlocator = mticker.FixedLocator(range(-180, 180, gl_dlon))
        gl.ylocator = mticker.FixedLocator(range(-90, 90, gl_dlat))
        gl.xformatter = LONGITUDE_FORMATTER
        gl.yformatter = LATITUDE_FORMATTER

        if manual_remove_gl_labels:
            if gl_label_args is None:
                gl_label_args = gl_label_defaults()
        
            # Ensure we don't mutate the input dictionary
            merged_label_args = gl_label_defaults()
            merged_label_args.update(gl_label_args)
        
            process_gridline_labels(gl, label_args=merged_label_args)
        gl_list.append(gl)

    if n == 1 and m == 1:
        axes = axes[0]

    if return_gl:
        return fig, axes, gl_list
    else:
        return fig, axes


def spna(*args, **kwargs):
    """
    Square LambertConformal Subpolar North Atlantic-specific wrapper region_cartopy.

    Examples
    --------
    >>> fig, ax = spna()       # single fancy plot
    >>> fig, axs = spna(1, 3)  # 1×3 Lambert grid
    """
    default_args = {
        'projection': 'LambertConformal',
        'set_boundary': False,
        'gl_dlat': 10,
        'ymin': 40,
        'xmin': -80,
        'xmax': 10,
        'ymax': 80,
        'gl_label_args': {
            'top': {'hide': True, 'rotate': False, 'pad': 0.0},
            'bottom': {'hide': False, 'rotate': True, 'pad': 0.1, 'threshold': 0.0001},
            'left': {'hide': False, 'rotate': False, 'pad': 0.0},
            'right': {'hide': True, 'rotate': False, 'pad': 0.0, 'threshold': 0.2},
            'fontsize': 20,
        },
    }
    default_args.update(kwargs)
    return region_cartopy(*args, **default_args)


def spna_greenlandzoom(set_boundary=False, **kwargs):
    return spna(
        xmax=-20, ymin=50, ymax=83, gl_dlon=10, gl_dlat=10,
        gl_label_args = dict(
            bottom=dict(threshold=0.0001, rotate=True, pad=.05),
            fontsize=16
        ),
        set_boundary=set_boundary,
        **kwargs
    )


def retain_only_perimiter_gl_labels(axes, gl):
    """Currently hardcoded to work with to region_cartopy_lc"""
    nrows, ncols = axes.shape

    for i, ax in enumerate(axes.ravel()):
        g = gl[i]  # gridliner for this axis

        row = i // ncols
        col = i % ncols

        # Retain y-axis for first column
        if col != 0:
            for label in g._labels:
                if ('N' in label.artist.get_text()):
                    label.artist.set_visible(False)

        # Retain x-axis for last row
        if row != nrows - 1:
            for label in g._labels:
                if ('W' in label.artist.get_text()) or (label.artist.get_text() == '0°'):
                    label.artist.set_visible(False)

    return axes
