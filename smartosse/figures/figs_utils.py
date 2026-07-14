"""
Small plotting helpers shared across the per-figure modules in this package
(e.g. ``fig9_patm_unc.py``, ``fig10_patm_mechanism.py``). Nothing here is
figure-specific -- if a helper starts accumulating figure-specific branches,
it belongs back in that figure's module instead.
"""
import numpy as np
import cartopy.crs as ccrs


def latex_escape(s):
    """Escape LaTeX-special characters in `s` if ``text.usetex`` is currently
    on (see ``use_latex_times``); no-op otherwise.

    Plain (non-mathtext) strings built elsewhere in this package -- e.g. a
    panel-label suffix like ``' LS_cable'`` or a legend label like
    ``'P&D 2003'`` -- are fine under matplotlib's own mathtext renderer, but a
    bare ``_`` or ``&`` outside math mode is invalid syntax to a real LaTeX
    engine (``text.usetex=True``) and errors out. Only handles the characters
    this package's labels actually contain -- extend if a new label needs it.
    """
    import matplotlib.pyplot as plt
    if not plt.rcParams.get('text.usetex', False):
        return s
    return s.replace('_', r'\_').replace('&', r'\&')


def add_panel_label(ax, letter, fontsize=30, suffix='', x=0.0, y=1.0, **text_kwargs):
    """Bold '(a)'-style panel label in the top-left corner of `ax`.

    `suffix` (e.g. ``' LS_cable'``) is appended as plain text after the
    mathtext ``(a)`` -- so the letter stays serif (mathtext.fontset, see
    ``use_serif_mathtext``) while the suffix follows the regular
    ``font.family`` (sans-serif under ``use_serif_mathtext``), giving e.g.
    "(c) LS_cable" with only the "(c)" serif. Passed through ``latex_escape``
    first, so this is safe under ``use_latex_times()`` too.

    `x` (axes fraction, default 0.0 = flush with the left spine) -- raise it
    (e.g. 0.03) to nudge the label right, off the spine.
    `y` (axes fraction, default 1.0 = flush with the top spine) -- lower it
    (e.g. 0.9) to nudge the label down away from the frame.
    """
    kwargs = dict(fontweight='bold', va='top', ha='left', zorder=16)
    kwargs.update(text_kwargs)
    return ax.text(x, y, rf"$\mathrm{{({letter})}}$" + latex_escape(suffix), transform=ax.transAxes,
                    fontsize=fontsize, **kwargs)


def add_cable_scatter(ax, lons, lats, s=10, edgecolor='k', facecolor='w',
                       transform=None, **scatter_kwargs):
    """Scatter a cable's sensor lon/lat locations onto a map axis.

    Small, but re-derived independently in a few places (fig9_patm_unc's
    per-region cable overlay, osse._plot_skill's cable_scatter_kwargs, the
    fig10 notebook) -- centralized here so they share one implementation.
    """
    if transform is None:
        transform = ccrs.PlateCarree()
    return ax.scatter(lons, lats, s=s, edgecolor=edgecolor, facecolor=facecolor,
                       transform=transform, **scatter_kwargs)


