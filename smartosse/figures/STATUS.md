# Fig. 7 (Labrador Sea cable "freshwater flux journey", `fig:greenland_adjustment`)

## 2026-07-15: layout rebuilt on Matt's tested skeleton, panel content re-matched to the notebook

Matt wasn't happy with a prior session's first pass at this figure -- panels
looked visibly different from ``greenland_ekman_transport_patmon.ipynb``'s
actual saved output. He supplied his own tested skeleton (verified with fake
cartopy data that panel proportions survive real map projections) and asked
for a fresh, literal port of the notebook's panels onto it, deferring the
two Round-2-reviewer-requested additions (arrow-scale-legend boxes on panel
(a), feature-label legend on panel (d)) to a later pass.

- **Layout**: `fig7_skeleton.py` replaced with Matt's tested version
  (`gs_outer` 2x1 -> row1 `GridSpecFromSubplotSpec` 2x3 with (a)/(b) each
  getting a dedicated colorbar-strip sub-row and (c) spanning both sub-rows
  -> row2 full-width (d)). **Critical fix carried over**: `ax.set_aspect
  ('auto')` on every cartopy geo-axes (a/b/d), called right after axes
  creation and before `set_extent` -- without it, cartopy's equal-aspect
  projection silently shrinks the axes within its gridspec cell at draw
  time to preserve the projection's true aspect ratio, which overrides the
  configured width/height ratios in a way that isn't visible until the
  figure is actually rendered (bare rectangles don't show it). Verified
  with a fake-pcolormesh+coastlines render (not just tinted boxes) before
  and after -- panels now fill their gridspec boxes exactly.
  `fig7_greenland_fwflux.py`'s `make_fig7` now builds the identical
  gridspec (not a simpler 2x2 as before) with the same aspect fix; the two
  files are meant to stay in lockstep -- don't touch one without re-running
  the other's skeleton test.
- **Real bug found and fixed in `smartosse/plot.py`**: routing (a)/(b)'s
  colorbars into their dedicated `cax_a`/`cax_b` strip axes (rather than
  letting `plotpc` steal space from `ax` via `pad`/`shrink`, the only mode
  that existed before) means passing a live `cax=` Axes through
  `cbar_kwargs`. `llc_map.__call__`'s colorbar section did
  `cbar_kwargs = copy.deepcopy(cbar_kwargs)` unconditionally -- deep-copying
  a live `Axes` recurses into its `Spines`, which don't implement
  `__deepcopy__` and raise `ValueError: 'Spines' object does not contain a
  '__deepcopy__' spine`. Fixed by popping `cax` out of a shallow-copied
  `cbar_kwargs` *before* the deepcopy, then passing it straight to
  `plt.colorbar(pl, cax=cax, ...)` (skipping the now-inapplicable
  `pad`/`shrink` steal-space kwargs in that branch). Backward compatible --
  no `cax` key means identical behavior to before.
- **Real content bug found and fixed in `fig7_greenland_fwflux.py`'s panel
  (a)**: the prior session's `plot_panel_a` defaulted `vmax_curl=3` with no
  outlier clipping. The notebook's actual *published* panel (a) (cell 26 of
  the source notebook, the cell whose figure was saved to
  `dwind_labsea_0_20_lambertconformal.pdf`) uses `vmax=40` for the curl
  colorbar range and clips outliers beyond 8 std before plotting
  (`curl_da.where(|curl_da - mean| <= 8*std)`) -- an order-of-magnitude
  colorbar mismatch plus a missing clip, which is why the previous render
  looked nothing like the notebook despite correct quiver scales. Fixed:
  `plot_panel_a` now defaults `vmax_curl=40, clip_std=8`, matching cell 26
  exactly. Also fixed the colorbar to `pad=.08` + 5-point
  `linspace(-vmax_curl, vmax_curl, 5)` ticks + `'{:d}'`-style integer
  labels (`style_colorbar(..., ticks=...)`), matching cell 26's
  `cbar_kwargs` (was `pad=.02` with `style_colorbar`'s default 3 ticks).
- **Real content bug found and fixed in panel (d)**: the prior session's
  quiverkey used `U=5000` at `(X=0.18, Y=0.06)` with no bounding box. The
  notebook's actual published panel (d) (cell 35, saved to
  `dfw_labsea_0_20_lambertconformal.pdf`) uses `U=10000` (label `$10^4$
  m$^3$s$^{-1}$`) at `(X=0.7, Y=0.1)` with a boxing `Rectangle` at
  `(0.625, 0.075)`, size `(0.36, 0.06)`. Fixed to match exactly.
- Panel (b) cbar gained `ticklabel_format='{:d}'` (was defaulting to
  `'{:.2f}'`, e.g. "-10.00" instead of "-10") to match cell 28.
- **Verified against the actual notebook-saved reference PDFs**, not just
  read by inspection: `/work/08381/goldberg/ls6/smart_da/figs/
  greenland_adjustment/individual2/d{wind,bp,fw}_labsea_0_20_
  lambertconformal.pdf` (converted to PNG via `pdftoppm`, this machine has
  no `pdf2image`/`pymupdf`). Panels (a)/(b) now match closely: same
  localized diagonal-band pattern down the Labrador Sea/Davis Strait
  corridor (this is real physics, not a masking bug -- this run
  (`runc68v_froman_partialcables_jrastd/201201/labsea`) is a
  **partial-cable** OSSE, so the wind/current control adjustment is
  genuinely ~zero/NaN-masked outside the region the Labrador Sea cable's
  sensors actually constrain), same color ranges, same quiver
  convergence pattern. Panel (d)'s gateway lines/labels and SPNA
  circulation schematic also match position.
- **Open item, not resolved this session**: panel (d)'s ADV-flux quiver
  field (`field='adv'`) renders visibly denser/darker than the reference
  PDF despite identical `skip=4, ke_threshold_min=.08, ke_threshold_max=.7`
  params to the notebook's own `pq_adv` dict. Suspected cause: the new
  `llc_map` regrids onto a 0.25 deg lat/lon grid by default (`plot.py`'s
  `llc_map.__init__`, `dx=dy=0.25`) before `get_quiver`'s `[::skip]`
  decimation -- if the old (now-removed) `asteoptim`/`smartcables` quiver
  pipeline regridded onto something coarser, the same `skip` value would
  decimate far less aggressively here, explaining the extra density. Not
  chased further this session (would need either the old pipeline's source,
  long gone, or a parameter sweep) -- flag for Matt's review; a larger
  `skip` or narrower `ke_threshold` window on `plot_panel_d`'s
  `quiver_kwargs` is the likely fix if he wants it tighter.
- **Caching added**: `WindBPFWPlotter.load_vel_advfw` (new, in
  `wind_bp_fw.py`) nc-caches `uE`/`vN`/`ADVe_FW`/`ADVn_FW` together, keyed
  on `(run_dir, iternums)`, in the same directory-scoped-cache style as
  `smartosse.osse.ForecastModel`'s existing `advfw_fm_cache_*.nc` (prefixed
  `wb_` to avoid colliding with it, since this class computes advfw
  independently rather than through `ForecastModel(fld_type='fwflx')`).
  First real run this session: 97.6s (full month of 3D trsp_3d_set1 +
  state_3d_set1 across all 6 ASTE tiles, for both iterations). Cache file:
  `.../labsea/wb_veladvfw_cache_iters0_20.nc`. `load_wind_bp_fw` now calls
  this instead of the old separate `load_vel`/`load_state3d`/`get_advfw`
  sequence.
- Both `arrow_legend` (panel a) and `feature_labels` (panel d) kwargs kept
  in the functions but now default to off/`None` -- per Matt's explicit
  ask to defer those two reviewer-requested additions to a later pass, not
  because the code was removed. Flip them on once he's ready.
- Current render: `figures/output/fig7_greenland_fwflux.png`/`.pdf`
  (real `runc68v_froman_partialcables_jrastd/201201/labsea` data,
  `use_latex_times()` + `use_embedded_pdf_fonts()`).

### Next steps

- Panel (d) ADV quiver density (see "Open item" above) -- needs Matt's
  visual call on whether it's worth chasing further.
