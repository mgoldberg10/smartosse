# Fig. 9 (p_atm uncertainty) — where we left off

## Update 2026-07-13 (latest): 2x2 redesign per Matt's new vision

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