def style_colorbar(cb, xlabel=None, nticks=3, fontsize=16, labelsize=None,
                    ticks=None, ticklabels=None, height_frac=None, y_shift_frac=None):
    """Apply consistent tick count/labels + an xlabel to a plotpc colorbar.

    Defaults to `nticks` evenly spaced ticks over the colorbar's own
    (vmin, vmax); pass `ticks`/`ticklabels` explicitly to override (e.g. a
    fixed [0, 0.5, 1] for a ratio panel). Ticks are only auto-formatted with
    plain decimal labels here -- for scientific-notation or integer labels,
    pass `ticklabels` explicitly.

    `height_frac`/`y_shift_frac` reproduce the manual colorbar shrink-and-
    nudge from the original fig10 notebook (needed there because
    ``fig.subplots_adjust(wspace=-0.4, hspace=.1)`` packed panels tightly
    enough that default colorbar placement collided with the next row).
    `height_frac` shrinks the colorbar axis height by that fraction;
    `y_shift_frac` multiplies its y0 (>1 nudges up, <1 nudges down). Both
    default to None (no-op) since a looser gridspec may not need them --
    pass explicit values if colorbars overlap neighboring panels.
    """
    vmin, vmax = cb.mappable.get_clim()

    if ticks is None:
        ticks = np.linspace(vmin, vmax, nticks)
        ticks[np.isclose(ticks, 0, atol=1e-12)] = 0.0
    cb.set_ticks(ticks)

    if ticklabels is None:
        ticklabels = ["0" if t == 0 else f"{t:g}" for t in ticks]
    cb.set_ticklabels(ticklabels)

    if labelsize is not None:
        cb.ax.tick_params(labelsize=labelsize)

    if xlabel is not None:
        cb.ax.set_xlabel(xlabel, fontsize=fontsize)

    if height_frac is not None or y_shift_frac is not None:
        pos = cb.ax.get_position()
        height = pos.height * height_frac if height_frac is not None else pos.height
        y0 = pos.y0 * y_shift_frac if y_shift_frac is not None else pos.y0
        cb.ax.set_position([pos.x0, y0, pos.width, height])

    return cb


def use_serif_mathtext(mathtext_fontset='cm', font_family='serif'):
    """Render everything -- mathtext ($...$, e.g. panel letters and
    LaTeX-style axis labels) *and* plain text (axis tick numbers, cartopy
    lat/lon gridline labels, colorbar tick numbers) -- in a serif font.

    Unlike ``text.usetex=True`` (which routes *all* text through a real LaTeX
    install), this stays in matplotlib's own renderer: `font_family='serif'`
    covers plain text (matplotlib's built-in DejaVu Serif, no LaTeX install
    needed) and `mathtext_fontset` covers ``$...$`` text specifically, which
    otherwise ignores `font.family`. Pass `font_family='sans-serif'` to go
    back to serif-math-only/sans-serif-everything-else. `mathtext_fontset`
    can also be 'stix' (closer to Times than 'cm'/Computer Modern).

    Call this once in a notebook before plotting, the same way you'd
    previously have set ``plt.rcParams.update({"text.usetex": True, ...})``.
    """
    import matplotlib.pyplot as plt
    plt.rcParams.update({
        'text.usetex': False,
        'mathtext.fontset': mathtext_fontset,
        'font.family': font_family,
    })


def use_latex_times():
    """Render all text -- mathtext and plain -- through a real LaTeX install
    with Times-like glyphs (``mathptmx``), rather than matplotlib's own
    mathtext renderer (see ``use_serif_mathtext``).

    Requires a working ``latex`` on PATH -- on this machine, ``module load
    texlive`` in the same shell before starting Python. Slower and more
    failure-prone than ``use_serif_mathtext()`` (depends on the LaTeX
    toolchain working end-to-end, and plain-text labels built elsewhere with
    a bare ``_``/``&`` need ``latex_escape()`` first -- ``add_panel_label``
    already does this), but gives actual Times rather than
    Computer-Modern-ish math + DejaVu Serif plain text.
    """
    import matplotlib.pyplot as plt
    plt.rcParams.update({
        'text.usetex': True,
        'font.family': 'serif',
        'text.latex.preamble': r'\usepackage{mathptmx} \usepackage{amsmath}',
    })


def use_embedded_pdf_fonts():
    """Embed real (Type 42/TrueType) font outlines in PDF output instead of
    matplotlib's default Type 3 (glyphs as vector drawing procedures rather
    than font-program data).

    Type 3 glyphs are technically self-contained but many journal PDF/font
    checkers -- see smartosse-manuscript/README.md's revision TODO, "save
    figures as PDFs with embedded fonts" -- don't count them as embedded, and
    they can render inconsistently or block text selection/search in some
    viewers. Call once before any ``fig.savefig(..., format='pdf')`` (or a
    ``.pdf`` path); has no effect on PNG/other raster output.
    """
    import matplotlib.pyplot as plt
    plt.rcParams.update({'pdf.fonttype': 42, 'ps.fonttype': 42})