- Font embedding not yet re-checked with the project's standard
  `grep -a -o '/Subtype */Type[0-9C]*\|/FontFile[0-9]*'` recipe this
  session -- do that before treating the PDF as submission-ready.
- Arrow-scale-legend box (panel a) and feature-label legend (panel d), the
  two reviewer-requested additions, deliberately deferred -- see module
  docstring in `fig7_greenland_fwflux.py`.
- `fig7_greenland_fwflux.py`/`fig7_skeleton.py` still untracked in git, like
  the other per-figure modules in this package.

---

# Fig. 3 (sigma_phibot synthetic OBP uncertainty map, `fig:bp_std`)

## 2026-07-14: new module `fig3_bp_std.py`, thicker/darker gridlines

Matt asked to remake Fig. 3 (the sigma_phibot map in `uncertainty.tex`,
original code in `smart_cables/osse/fig_sigma_pb.ipynb`) with wider
meridian/parallel gridlines, following this package's `figures/fig3...`
naming pattern used by the other per-figure modules.

- New `fig3_bp_std.py`: same content as the notebook (sigma_phibot in cm on
  `spna()`, `grace_cmap`, cable sensor dots, manual horizontal colorbar) --
  only deliberate change is gridline styling.
- **Gridline width/color**: `smartosse/plot.py`'s `region_cartopy`/`spna`
  previously had no way to control gridline styling -- `ax.gridlines(...)`
  was called with no explicit `linewidth`/`color`, which (checked directly)
  resolves to matplotlib's `grid.linewidth`/`grid.color` rcParam defaults,
  `0.8`pt / light grey (`#b0b0b0`). Added optional `gl_linewidth`/`gl_color`
  kwargs to both functions (default `None` -- only passed to `ax.gridlines()`
  if set, so every other figure using `spna()`/`region_cartopy()` is
  unaffected). `fig3_bp_std.py` uses `GL_LINEWIDTH=1.8`, `GL_COLOR='k'`.
  **Color choice**: Matt asked whether black/white/grey reads best against
  this figure's busy rainbow `grace_cmap` fill (white -> blue -> green ->
  yellow -> red -> dark red). Black recommended and used -- it has strong
  contrast against the light end of the colormap and the silver land fill,
  and (checked in the actual render, not just reasoned about) stays legible
  even over the darkest red patches (small fraction of the map area, mostly
  near Greenland/Norway coasts) since gridlines are dotted rather than solid.
  Pure white would vanish over the colormap's own near-white low end; a
  mid-grey is a weaker compromise at both extremes than black.
- **Real bug hit and fixed, not a data issue with our code**: the notebook's
  sensor-location loading (`BPReader(run_dir, iternums=[0]).sensor_args`)
  crashes outright on this machine -- `BPReader.read_data()`'s per-iteration
  `bpdatanom_raw`/`bpdatanom_smooth`/`m_bpday` files are missing from
  `iter0000` on `/scratch` (purged -- same purge issue flagged in
  `fig1_global_cables.py`'s docstring), so `_discover_bp_vars()` finds zero
  variables and the resulting empty `xr.Dataset` has no `'k'` dim to rename,
  raising `ValueError`. Worked around by reproducing `BPReader.get_sensors()`'s
  own data.ecco-fallback logic (Method 2) directly in
  `fig3_bp_std.load_cable_sensor_lonlat()`, bypassing `BPReader` entirely:
  parse `iter0000/data.ecco`'s `gencost_datafile(1)` entry, read that one
  binary (`SMART_bp_..._142sensors_fullnatl.bin`, itself a symlink resolving
  to `/work`, not `/scratch` -- unaffected by the purge) via `read_aste_bin`,
  mask non-sensor cells (`0`, `-9999`) same as `BPReader`. Found 157 sensors
  this way (not 142, despite the filename) -- cross-checked against
  `fig1_global_cables.load_partial_cables()`'s 4 partial-cable coordinate
  files (labsea 64 + subgyre 25 + northsea 41 + newfoundland 27 = 157
  exactly), a strong independent confirmation this is the right sensor set
  for the full SPNA cable.
- Verified end-to-end (real render, `module load texlive` + `esmpy_3.10`,
  `python -m smartosse.figures.fig3_bp_std`), not just read by inspection --
  output visually checked (gridlines clearly bolder/darker, data/cable dots
  otherwise match the existing `figures/bp_day_var_cm_withcable.png`) and PDF
  font embedding re-checked with the project's standard
  `grep -a -o '/Subtype */Type[0-9C]*\|/FontFile[0-9]*'` recipe: real
  embedded Type 1 fonts present. Current render:
  `figures/output/fig3_bp_std.png`/`.pdf`.

### Next steps / open items

- Not yet swapped into the manuscript (`figures/bp_day_var_cm_withcable.png`
  in `smartosse-manuscript/figures/` is still the standing version) --
  flag for Matt's visual review of the new gridlines before replacing it.
- `fig3_bp_std.py` is untracked in git, like the other per-figure modules in
  this directory.

---

# Fig. 1 (global cable network + SPNA inset)

## Update 2026-07-14 (latest): multiline legend height-matched to the inset, fontsize bumped on both legends

Matt liked the multiline-label render from the update below, with 2 more
asks: make that legend's box height ~match the inset's height (top/bottom
aligned), and bump the fontsize a little on both legends (inset + global
panel, so they still match each other).

- **Fontsize: `LEGEND_FONTSIZE` 27.2 (`17*1.6`) -> 32**, still the one
  constant driving both the global panel's Representative/Funded legend and
  the inset's region legend, so they can't drift apart.
- **New `INSET_MULTILINE_LEGEND_LABELSPACING = 0.6`**, applied to
  `legend()`'s `labelspacing` only when `legend_multiline=True` (the
  single-line variant is untouched, keeps matplotlib's own default
  spacing). Tuned by sweep, not guessed: built the actual figure
  end-to-end at each (fontsize, labelspacing) combo and compared
  `ax_inset.get_window_extent()` against `ax_inset.get_legend()
  .get_window_extent()` on the real renderer (`fig.canvas.get_renderer()`
  post-`draw()`) -- matplotlib's own default `labelspacing=0.5` undershoots
  the inset's height at `fontsize=32` (ratio 0.972); `0.6` lands at
  leg_h=465.3px vs inset_h=465.0px (ratio 1.001), effectively exact at this
  figure's size/dpi.
- **Top/bottom alignment came for free once the height matched** -- the
  legend was already anchored at the inset's own vertical center
  (`loc='center left', bbox_to_anchor=(1.05, 0.5)`, unchanged from the
  previous update), confirmed numerically (both bounding boxes' y-centers
  landed at the same value, 350.0px, at every labelspacing tried in the
  sweep) -- so matching the height alone was sufficient, no separate
  top/bottom-anchoring logic was needed.
- Re-rendered both standing variants end-to-end at the new fontsize/
  labelspacing and visually verified:
  `figures/output/fig1_global_cables.png`/`.pdf` (single-line) and
  `figures/output/fig1_global_cables_multiline_legend.png`/`.pdf`
  (multiline, now height-matched).

## Update 2026-07-14 (later, cont.): inset legend to the right + a second, multiline-label render

Per Matt's follow-up review of the top-center/2-col legend from the update
below:

- **Inset region legend moved from top-center/2-col to the inset's right
  side, 1 column.** `plot_spna_inset`'s legend `loc`/`bbox_to_anchor` ->
  `loc='center left', bbox_to_anchor=(1.05, 0.5), ncol=1` (was
  `loc='lower center', bbox_to_anchor=(0.5, 1.0), ncol=2`). Sits outside
  the inset axes' right edge; `bbox_inches='tight'` (already used by both
  `savefig` calls) expands the saved canvas to fit it, same pattern as
  fig9's row-2/row-3 outside-axes legends.
- **Fontsize matched to the global panel's Representative/Funded legend.**
  New shared constant `LEGEND_FONTSIZE = 17 * 1.6` (was a separately
  hardcoded `22` for the inset, `17 * 1.6` for the global panel); both
  legends now reference it, so they can't drift apart again.
- **Two renders produced, per Matt's request** -- `plot_spna_inset`/
  `make_fig1` gained a `legend_multiline` bool (default False, so the old
  single-line-label behavior is still the default for any other caller).
  When True, each legend entry's abbreviated code and parenthetical region
  name split onto two lines (`_region_legend_label()`, replaces the first
  `' ('` with `'\n('`) -- e.g. "LS_cable" / "(Labrador Sea)" stacked,
  instead of "LS_cable (Labrador Sea)" on one line. Matplotlib splits `\n`
  in a `Text` itself (renders each line separately, even under
  `text.usetex=True`), so no extra LaTeX-side handling was needed beyond
  the existing `latex_escape()` call (still applied, on the full
  label before or after the newline split doesn't matter since `latex_escape`
  doesn't touch whitespace/newlines).
- Rendered both end-to-end and visually verified:
  `figures/output/fig1_global_cables.png`/`.pdf` (single-line, the standing
  default) and `figures/output/fig1_global_cables_multiline_legend.png`/
  `.pdf` (new, multiline variant) -- both via the same one-off script
  pattern as before (`module load texlive`, `esmpy_3.10`,
  `make_fig1(legend_multiline=...)`).

## Update 2026-07-14: legend labels, inset gridline labels, legend placement, ASTE domain outline

`fig1_global_cables.py` was already untracked/rendered from a prior session
(no earlier STATUS.md entry for it) with the projection/rectangular-inset
rebuild from the manuscript's Round-2 revision plan already done. This
session closed out the remaining open items from that plan plus a few of
Matt's styling requests, all in `fig1_global_cables.py`:

- **Region legend labels -> experiment codes.** `REGION_LABELS` changed from
  plain region names ("Labrador Sea") to `"LS_cable (Labrador Sea)"` /
  `"SPG_cable (Subpolar Gyre)"` / `"NS_cable (North Sea)"` /
  `"Nfl_cable (Newfoundland)"`, per the manuscript README's Fig. 1 rebuild
  bullet. Underscores are already handled -- the legend call already wraps
  labels in `latex_escape()` (needed since `make_fig1()` renders with
  `use_latex_times()`), so no separate escaping fix was needed here.
- **Inset lat/lon gridline labels: turned out to already be fixed, not a
  live bug.** The old `figures/output/fig1_global_cables.png` (from the
  prior session, timestamped before this one) showed visible "60N/50N/40N"
  labels floating left of the inset frame despite
  `INSET_GL_LABEL_ARGS_NONE` setting `hide: True` on all 4 sides. Suspected
  cause going in: `process_gridline_labels`'s hide is a one-time
  `artist.set_visible(False)` right after `ax.gridlines(draw_labels=True)`,
  and Cartopy's Gridliner regenerates label artists on later draws (e.g.
  `add_inset_indicator_line`'s explicit `fig.canvas.draw()`, or the final
  `savefig`), which could plausibly reset visibility. **Tested directly,
  not just inferred**: built a minimal repro (bare `spna()` call with the
  same `gl_label_args`, drawn 2x + `savefig`) and then the actual
  `make_fig1()` path, checking `gl._labels[*].artist.get_visible()` after
  each draw/savefig. Labels stayed hidden throughout in both cases -- the
  hide mechanism works correctly as written. The stale PNG was just that:
  stale, generated before the current `hide: True` config was in place (or
  from a version of the code predating it). No code change needed; a fresh
  render confirms no lat labels on the inset.
- **Inset region legend: moved to top-center, 2 columns.** Was
  `loc='lower right', bbox_to_anchor=(1.15, 0.0)`; now
  `loc='lower center', bbox_to_anchor=(0.5, 1.0), ncol=2` -- anchors the
  legend box's own bottom-center just above the inset frame.
- **Full ASTE domain outlined/filled on the global panel** (manuscript
  README bullet: "Outline the full ASTE domain in Fig. 1 and mark the SPNA
  window" -- the SPNA window part was already done via the existing black
  box). New `load_aste_domain_mask()` (`open_astedataset().hFacC.isel(k=0)`,
  the standard grid-only load already used elsewhere in this package) +
  new `plot_aste_domain()`, called from `plot_global_panel()` before
  anything else so cable dots/box/legend all land on top of it.
  - **Real bug hit and fixed**: Matt's suggested one-liner
    (`ds.plotpc(mask, ax=ax, levels=[1], cmap='Greys_r')`) hits
    matplotlib's `ValueError: Filled contours require at least 2 levels` --
    `llc_map.__call__`'s `contourf` branch is built for continuous
    multi-level fields (auto `vmin`/`vmax`/`cmap` via `compute_vlims`), not
    a flat single-color fill for a binary mask. `plot_aste_domain()`
    bypasses `ds.plotpc`/`llc_map.__call__` entirely for this (still reuses
    `llc_map.regrid` for the actual LLC tile/j/i -> lat/lon regridding, not
    reimplemented) and calls `ax.contourf` directly with `levels=[0.5, 1.5]`
    + `colors=[color]` (one filled band, fixed color, no colormap) -- 2
    levels bound exactly one region for a binary mask, sidestepping the
    "needs >=2 levels" restriction cleanly rather than working around it.
    A second, separate `ax.contour(..., levels=[0.5], colors='k')` on a
    0/1-filled (not 0/NaN) version of the same regridded field draws a thin
    boundary line -- needed a *different* NaN-handling of the mask than the
    fill: the fill wants non-ASTE cells as NaN (so the base ocean color
    shows through untouched), but a contour *line* can't be traced against
    NaN on one side of the 0.5 threshold, so the outline pass uses a 0/1
    version instead. Verified end-to-end (real render, not just read by
    inspection) and by cropping/inspecting the PNG at the Bering Strait
    notch and the domain's -34S southern cutoff -- the outline is smooth at
    this figure's scale (regrid at `dx=dy=0.5`, coarser than `llc_map`'s own
    0.25 default since this is a binary domain edge, not a field needing
    fine gradients), no blockiness or artifacts.
  - **Color scheme (Matt asked for a recommendation, not just "make it
    work")**: ASTE-domain ocean keeps the pre-existing `OCEAN_COLOR`
    ('silver') -- same shade as the inset's ocean, so the global panel's
    ASTE patch and the SPNA inset visually read as "the same water," tying
    the two panels together. Non-ASTE ocean gets a new, distinct
    `NONASTE_OCEAN_COLOR = '#dbe7ec'` (a pale, cool blue-gray) rather than
    reusing silver everywhere -- picked so it reads as recessive/background
    water (a common light-blue-ocean cartographic convention) without
    competing with the gray/red cable dots plotted on top, and stays
    clearly distinct from both the silver ASTE patch and the white land
    (verified visually, not just by eye on the color values in isolation --
    checked the actual render, not a swatch). Land is drawn *after* the
    ASTE fill (`zorder`: ocean fills 0 -> ASTE patch ~0.5 -> ASTE outline
    ~0.6 -> land 1 -> cable dots 2/3 -> SPNA box 10) so any near-coastline
    regrid bleed from the mask doesn't tint land pixels.
- Module docstring updated to match (legend position, ASTE domain mention)
  -- was describing the pre-this-session state (bottom-right legend, no
  ASTE outline).

Verified via a real end-to-end render (`module load texlive`, `esmpy_3.10`
env, `make_fig1()` -> `savefig` both PNG/PDF) -- not just read by
inspection. Font embedding re-checked with the project's standard
`grep -a -o '/Subtype */Type[0-9C]*\|/FontFile[0-9]*'` recipe: real
embedded Type 1 (`/FontFile` present), consistent with the LaTeX/dvips
route documented for Fig. 9. Current render:
`figures/output/fig1_global_cables.png`/`.pdf`.

### Next steps / open items

- `fig1_global_cables.py` is still untracked in git -- not committed this
  session either (no commit requested). `smartosse/plot_new.py` and
  `smartosse/slope_cable.py` are also untracked, unrelated to this figure.
- Not re-litigated, just noted: `ASTE_OCEAN_COLOR`/`NONASTE_OCEAN_COLOR`
  are this session's judgment call on "most visually pleasing" per Matt's
  open-ended ask -- flag for his review like any other styling choice, not
  presented as final.

---

# Fig. 9 (p_atm uncertainty) — where we left off

## Update 2026-07-13 (latest, cont.): (c) legend height, split the difference

`0.22` (previous update) read as too high to Matt. Settled on the midpoint
between the two tried values, `bbox_to_anchor=(1.0, 0.175)` (halfway between
`0.13` and `0.22`) -- still flush-right, clear of the grey band. Re-rendered:
`figures/output/fig9_patm_unc.png`/`.pdf`.

## Update 2026-07-13 (earlier, cont.): (c) legend nudged up further [superseded, see above]

`ax_c.legend(..., bbox_to_anchor=(1.0, 0.13 -> 0.22))` -- too high per Matt's
next review, see the update above for the resolved value.

## Update 2026-07-13 (earlier): (c)/(d) panel-label height matching + legend tweaks

- **(c) legend fontsize** 13 -> 15.
- **(c) panel label nudged up**: `add_panel_label(ax_c, ..., y=0.95 -> 0.98)`.
- **(d) panel label moved from "floating above the frame" to the right
  margin, height-matched to (c)'s label.** Previously `x=0.0, y=1.15`
  (floating above ax_d's top spine, in the row1/row2 gridspec gap -- see
  the older update below for why: no blank space inside the stacked-to-1
  bars for an interior label). Now `x=1.02, y=0.98` -- same y as (c)'s
  (both axes share one gridspec row, so identical axes-fraction y = identical
  physical height; verified via `get_window_extent()`, both labels' bboxes
  landed at pixel y0=451.6/y1=527.7, i.e. exactly matched, not just close),
  and x=1.02 puts it in the same right-margin column as (d)'s own legends,
  directly above them.
- **(d)'s two legends moved down to sit under the relocated label**:
  `shade_legend` (the "control" p_atm/winds/other key) `bbox_to_anchor`
  y 1.0 -> 0.82; the hatch ("sigma_patm" STD/SPREAD) legend y 0.5 -> 0.40 --
  gap between the two anchors tightened (0.5 -> 0.42) so both still fit
  in the available vertical span once shifted down. Verified via
  `get_window_extent()`: (d) label's bottom edge sits ~0.1px above the
  control legend's top edge (effectively touching, "right above it"), and
  the control legend's bottom sits ~4.5px above the sigma_patm legend's top
  (tight but not overlapping); the sigma_patm legend's own bottom clears
  ax_d's bottom spine by ~18px, not clipped.

Current render: `figures/output/fig9_patm_unc.png` + `.pdf`.

## Update 2026-07-13 (older): colorbar orientation, panel (c) font matching, legend placement, panel (d) legend order

Five targeted styling changes, all in `fig9_patm_unc.py`, verified via a real
end-to-end render (`open_astedataset()`, `use_latex_times()` +
`use_embedded_pdf_fonts()`, `make_fig9(ds)`) on this machine, not just read by
inspection:

- **(a)/(b) colorbar: horizontal-under-both -> vertical, to the right of (b).**
  `make_fig9()`'s manual `cax` placement (still a manual axes, not
  `fig.colorbar(ax=[ax_a, ax_b])`, for the same space-stealing-resize reason
  as before) now sits at `b_x0 + pos_b.width + cbar_pad` spanning `pos_b.y0`/
  `pos_b.height` (`cbar_width=0.018`, `cbar_pad=0.015`, figure-fraction),
  `orientation='vertical'`, label moved from `set_xlabel` to
  `set_ylabel(..., labelpad=8)`.
- **(a)/(b) horizontal buffer added, sizes unchanged**: `map_gap` (the
  variable spacing (a) and (b) apart after cartopy's aspect-shrink resolves)
  0.005 -> 0.02. Both maps are still re-centered as a pair on `row1_center`
  exactly as before -- only the gap between them grew, both widths/heights
  are untouched.
- **Panel (c) y-tick/ylabel fontsize now matches panel (d)'s.**
  `plot_patm_adjustment_combined()` gained a `ytick_fontsize` param
  (defaults to `tick_labelsize` if omitted, so old callers are unaffected)
  so the y-axis tick size can be set independently of the x-axis date-tick
  size (`tick_labelsize`, previously one param drove both). `make_fig9()`
  now passes `ytick_fontsize=18, ylabel_fontsize=30` for panel (c), matching
  panel (d)'s `ytick_fontsize=18, ylabel_fontsize=30` exactly.
- **Panel (c) ylim extended down by 0.3** (`(-1, 3) -> (-1.3, 3)`) to make
  room for the row-2 legend fully inside the white zone below the grey
  `+/-sigma_spread` band (band half-width ~0.65 hPa averaged across the 4
  cables -- verified numerically this session:
  `{'labsea': 0.747, 'subgyre': 0.649, 'northsea': 0.636, 'newfoundland': 0.565}`,
  mean ~0.649).
- **Panel (c) legend moved from lower-left to lower-right**, flush against
  the right spine (`loc='upper right', bbox_to_anchor=(1.0, 0.13)`, was
  `loc='upper left', bbox_to_anchor=(0., 0.18)`) -- verified the legend's
  right edge lands within ~9px of the axes' right edge (609px wide axes,
  i.e. ~1.5%, matplotlib's own legend padding accounts for the rest) and
  sits entirely below the grey band's lower edge, not touching it.
- **Panel (d) "control" shade legend order reversed**: now reads top-to-bottom
  $p_{\mathrm{atm}}$ / winds / other (was other/winds/$p_{\mathrm{atm}}$),
  i.e. the headline result listed first. `_relcon_shade_legend_handles()`
  gained an `order` param (defaults to `reversed(RELCON_GROUP_ORDER)`) --
  `RELCON_GROUP_ORDER` itself (`('other', 'winds', 'patm')`) is unchanged and
  still governs the bars' bottom-to-top stacking order, which this does not
  touch.

Current render: `figures/output/fig9_patm_unc.png` + `.pdf`.

## Update 2026-07-13 (older): 2x2 redesign per Matt's new vision

Matt: the old 4-panels-per-row layout (row 2: one timeseries panel per
cable; row 3: one relcon bar-pair per cable) wasted space reusing the same
Jan01-31 time axis 4x, and row 3's flat-purple stacked bars didn't
distinguish cables at all. New layout, a plain 2x2 grid:

- **(a)/(b)** unchanged (sigma_patm STD/SPREAD maps + shared colorbar).
- **(c)** *all 4 cables' STD/SPREAD |dp_atm| time series merged onto one
  shared axes* -- `plot_patm_adjustment_combined()` (new). Color = cable
  (reuses REGION_COLORS, so it matches (a)/(b)'s map dots and (d)'s bars).
  STD solid / SPREAD dashed (unchanged convention). ONE shared
  +/-sigma_spread band (mean of the 4 cables' own bands -- they're all
  similar magnitude, ~0.3-0.7 hPa) and ONE P&D line, both grey/black
  (basin-wide references, not cable-specific) -- per Matt's explicit choice
  over per-cable bands (option considered and rejected: 4 overlapping
  translucent bands read as muddy). Cable identity is a **direct
  end-of-line label** (colored text at the STD curve's endpoint) instead of
  an 8-entry (4 cable x 2 linestyle) legend -- Matt's call, to keep the
  panel from being legend-dominated. The 4 cables' STD curves converge
  within ~0.5 hPa of each other during the late-Jan spike, so naive
  end-labels at the exact endpoint collide -- fixed with `_declutter_1d()`
  (nudges labels apart along y, preserving rank order, with a thin leader
  line to the true endpoint when nudged). `min_label_gap=0.3` (hPa) is what
  it took to fully separate "NS"/"Nfl" in the final render at this figsize
  -- retune if figsize/fontsize changes.
- **(d)** *per-cable relcon as grouped/shaded/hatched bars*, one x-tick per
  cable, replacing row 3's 4 separate horizontal-bar-pair panels --
  `plot_relcon_bars_grouped()` + `region_group_colors()` (new). Two STD/
  SPREAD bars per cable (`bar_width=0.32`, small `pair_gap`), each stacked
  other/winds/patm as before, but now colored as **light/mid/dark shades of
  that cable's own base color** (`REGION_SHADE_FACTORS = {'other': 0.6,
  'winds': 0.0, 'patm': -0.35}` -- 'winds' is literally the cable's
  unmodified color, i.e. the same swatch as (a)-(c); 'other' lightened,
  'patm' darkened since it's the headline/dominant result) rather than the
  old flat ColorBrewer-purple scheme, so cable identity and
  component/run are both legible without a 12-entry legend. **Hatch (not
  color) distinguishes STD (plain) from SPREAD (`///`)**, since color is
  already spoken for by cable+component -- Matt explicitly asked for
  "something other than color" to mark STD/SPREAD here. Two small separate
  legends off to the right: a neutral-grey shade key ("component":
  other/winds/patm) and a plain hatch key ("run": STD/SPREAD).
- `gs_outer` simplified from 3 rows (`[2.2, 1, 0.45]`) to 2
  (`[1.5, 1]`, `hspace=0.3`); `figsize` shrunk `(18,16) -> (16,13)` since
  there's only one bottom row now, not two. (a)/(b)'s own layout/centering/
  shared-colorbar code is untouched -- still keyed off `gs_outer[0]` and
  `row1_center` exactly as before.
- Old row2/row3 per-cable functions (`plot_patm_adjustment_row`,
  `plot_relcon_bars_row`, `plot_relcon_bars_region`, and the older
  `plot_relcon_bars`/`load_relcon_std_spread` mean-over-region variant) are
  all kept, just unused by `make_fig9()` now -- fall back to them if the
  merged (c)/(d) panels ever read as too cluttered once more data (e.g. a
  5th cable) is added.
- **Real bug found and fixed while first rendering this**: `use_latex_times()`
  makes bare `_`/`&` in plain text invalid LaTeX (see the existing
  `latex_escape()` machinery in `figs_utils.py`, already used by
  `add_panel_label`). `plot_relcon_bars_grouped()`'s new x-tick labels
  (`"LS_cable"` etc., via `ax.set_xticklabels`) went straight to matplotlib
  without it and crashed `latex` outright (`! Missing $ inserted`,
  `LS_cable` read as subscript syntax) -- fixed by wrapping them in
  `latex_escape(...)` before `set_xticklabels`. Caught immediately on the
  first end-to-end render, not a latent bug.
- Verified end-to-end via a one-off script (`open_astedataset()` for `ds`,
  `use_latex_times()` + `use_embedded_pdf_fonts()`, `make_fig9(ds)`), same
  recipe as prior updates. Current render: `figures/output/fig9_patm_unc.png`
  + `.pdf`.
- Added `debug_panel_c.py` -- a paste-into-Jupyter-cells snippet (not an
  importable module -- has `%autoreload` magics) that loads only what panel
  (c) needs (`ds`, `sigma_spread`, `row2_data`) once, then re-plots just
  `ax_c` on repeat, skipping `make_fig9()`'s maps/relcon loads entirely.
  Motivated by Matt hand-copying make_fig9()'s panel-c body into a notebook
  cell and it silently going stale relative to the real source (the legend
  call he'd pasted predated the ncol=4/label_y_offsets changes above) --
  this gives an always-current alternative for panel-only iteration. Same
  pattern (load once + a thin re-plot cell) should be replicated for panel
  (d) if that starts getting the same manual-copy treatment.

## Update 2026-07-13 (older) — where we left off

2026-07-12. Working from `smartosse-manuscript/reviews/fig_revision_plan_reviewer2.md`
(Reviewer #2 comments 1-4). Companion notes: `eta_ib_check_notes.md`,
`eta_ib_histogram.py` (those are for Fig. 10, not this figure, but share the
same STD/SPREAD run pair).

## What exists

`fig9_patm_unc.py` — modular loaders + plotters for the rebuilt Fig. 9:

- **Row 1** (3 panels): (a) sigma_patm STD map, (b) sigma_patm SPREAD map,
  (g) 2-bar relcon (STD vs SPREAD, winds/patm/other stacked, sums to 1).
- **Row 2** (4 panels): one per partial cable (LS, SPG, NS, Nfl) — solid
  STD |dp_atm| curve, dotted SPREAD curve, constant grey +/-sigma_spread band,
  constant dashed P&D-2003 ~2 hPa RMS line.

Every `plot_*` function takes/returns `ax` and passes through `**kwargs`, so
panels can be built and restyled individually in a notebook. `make_fig9()`
assembles the full mosaic as a *starting template*, not a fixed API — expect
to hack on it directly once panel content is finalized.

Not yet run end-to-end against real data (see blocker below) — written
correctly by inspection/reading, not verified by execution.

## Decisions made this session (don't re-litigate without reason)

- Both `sigma_patm` fields are shown as actual maps side by side (a)+(b),
  not one map + a hidden alternative. STD = sub-daily std (main-run prior,
  `wApressure_ASTE270_EXFpress_std_new.bin`). SPREAD = Chaudhuri reanalysis
  spread (`wApressure_ASTE270_jra55_jra3q_era_spread.bin`), Ponte-consistent.
  Both already exist as ASTE-grid weight binaries in `input_weight/` — no
  on-the-fly regridding needed.
- The old Fig. 9 panel (b) — the JRA55-vs-ERA5 MSD contour map — is **gone**.
  P&D (2003) is now just a constant reference line at
  `PD_2003_RMS_HPA = sqrt(4 hPa^2) ~= 2 hPa` (Matt's rough SPNA estimate;
  we don't have the real P&D data). Don't resurrect the MSD map without
  updating the plan doc first.
- relcon panel (g): **2 bars total** (STD, SPREAD), each the mean over the
  4 partial-cable regions — not the per-region grouped/hatched version from
  `fullnatl_skill.ipynb`. That per-region version was explicitly superseded
  by the updated plan doc.
- Fixed a real bug found while porting `fullnatl_skill.ipynb`'s
  `load_grouped_cost`: it pointed both STD and SPREAD `ControlDataset` loads
  at the *same* `data_ctrl_dir`. `data_ctrl_dir_std/` and
  `data_ctrl_dir_spread/` are genuinely different `data.ctrl` files (verified:
  line 8's `xx_gentim2d_weight` points at the std vs spread apressure weight
  binary respectively) — `load_relcon_std_spread()` now uses the matching one
  for each run.
- Row 2 grey band = mean SPREAD-sigma across *that cable's own sensors*
  (`compute_sigma_band_hpa`), not one flat basin-wide number. My call, since
  Matt deferred; revisit if it reads oddly once plotted.
- Fixed the cable-sensor-file glob: was `*{region}.bin`, which also matches
  `..._allbutnorthsea.bin` for `region="northsea"` (silently wrong sensor
  set). Now `*_{region}.bin` (leading underscore).

## Update 2026-07-12 (later same day): panel (a)/(b) now use dedicated plotting fields

The ASTE-gridded `wApressure_*.bin` weight files (what's actually fed into the
OSSEs as control-uncertainty priors) don't make good plots. Added
`gen_patm_uncertainty_fields.py`, which reproduces the STD field
(`jra_daily_std_mean` from `patm.ipynb`) and the SPREAD field (`Ev` from
`test_chaudhuri_uncertainty.ipynb`) directly from the JRA55/JRA3Q/ERA5
reanalysis products, on the native JRA55 lat/lon grid -- meant to be plotted
directly, not regridded onto ASTE. Run with the `esmpy_3.10` conda env (has
xarray/cartopy; the repo's usual env may not). Output:
`figures/data/sigma_patm_{std,spread}_2012.nc` (~7 min to regenerate, mostly
ERA5 I/O -- 28.8 GB raw). `fig9_patm_unc.py`'s `plot_sigma_patm_map()` /
`load_sigma_patm_{std,spread}_map()` / `make_fig9()` now use these for panels
(a)/(b); `load_sigma_patm_{std,spread}()` (ASTE grid) are kept only for row
2's `compute_sigma_band_hpa` (needs cable tile/j/i indexing, which a lat/lon
field can't do).

**Real bug found and fixed, not just the known "weird roll hack":**
`load_forcing_generic`'s lon coordinate is built as
`np.sort((lon_raw + 180) % 360 - 180)` -- the sort reorders the coordinate
*labels* but not the underlying *data* columns, so every field from that
loader is silently misaligned by a fixed cyclic shift. `patm.ipynb`'s
`.roll(lon=320)` before plotting was patching exactly this, for JRA55 only,
right before plotting. Verified two ways (not just assumed): unrolled JRA55
puts ~1020 hPa over the Tibetan Plateau and ~861 hPa over open mid-Pacific
(both impossible); rolled gives ~540 hPa / ~1009 hPa (physically sane).
Cross-correlating JRA3Q/ERA5 against rolled JRA55 over a pure-ocean N.
Atlantic box flips from *negative* correlation at roll=0 to ~+0.5 at
roll=ny/2. **The same bug is in JRA3Q (roll=480) and ERA5 (roll=640)**,
confirmed the same way -- and `test_chaudhuri_uncertainty.ipynb`'s Em/Ev
never dealiased any of the three before combining them, so anything computed
from it, including `input_weight/chaudhuri_method/ev_patm_2012_*.nc` (its
`em_` counterpart is actually corrupt on disk -- `file` reports "data", not
netCDF), predates this fix and should be treated as unverified.
`gen_patm_uncertainty_fields.py` dealiases each product on its own native
grid before interpolating onto JRA55's grid. See the script's module
docstring for the full writeup.

Rendered panels (a)/(b) from the new .nc files to confirm end-to-end (see
scratchpad `fig9_ab_test.png` / `fig9_b_tuned.png` from this session) --
geographically sane (correct coastlines/land mask alignment, plausible SPNA
storm-track pattern in (a), plausible reanalysis-disagreement pattern in
(b)). `plot_sigma_patm_map()`'s default `robust=True` auto-scaling is
whole-globe, which washes out (b)'s SPNA-local contrast (its global max is
~34 hPa, driven by high-latitude/storm-track outliers elsewhere) -- pass
explicit `vmin`/`vmax`/`levels` (e.g. `vmin=0, vmax=6`) when tuning for the
actual submission.

## Update 2026-07-12 (later still): make_fig9() runs end-to-end; data blocker resolved

The run-data blocker below is **stale** -- all 4 regions x both STD/SPREAD
runs now have `iter0000/`, `iter0020/xx_apressure.effective.*`, `data.ctrl`
present on this machine (re-checked directly, not just assumed). `make_fig9()`
now runs start to finish; output saved to
`figures/output/fig9_patm_unc.png` (transparent, `bbox_inches='tight'`).

Two things fixed to get there:
- **Real bug, not data-related:** `plot_patm_adjustment_timeseries` passed a
  raw `pd.DatetimeIndex` straight to `ax.plot()`/`fill_between()`. This env's
  matplotlib (3.4.3) predates pandas 2.x dropping `Index[:, None]`, so that
  raised `ValueError: Multi-dimensional indexing... no longer supported`.
  Fixed by converting to a plain `np.asarray(time)` (datetime64 ndarray) at
  the top of the function -- mpl handles that fine regardless of version.
- Confirmed `figs_utils.use_serif_mathtext()` (called once before plotting)
  does what its docstring says on the actual render: panel letters and any
  `$...$` math (e.g. the `±σ_spread` legend entry) come out serif (Computer
  Modern), while lat/lon gridline labels, colorbar/axis tick numbers, and
  row-2's `Jan/01`-style date ticks all stay sans-serif. Verified by
  pixel-cropping the render, not just by reading the rcParams call.

Known rough edge, not yet fixed: panel (g)'s `other/winds/patm` legend
(`plot_relcon_bars`, `bbox_to_anchor=(0.5, -0.12)` in *panel g's own* axes
fraction) lands in the row1/row2 gap and visually collides with row 2's
`NS`/`Nfl` titles + its own STD/SPREAD/P&D legend, because panel g is short
relative to gs_outer's row-1 height allocation (`height_ratios=[1.3, 1]`,
sized for the wide map panels). Leave for the styling pass in Next Steps #5.

Row-2 magnitudes are now real: STD spikes to ~2.5-2.6 hPa late Jan (LS/SPG/NS),
SPREAD stays mostly within its own ~0.3-0.5 hPa grey band except a similar
late-month uptick -- same order of magnitude as the plan doc's ~4 hPa STD /
~0.3 hPa SPREAD estimates, which is a mild positive signal for the
`reverse_time=True` assumption below, though not a substitute for actually
checking it.

## Update 2026-07-12 (later still): layout/styling pass per Matt's review of the first render

Panel (g) removed (row 1 back to a plain a/b split -- "two above, four
below"). Replaced with a **new row 3 experiment**: per-cable relcon as a
horizontal STD/SPREAD bar pair under each row-2 timeseries panel
(`load_relcon_per_region`, `plot_relcon_bars_region`/`plot_relcon_bars_row`)
-- SPREAD bars are hatched (`spread_hatch='///'`) so they read as distinct
from STD even without the y-tick label. `load_relcon_std_spread`/
`plot_relcon_bars` (the old mean-over-region 2-bar version) are kept, just
unused in `make_fig9()` now.

Other changes, all in `fig9_patm_unc.py` unless noted:
- Row 2 yticks fixed to `(0, 1, 2)` (`plot_patm_adjustment_timeseries`'s new
  `yticks` param) -- gridlines follow automatically. ylim still dips below 0
  (the grey band's lower edge, some data) -- just no tick/label/gridline down
  there anymore.
- P&D 2003 line: densely dotted (`ls=(0, (1, 1))`), `lw=1.8` (was dashed,
  `lw=1.2`). SPREAD lines: now dashed (`ls='--'`, the P&D line's *old* dash
  pattern) -- was dotted (`ls=':'`). New shared constants `STD_LINE_STYLE`/
  `SPREAD_LINE_STYLE`/`PD_LINE_STYLE` so the per-panel lines and the legend
  swatches can't drift apart.
- Row-2 legend rebuilt from black `Line2D`/`Patch` proxies
  (`_row2_legend_handles()`) instead of grabbing the actual plotted-line
  artists -- previously it lived in the Newfoundland panel and every swatch
  came out Newfoundland-green.
- Sigma-band legend label -> `SIGMA_BAND_LABEL = r'$\pm\sigma_{p_{\mathrm{atm}}}^{\mathrm{spread}}$'`
  (was `r'$\pm\sigma_{\mathrm{spread}}$'`).
- Row-2 panel labels now read e.g. "(c) LS_cable" (`add_panel_label`'s new
  `suffix` kwarg, in `figs_utils.py`) instead of a separate `ax.set_title()`
  -- `plot_patm_adjustment_row` no longer sets a title at all.
- Panel (a): explicit `levels=np.linspace(0, 3, 21)`, `extend='max'`,
  colorbar ticks `[0,1,2,3]` (`SIGMA_STD_MAP_KWARGS`/`_CBAR_KWARGS`). Panel
  (b): `levels=np.linspace(40, 90, 21)`, `extend='both'`, ticks
  `[40,50,60,70,80,90]` (`SIGMA_SPREAD_MAP_KWARGS`/`_CBAR_KWARGS`). Both:
  `landfacecolor='white'` via `spna(..., landfacecolor=...)`.
- Fonts: render with `figs_utils.use_serif_mathtext(font_family='sans-serif')`
  explicitly -- **note the function's default flipped to `font_family='serif'`
  (render everything serif)** during this session's fig10 work, so fig9 (which
  wants the old mixed behavior: mathtext serif, plain text sans-serif) now
  needs the explicit override, not the bare call.

**Panel (b) is currently a blank/below-range map, not a bug -- flagging for
Matt to confirm.** `sigma_patm_spread_2012.nc`'s actual SPNA-box range is
~0.3-19 hPa (global max ~34 hPa, per `gen_patm_uncertainty_fields.py`'s own
sanity check and re-verified here: `field.min/max/mean` = 0.35/33.58/2.66
hPa). The requested 40-90 hPa colorbar range is entirely above that, so with
`extend='both'` the whole panel renders as the "under" color (verified by
pixel-sampling the actual PNG, not just by reading the code -- it's genuine
opaque white, not a rendering glitch). Implemented literally as requested
rather than silently substituting a different range, but this needs Matt to
say whether 40-90 was intentional (different units/field in mind?) or a slip
-- panel (a)'s 0-3 hPa range, by contrast, lines up well with its field's
actual ~0.5-4.4 hPa range.

Current render: `figures/output/fig9_patm_unc.png` (transparent,
`bbox_inches='tight'`).

## Update 2026-07-13: styling pass per Matt's second review

- **(a)/(b) now share one range and one colorbar**: both use
  `SIGMA_MAP_KWARGS = dict(levels=np.linspace(0, 3, 10), extend='max')`
  (replaces the separate `SIGMA_STD_MAP_KWARGS`/`SIGMA_SPREAD_MAP_KWARGS`,
  the latter of which was the blank-panel-(b) bug from the previous update --
  moot now, both panels use the same 0-3 hPa range). One shared horizontal
  colorbar (`fig.colorbar(p_a, ax=[ax_a, ax_b], ...)`) sits under both.
  Row-1 height ratio bumped (1.4 -> 1.8) and `figsize` widened (16x11 ->
  18x13) to enlarge the maps; `gs_row1` wspace 0.25 -> 0.03 so they sit
  nearly flush. Panel (b)'s latitude gridline labels are now hidden
  (`spna(..., return_gl=True)` + hiding any label containing `'N'`, same
  pattern as the `fig10_subgyre_pb_misfit_patm_adjustments.ipynb` reference
  notebook) since they'd just duplicate (a)'s.
- **Row 2**: panel-letter/title labels nudged down (`add_panel_label`'s new
  `y` kwarg, `y=0.90` here) so they don't sit flush against the top frame.
  All 4 panels now share one explicit `ylim=(-1, 3)`
  (`plot_patm_adjustment_timeseries`'s new `ylim` kwarg). Leftmost panel's
  ytick label size bumped to 14 (`plot_patm_adjustment_row`) -- the other 3
  panels have no y-axis (spines hidden), so this only needed setting once.
  Legend moved from upper-right to lower-right, `ncol=2`.
- **Row 3**: `RELCON_GROUP_COLORS` changed from red/blue to greyscale
  (`other='#2b2b2b'`, `winds='#b0b0b0'`, `patm='#6e6e6e'`) --  Matt's call,
  picked for 3-way contrast. SPREAD-bar hatching removed
  (`plot_relcon_bars_region`'s `spread_hatch` default `'///' -> None`) since
  the std/spread y-tick labels already disambiguate. `tick_fontsize` default
  8 -> 12 (covers both the std/spread y-labels and the 0/0.5/1 x-labels --
  same rcParam controls both). Group legend's `patm` label now renders as
  `$p_{\mathrm{atm}}$` (new `RELCON_GROUP_LABELS` dict) instead of the bare
  string.
- **Fonts: switched to real LaTeX (Times via mathptmx), not mathtext.**
  Matt asked for the exact snippet flagged as a future option in
  `smartosse-manuscript/README.md`'s "Font choice caveat" -- now wrapped as
  `figs_utils.use_latex_times()` (requires `module load texlive` in the same
  shell before starting Python). This surfaced two real LaTeX-under-usetex
  landmines, now fixed generically rather than special-cased:
  - A bare `_` outside math mode (e.g. `add_panel_label`'s `' LS_cable'`
    suffix) is invalid LaTeX syntax (`text.usetex=True` doesn't auto-escape
    it, unlike matplotlib's own mathtext). Same for a bare `&` (e.g. the
    row-2 legend's `'P&D 2003 (SPNA)'` label -- `&` is a LaTeX
    alignment-tab character outside tabular/math).
  - Fixed with a new `figs_utils.latex_escape(s)` (checks
    `plt.rcParams['text.usetex']`, no-ops if off) -- applied in
    `add_panel_label` (so any suffix is automatically safe) and to
    `_row2_legend_handles`'s `pd_rms_label`. Extend `latex_escape` if a new
    plain-text label needs different characters escaped.
  - Verified both PNG and PDF export run clean under `use_latex_times()`
    with no LaTeX errors (degree symbols in cartopy's gridline labels came
    through fine too). **Bonus**: the LaTeX/dvips PDF route embeds real
    Type 1 fonts (`/FontFile` present) by itself -- checked with the same
    `grep -a -o` recipe from the manuscript README -- so for this figure
    `use_embedded_pdf_fonts()` (which targets the non-usetex mathtext path's
    Type 3 default) isn't actually load-bearing, though harmless to still
    call.
  - `use_serif_mathtext()` (the old mixed serif-math/sans-plain approach)
    is unchanged and still used elsewhere (e.g. Fig. 10) -- this only swaps
    Fig. 9 to the new helper.

Current render: `figures/output/fig9_patm_unc.png` + `.pdf` (regenerated via
a one-off script, `module load texlive && conda activate .../esmpy_3.10`,
calling `use_latex_times()` + `use_embedded_pdf_fonts()` then `make_fig9(ds)`
-- no permanent runner script exists in the repo yet, see Next Steps).

## Update 2026-07-13 (later still): 4 targeted styling fixes per Matt's third review

- **Row-2 panel labels** ("(c) LS_cable" etc.) nudged off the left spine and
  down from the top frame: `add_panel_label` gained an `x` kwarg (mirroring
  the existing `y`) since it previously hardcoded `x=0.0` (flush-left); the
  `make_fig9()` row-2 call now passes `x=0.04, y=0.94` (was `y=0.90` at
  `x=0.0`). Default `x=0.0` preserved for other callers (panels a/b, fig10),
  so this is additive, not a behavior change for existing calls.
- **Row-2 legend** (STD/SPREAD/P&D/sigma-band) moved from inside panel (f)
  (`loc='lower right', ncol=2`) to outside it, one column, matching row-3's
  legend placement exactly (`frameon=False, loc='center left',
  bbox_to_anchor=(1.05, 0.5), ncol=1`).
- **Row-3 (relcon) legend** fontsize bumped 13 -> 18 (was noticeably smaller
  than the row's own 16pt tick labels).
- **Real bug found and fixed: panels (a)/(b) were not centered over row2/
  row3.** The "glue (b) flush against (a)" hack (previous update) repositioned
  (b) relative to wherever cartopy's aspect-driven shrink happened to center
  (a) *within its own half of row 1* -- not row 1's overall center. Since
  row2/row3 span the same full row-1 gridspec extent, this put the whole
  (a)+(b) block measurably left of center relative to the panels below (empirically
  ~0.49 vs ~0.5125 in figure-fraction x, i.e. ~0.4in off center at this
  figsize -- verified with a standalone layout-only reproduction before and
  after the fix, not just eyeballed). Not a legend-spillover illusion, as
  suspected -- a real centering bug. Fixed by computing the combined (a,b)
  pair's width *after* both are drawn (so cartopy's aspect shrink has already
  resolved), then centering that pair on row1's full gridspec extent
  (`row1_center`, captured before the 1x2 subgridspec split) and setting
  *both* axes' positions from that center, rather than anchoring on (a)'s
  incidental position. Verified visually in the actual re-render (both PNG
  and PDF), not just the layout-only repro.

Re-rendered end-to-end via a one-off script (`open_astedataset()` for `ds`,
`use_latex_times()` + `use_embedded_pdf_fonts()`, `make_fig9(ds)`) -- same
recipe as the previous update, still no permanent runner script in the repo
(see Next Steps). Current render: `figures/output/fig9_patm_unc.png` + `.pdf`.

## Update 2026-07-13 (later still): 3 more styling fixes + Fig. 10 re-rendered with LaTeX Times

- Panel (a)/(b) letters doubled: `add_panel_label(ax_a/ax_b, ..., fontsize=60)` (was the
  default 30, unchanged for row 2/3 letters).
- Colorbar `[hPa]` label nudged up (toward the colorbar) slightly:
  `cbar_ab.ax.set_xlabel('[hPa]', fontsize=22, labelpad=2)` (mpl default labelpad is 4).
- Row-3 STD/SPREAD y-tick labels: now upper-case (`'STD'`/`'SPREAD'`) and sized
  independently of the x-tick (0/0.5/1) labels via `plot_relcon_bars_region`'s new
  `ylabel_fontsize` kwarg (`make_fig9()` passes `ylabel_fontsize=22`, vs.
  `tick_fontsize=16` for everything else in that row) -- previously
  `ax.tick_params(axis='both', labelsize=tick_fontsize)` silently overrode the
  y-label fontsize passed to `set_yticklabels`, so both were stuck at 16.
- Re-rendered via the same one-off-script recipe as before (no permanent runner
  yet, still flagged in Next Steps): `figures/output/fig9_patm_unc.png`/`.pdf`.

Also rendered **Fig. 10** end-to-end for the first time via a one-off script
(`make_fig10(ds)`, no kwargs -- panel content/layout untouched) with
`figs_utils.use_latex_times()` + `use_embedded_pdf_fonts()` instead of the
module docstring's old `use_serif_mathtext()` suggestion, per Matt's request to
match Fig. 9's real-Times rendering. Output: `figures/output/fig10_patm_mechanism.png`/`.pdf`
(first files ever written there -- no earlier version to diff against). Slope
comes out ~0.83, matching the module docstring's expected ~0.829. One
pre-existing, unrelated non-fatal print surfaced during the run:
`BPReader.get_cost()` (bp.py:297, called from its own `__init__`) hits
`'dim_0' not found in array dimensions` and prints `"Error during
computation: ..."` instead of raising -- `get_cost()`'s `self.cost` isn't
consumed anywhere in `fig10_patm_mechanism.py`'s plotting path, so panels
(a)-(f) are unaffected (confirmed by inspecting the rendered PNG), but this is
a real latent bug in `bp.py` worth fixing separately if `self.cost` is ever
needed again.

## Update 2026-07-13 (later still): Fig. 10 (e)/(f) swap + eta-skill variant

Per Matt's request, `fig10_patm_mechanism.py`'s (e)/(f) content is now
swapped from the original build: IB scatter is (e) (left column, row 3),
eta skill map is (f) (right column, row 3) -- letters stay in normal
reading-order position, only the content moved (see module docstring NOTE).
This is now `make_fig10`'s standing default, not a one-off flag -- the old
`panel_f_shrink` kwarg (pre-shrinks the colorbar-free scatter panel so its
equal-aspect square doesn't sit too low) is renamed `panel_scatter_shrink`
and now anchors top-left (was top-right) to match the scatter panel's new
column; `plot_ib_scatter` gained an `aspect_anchor` kwarg (default `'NE'`,
called with `'NW'` from `make_fig10`) so the equal-aspect box anchors to
match. `make_fig10` also gained `nlev_eta_skill` (contourf level count for
just the eta-skill map, independent of the other map panels' hardcoded
`nlev=27`) and `eta_skill_cbar_ticks` (explicit colorbar ticks for that one
panel, via `style_colorbar`'s existing `ticks` kwarg).

Rendered a variant via a one-off script with `vmax_eta_skill=0.6,
nlev_eta_skill=12, eta_skill_cbar_ticks=[-0.6, -0.3, 0, 0.3, 0.6]` (Matt's
requested list had `-0.3` twice and no `+0.3` -- treated as a typo for the
symmetric set; flagged to him, unconfirmed). `nlev_eta_skill` went through
11 (initial guess) then Matt asked for 12 explicitly -- 12 is final. Saved
under a different name so it doesn't clobber the standard render:
`figures/output/fig10_patm_mechanism_etaskill0.6.png`/`.pdf` (vs. plain
`fig10_patm_mechanism.png`/`.pdf` from the previous update, which still uses
the function's own defaults: `vmax_eta_skill=1., nlev_eta_skill=20`).

Confirmed (not a bug, just documented in `plot_eta_skill_map`'s docstring):
the eta-skill colormap was already exactly `Colormaps(nlev_eta_skill)
.custom_div_cmap(template_cmap=cmocean.cm.curl_r)` all along, inherited
automatically from `osse.py`'s `_plot_skill` (nlev flows through
plot_eta_skill_map -> OSSE.plot_skill -> _plot_skill's `nlev` param, which
builds both the levels *and* the cmap from the same value) -- nothing to
change there.

**Note on nlev parity:** `Colormaps.custom_div_cmap` forces the color at
`sampled_colors[num_colors // 2]` to pure white. For odd `num_colors` (e.g.
11) that index sits at exactly the midpoint of `linspace(0, 1, num_colors)`,
lining the forced white up with the true zero-skill level. For even
`num_colors` (e.g. 12, 20 -- 20 being `_plot_skill`'s own default elsewhere
in the codebase, so this isn't unusual), that index is slightly off-center
(6/11 of the way, not 0.5), which visibly shifted where panel (f) reads as
"blank" between the nlev=11 and nlev=12 renders -- more of the weak-skill
field lands in/near that off-center white bin at nlev=12. Flagged to Matt as
an expected side effect of the level count, not a rendering bug.

## Known-uncertain, flagged in code (not resolved)

- `load_patm_adjustment(..., reverse_time=True)` reproduces a
  `.sel(time=slice(None,None,-1))` reversal from `patm.ipynb` before stamping
  calendar dates onto the xx_apressure control knots. It worked there but the
  reasoning wasn't re-derived here. **Check the row-2 time series aren't
  calendar-inverted before trusting them**; toggle `reverse_time=False` if so.
  The rigorous alternative (ctrl_t/diag_t interpolation with a verified
  `ctrl_offset`) lives in `eta_ib_histogram.py` — port that over if the naive
  slice/reverse turns out wrong.
- `make_fig9()`'s SPNA projection center is hardcoded
  (`central_longitude=-35, central_latitude=60`) to match `spna()`'s current
  defaults (`xmin=-80, xmax=10, ymin=40, ymax=80`). If those defaults change
  in `smartosse/plot.py`, this goes stale silently.

## Blocker: run data incomplete on this machine [RESOLVED 2026-07-12, see Update above]

Checked `/scratch/08381/goldberg/aste_270x450x180/osses/` before writing
loaders. Only `runc68v_froman_partialcables_jrastd/201201/{labsea,subgyre}`
have `iter0000/` + `xx_apressure.effective` + `data.ecco`/`data.ctrl`.
Missing everywhere else (northsea, newfoundland, and almost all of the
`jraspread` run) — `iter0000/`, `xx_apressure.effective`, `data.ecco`,
`data.ctrl` absent. Matt suspects this is a copy-over-from-another-machine
gap, not a real absence. **Nothing in `fig9_patm_unc.py` can be smoke-tested
past labsea/subgyre STD until this is synced.**

## Next steps

1. Sync/copy the missing `northsea`, `newfoundland`, and `jraspread` run
   directories onto this machine (or point loaders at wherever they live).
2. Smoke-test `load_row2_data()` + `plot_patm_adjustment_row()` on
   `labsea`/`subgyre` STD first (data present) to catch loader bugs before
   the full run set is available.
3. Once data is synced, run `make_fig9()` end-to-end, sanity check the
   `reverse_time` assumption (item above) against known-good adjustment
   magnitudes (~4 hPa STD, ~0.3 hPa SPREAD per the plan doc).
4. Confirm the IB slope 0.83 robustness to `ctrl_offset` (a Fig. 10 loose end,
   noted in `fig_revision_plan_reviewer2.md`, but shares the same alignment
   machinery — worth resolving alongside the `reverse_time` question above).
5. Only after (a) and (b) look right: revisit styling/layout of `make_fig9`
   (legend placement, panel sizing, letter-label fontsizes) — it's a rough
   starting template, not tuned for the actual submission yet. Panels (a)/(b)
   themselves are now resolved (see "Update 2026-07-12" above) — remaining
   work there is just `vmin`/`vmax`/`levels` tuning for the submission, not
   data/alignment.
