# Sensor-spacing sweep (`sensor_spacing_skill_diff.py`)

## 2026-08-19: new module -- pairwise p_b skill differences, 70/140/210 km

Port of `smart_cables/osse/fullnatl_nthsensors.ipynb` cells 22/24/25
(`sensor_spacing_pb_skill_70_140_210_diff.png`) onto this package's
conventions, pointed at the **new** sweep
`runc68v_froman_partialcables_jraspread_spacing/201201/`, which today holds
`70km/` and `140km/` at 10 iterations and no `210km/` yet. Writes
`output/sensor_spacing_pb_skill_70_140_210_diff.{png,pdf}` and the cache
`data/sensor_spacing_skill.nc`.

- **Built to be finished later.** `build_cache` computes whatever spacings are
  on disk and merges into the cache (`combine_first`, as in
  `gen_appendixB_skill_cache`); a spacing already cached is *reused*, not
  recomputed. `make_fig` draws any panel whose two spacings are both cached and
  leaves the others as empty decorated maps, announcing which. So today: panel
  (a) = 70-140, (b) and (c) blank. When 210 km arrives, drop it in as `210km/`
  (glob is `{spacing}km*`, so the notebook's `210km_71sensors_fullnatl` naming
  works too) and re-run `--rebuild`; only 210 km is computed. Exercised
  end-to-end before shipping by symlinking `140km/` in as a fake `210km/`:
  all three panels rendered, (c) came out identically zero, and only the fake
  spacing was recomputed.
- **`70km/iter0000/` has no `m_bpday`** (only `adm_bpday`), so the 70 km run
  has no first guess of its own to divide by. Iteration 0 is the unassimilated
  forward run, so it is taken from another run -- `140km/iter0000` today, else
  `runc68v_froman_partialcables_jraspread/201201/fullnatl` -- and the
  substitution is printed every time. **This is measured, not assumed**:
  `140km/iter0000/m_bpday` is bit-identical (`max|dp_b| = 0.0`) to that of the
  full-cable `..._jraspread/201201/fullnatl` run, i.e. a completely different
  observing system on the same base config. `check_first_guesses` re-runs that
  comparison over every available donor on each `--rebuild`.
- **`BPReader` bypassed** (`gen_appendixB_skill_cache.load_bp_anom` reused
  directly) -- these directories ship no `data.ecco`, same situation and same
  workaround as `smart_grace_mo_skill` / `fig3_bp_std`.
- **Both 2026-08-14 rendering bugs avoided from the start**: saved
  `facecolor='white', edgecolor='none'` (not `transparent=True`, which speckles
  the coastlines black on a dark ground) and `patch_pdf_indexed_image_bitdepth()`
  called in `__main__` (required because the `contourf` fills are rasterized on
  matplotlib 3.4.3, else the PDF opens as though unfinished). Verified after
  writing: PNG alpha == 255 everywhere, and both image streams in the PDF
  unfilter to exactly their expected byte counts.
  **`smart_grace_mo_skill.py` had both of these bugs and is now fixed the same
  way** -- it rasterizes and was still saving `transparent=True`.
- **No cable scatter**, as in the notebook: each panel differences two
  *different* sensor layouts, so there is no single one to draw. Layouts belong
  in the companion `sensor_spacing_pb_skill_70_140_210.png` (cell 19).
- **Panel titles off by default** (Matt, 2026-08-19); `--titles` writes
  `S(p_b^{70 km}) - S(p_b^{140 km})` over each panel.
- First numbers, wet points, whole ASTE domain: 70-140 has mean `-0.0073`,
  median `-0.0085`, 18% of wet points favouring 70 km -- i.e. **the 140 km
  cable scores better over most of the domain**, in the same direction as the
  notebook's "fewer sensors better!" note on the old sweep, but this time
  without that sweep's `xx_apressure` confound.

# Fig. 10 (p_atm mechanism, `fig:misfit_and_apressure`)

## 2026-08-17 (latest+1): spreadsigma variant tightened

`make_fig10` gained `hspace`/`wspace` kwargs (were hardcoded 0.3/0.15) and
`--figsize`/`--hspace`/`--wspace` CLI flags. Defaults unchanged.

`fig10_patm_mechanism_abcd_spread_spreadsigma.{png,pdf}` re-rendered at
**`--figsize 11 8.0 --hspace 0.02 --wspace 0.02`**. Note the figure *height* is
the main lever, not `hspace`: the maps are equal-aspect and fill the cell
width, so any leftover cell height shows up as whitespace above and below each
map no matter how small `hspace` gets. 10 -> 8 in removes most of it. Picked by
rendering four combos side by side at low dpi
(`hspace/wspace/height` = 0.05/0.05/8.6, 0.02/0.02/8.0, 0.10/0.08/9.0,
0.0/0.0/7.8); 7.8 with zero spacing puts the row-1 colorbar tick labels
uncomfortably close to the row-2 panel borders, so 8.0/0.02 is the pick. The
residual row gap is the colorbar band itself -- shrinking it further needs
`cbar_height_frac`/`cbar_y_shift_frac`, not the gridspec.

Only the spreadsigma file was redone, per the ask;
`fig10_patm_mechanism_abcd_spread.{png,pdf}` is still at the (11, 10) /
0.3 / 0.15 geometry.

## 2026-08-17 (latest): spread (a)-(d) re-rendered -- 2-decimal colorbar ticks,
## no middle tick on (d), perimeter-only lat/lon ticklabels

Three of Matt's asks on `fig10_patm_mechanism_abcd_spread`, all now kwargs
rather than one-off edits, and all defaulting to the previous behavior so
nothing else re-renders differently:

- **`style_colorbar(..., decimals=N)`** (figs_utils) fixes tick-label
  precision: `decimals=2` gives `-0.50 / 0 / 0.50` on (c) and `-0.01 / 0 /
  0.01` on (a)/(b) instead of `%g`'s ragged `-0.5`. Zero stays a plain `0`
  (both the module's existing convention and the notebook's) -- say so if you
  want `0.00` there instead, it is one line. `make_fig10(cbar_decimals=...)` /
  `--cbar-decimals` pass it through to every colorbar at once.
- **(d)'s middle tick dropped** by passing `--ratio-cbar-ticks 0 0.05` (two
  ticks) to the `ratio_cbar_ticks` kwarg added in the previous entry -- no new
  machinery needed. vmax stays the notebook's 0.051, so the `0.05` label sits a
  hair inside the bar's end, exactly as in the reference PNG.
- **`gl_labels='perimeter'`** (`--gl-labels perimeter`) drops interior lat/lon
  ticklabels: (a) latitudes only, (b) none, (c) both, (d) longitudes only. This
  is the original notebook's cell-11 framing (`ig % 2` / `ig < 2` label loop),
  reimplemented through `spna`'s `gl_label_args` rather than by walking
  `gl._labels` after the fact. `_gl_label_args` gained a `hide_left` switch
  alongside `hide_bottom`. **Restricted to `panels='abcd'`** (raises otherwise):
  the 3x2 has no unambiguous perimeter, since (c)'s bottom edge is interior to
  a row whose left panel is the plain-axes IB scatter. Default stays `'all'`,
  so `fig10_patm_mechanism_abcd.{png,pdf}` keeps matching the published 3x2's
  every-panel framing.

Both spread renders were redone with all three (the spread-sigma variant too,
so the pair stays comparable; its (d) ticks are `0 0.15`):
`output/fig10_patm_mechanism_abcd_spread{,_spreadsigma}.{png,pdf}`. PDFs
checked clean (no sub-8-bpc indexed images, EOF intact).

## 2026-08-17 (later): (a)-(d) for the SPREAD-prior run, colorbar limits taken
## from the notebook -- and what the ratio panel's denominator actually is

Matt asked for the (a)-(d) subset regenerated for the **spread-based** p_atm
uncertainty (as opposed to std / day-to-day), with the colorbar limits read off
the notebook cell that produced
`apressure_variability/subgyre_wmisfit_apressure_SPREAD_jan012012_opt0_opt20_ONLY_stdUncRatio.png`
(`~/smart_cables/osse/fig10_subgyre_pb_misfit_patm_adjustments.ipynb`, cells
1/4/6/11/14).

**Config that reproduces that PNG** (cell 11 + cells 1/4/6):

| piece | value |
| --- | --- |
| run | `runc68v_froman_partialcables_jraspread/201201/subgyre/`, iters 0/20 (intact on /scratch, own `data.ecco`, no fallback needed) |
| knots | `xx_apressure.effective`, iters **1 and 20** (both present here) |
| (a)/(b) `vmax_misfit` | 0.01 (same as the std figure) |
| (c) `vmax_ctrl` | **0.5 hPa** (vs. 4 hPa for the std run -- the spread run's iter-20 knots only reach -37/+83 Pa, i.e. -0.37/+0.16 hPa on the plotted day) |
| (d) `vmax_ratio` | **0.051**, with explicit ticks `[0, 0.025, 0.05]` |
| (d) sigma | `wApressure_ASTE270_EXFpress_std_new.bin` -- the **std** prior, see below |

New in the module for this: `--vmax-misfit` / `--vmax-ctrl` / `--vmax-ratio` /
`--ratio-cbar-ticks` CLI flags and a `ratio_cbar_ticks` kwarg on `make_fig10`
(wired into `style_colorbar`'s `ticks` for (d), exactly like the existing
`eta_skill_cbar_ticks` for (f)). The explicit ticks are needed because
style_colorbar's default 3 evenly spaced ticks over (0, 0.051) label the middle
one `0.0255`.

### The ratio panel divides the SPREAD run's adjustments by the STD sigma

Notebook cell 1 reads `spread = True` -> `wApressure_ASTE270_EXFpress_std_new.bin`,
i.e. the if/else branches are swapped relative to the flag name, so the figure
that is *named* SPREAD uses the **std** sigma as the denominator. That is not a
transcription slip on my part and it is not obviously a slip on the notebook's
either -- the saved filename says `stdUncRatio`, and it is what the pixels show:
rendering both candidates at vmax=0.051, the std sigma reproduces the reference
PNG's panel (d) (broad grey field, dark ridge hugging the SE Greenland coast,
light lobe over the cable) while the spread sigma saturates solid black over the
whole subpolar basin. Field maxima for the spread run's `std(dp_atm)`:

* / `EXFpress_std_new.bin` (std prior, sigma mean 164 Pa): **max 0.084**, median 0.0035 -- vmax 0.051 clips the peak slightly, the same kind of deliberate under-tuning as the vmax=0.11-vs-0.575 case noted in the module docstring.
* / `jra55_jra3q_era_spread.bin` (spread prior, sigma mean 1448 Pa): max 0.148, median ~0.
* / `jra2012_daytoday_std.bin` (the unit-bug file): max 3.47 -- irrelevant here, listed only for scale.

Both renders are in `output/`:

* **`fig10_patm_mechanism_abcd_spread.{png,pdf}`** -- reproduces panels (a)-(d) of the notebook's
  SPREAD reference PNG (verified by eye against it:
  same misfit dipole, same +-0.5 hPa lobes, same grey ratio field including the
  East Greenland coastal ridge). Use this if the point of (d) is "how big are
  the spread run's adjustments compared with the *std* prior".
* **`fig10_patm_mechanism_abcd_spread_spreadsigma.{png,pdf}`** -- same
  everything, but (d) divides by the spread prior the run actually used, at
  `--vmax-ratio 0.15 --ratio-cbar-ticks 0 0.075 0.15`. Panel (d) becomes a
  clean cable-centered blob peaking at ~15% with no coastal ridge. This is the
  self-consistent reading of "adjustments stay within a fraction of the assumed
  uncertainty" for a spread-prior run, and is probably what controls.tex wants
  if the spread figure is the one that ships -- Matt's call, not made here.

Panel (d) keeps the module's `nlev=27` (26 contour levels) rather than the
notebook's `nlev=20` for that panel; only the color limits were changed, per
the ask. The `BPReader.get_cost()` `'dim_0'` print appears here too and still
affects nothing.

## 2026-08-17: `--panels abcd` (top 2x2 only) + a `__main__`, and the module's
## defaults have drifted onto the mis-weighted day-to-day run

Matt asked for an option to render only panels (a)-(d) and for both a PNG and a
PDF of it. Three changes to `fig10_patm_mechanism.py`, plus one finding that
matters more than the layout work.

- **`make_fig10(..., panels='abcd')`** builds the top 2x2 and skips the eta OSSE
  load entirely (`load_eta_osse`/`compute_ib_scatter` are now inside an
  `if 'e' in panels or 'f' in panels`), so the subset needs neither the eta
  nature run nor the ~minutes-long xmitgcm read. `PANEL_SETS` holds the two
  supported sets (`'abcd'`, `'abcdef'`) and their default figsizes; anything
  else raises. Panel content and styling go through the identical code path --
  the only deliberate layout difference is that **(d) keeps its bottom
  longitude labels** (the 3x2 hides them only because (f) sits under it).
  `figsize` defaults to `(11, 10)` for the subset, i.e. exactly 2/3 of the
  3x2's `(11, 15)` at the same `hspace=0.3`, so the two rows are proportioned
  and spaced exactly as rows 1-2 of the full figure. That inherits the full
  figure's fairly generous inter-row gap; pass e.g. `figsize=(11, 8.5)` to
  tighten it, at the cost of no longer matching the 3x2's proportions.
- **`__main__` added** (the module had none -- previous renders were one-off
  scripts, see the 2026-07-13 entries): `python -m
  smartosse.figures.fig10_patm_mechanism [--panels abcd]`, same
  `use_latex_times()` + `use_embedded_pdf_fonts()` +
  `patch_pdf_indexed_image_bitdepth()` + opaque-white-savefig recipe as
  `fig5_misfit_rmse_skill`. Writes `output/fig10_patm_mechanism{,_<panels>}.{png,pdf}`.
  New flags: `--run-dir`, `--sigma-file`, `--patm-iternums`, `--out-name`.
- **Two data-availability workarounds**, both new since the July render:
  `load_bp_misfit_maps` now falls back to `BP_SIGMA_FILE` (the canonical /work
  copy of `bp_var_day_coarse4320_detide16constituent_std_cm`, md5
  `c2894df2...`, verified byte-identical to the run-local copies that survive
  under `BADrunc68v_.../`, and the same file for every region) when the run
  directory has no `data.ecco`, by stubbing `BPReader.read_weight` for the
  construction and attaching `sigma`/`weight` afterwards -- same purge
  workaround, same reason, as `fig3_bp_std.load_cable_sensor_lonlat`. And
  `make_fig10` gained `patm_iternums` because `iter0001` (the module's default
  first knot iteration) is gone from the daytoday subgyre run; only the *last*
  entry is ever indexed (`ioptim=-1`), so `(0, 20)` -- the `__main__` default
  -- is inert for the figure.

### The finding: `RUN_DIR`/`sigma` no longer point where the published figure came from

`fig10_patm_mechanism` imports `RUN_DIR_ROOT_STD` and `load_sigma_patm_std`
from `fig9_patm_unc`, and **both were repointed after Fig. 10 was last
rendered** (2026-07-13):

- `EXT='_daytoday'` (fig9_patm_unc.py:116) moved `RUN_DIR` from
  `runc68v_froman_partialcables_jrastd/201201/subgyre/` to
  `..._jrastd_daytoday/201201/subgyre/`.
- `SIGMA_STD_FNAME` is assigned twice (fig9_patm_unc.py:98-99); the second
  assignment wins, moving sigma from `wApressure_ASTE270_EXFpress_std_new.bin`
  to `wApressure_jra2012_daytoday_std.bin`.

That second file is the one with the **hPa-vs-Pa unit bug** documented in the
2026-08-06 entry below, and the daytoday runs are the ones that ran with it, so
with today's defaults panels (c)/(d) come out badly wrong: iter-20 knots reach
-2456/+3121 Pa (25-31 hPa, saturating (c)'s +-4 hPa scale basin-wide) and
`std(dp_atm)/sigma` has median 3.0 and max 86, i.e. (d) is solid black
everywhere against its 0-1 scale. Renders of both configurations are in
`output/`:

- **`fig10_patm_mechanism_abcd.{png,pdf}`** -- matches the published
  `fig:misfit_and_apressure` panels (a)-(d). Explicit flags, not the module
  defaults: `--run-dir .../runc68v_froman_partialcables_jrastd/201201/subgyre/
  --sigma-file .../wApressure_ASTE270_EXFpress_std_new.bin --patm-iternums 1 20`.
  That run is intact on /scratch (iter0000-0020, its own `data.ecco` and
  errfile, so no fallback is used). Verified against `output/fig10_patm_mechanism.png`'s
  rows 1-2 by eye: same misfit dipole, same +-2 hPa adjustment lobes, same
  localized grey ratio blob.
- **`fig10_patm_mechanism_abcd_daytoday.{png,pdf}`** -- the *current module
  defaults*, kept only as the evidence for the paragraph above. Do not use it
  for the manuscript.

Unresolved, for Matt: whether the drift is intentional (Fig. 10 meant to follow
Appendix B onto the day-to-day prior, in which case it needs the *reruns* with
`wApressure_jra2012_daytoday_std_Pa.bin`, which don't exist yet) or whether
Fig. 10 should pin the sub-daily-std run explicitly instead of importing
fig9's constants. Nothing was changed in `fig9_patm_unc.py`, and Fig. 10's
imports were left as-is.

The pre-existing `BPReader.get_cost()` `'dim_0' not found` print (bp.py:297,
noted 2026-07-13) still appears and still affects nothing -- `self.cost` is
unused on this path.

# Fig. 5 (SPNA_cable misfit / RMSE / skill triptych, `fig:fullnatl_noapress_rms_skill`)

## 2026-08-14 (later): black blobs in the PNG, unopenable PDF -- both fixed

Matt reported the first render as "a little off": black blobs behind the grey
land in the PNG, and a PDF that Acrobat wouldn't open ("as though it wasn't
completed"). Two independent bugs, neither in the panel content -- the map
pixels are unchanged (still the same 98% match to the notebook's PNG; the
differing pixels are still only the gridlines and panel letters).

- **Black blobs = `savefig(..., transparent=True)`.** The Natural Earth land
  polygons (`plot.region_cartopy`'s `silver` feature) and the regridded ASTE
  field don't tile the map exactly, so a transparent save leaves alpha=0
  pinholes and blobs along every coastline -- ~5% of the pixels inside each
  axes. Composited on white they vanish, which is why they never showed up in
  the notebook (inline output is composited on white) or in the pixel diff
  against `misfit_rmse_skill_opt_20ONLY.png` (identical alpha, so the
  as-rendered comparison was blind to it). Composited on *black* -- Acrobat's
  dark mode, most image viewers' dark themes, pdflatex -- they are the blobs.
  **Now saved `facecolor='white', edgecolor='none'`, no `transparent`.** The
  output PNG is now fully opaque (alpha == 255 everywhere) and its white
  composite is byte-identical to the previous render. Note the notebook and
  `fig3_bp_std.py` both still pass `transparent=True` and have the same latent
  issue.
- **Unopenable PDF = a matplotlib 3.4.3 bug in *rasterized* image output**, hit
  here only because this module rasterizes the `contourf` fills.
  `backend_pdf.PdfFile._writeImg` re-encodes any rasterized image with <= 256
  colors as an `/Indexed /DeviceRGB` palette image; Pillow packs a 16-color
  panel at **4 bits/pixel** and matplotlib records `/BitsPerComponent 4` in the
  image dict -- but writes `/DecodeParms << /Colors 1 /Columns W /Predictor 10
  >>` with **no `/BitsPerComponent`**, which the PDF spec defaults to **8**. A
  conforming reader therefore unfilters the PNG predictor at twice the real row
  stride and the image stream fails to decode. Matplotlib's Agg path never
  re-reads the file, so the PNG was fine and only the PDF was broken. Panels
  (a) and (c) tripped it (16 and 15 colors -> 4 bpc); panel (b) has 20 colors
  -> 8 bpc and was fine, which is the "half-drawn" look. Fixed upstream in
  matplotlib 3.5; this env is pinned at 3.4.3.
  **Fix: `figs_utils.patch_pdf_indexed_image_bitdepth()`**, a small idempotent
  `PdfFile.beginStream` wrapper that copies the image dict's
  `BitsPerComponent` into the `DecodeParms` when the two would disagree. It is
  a no-op on a matplotlib that already emits the key, so it is safe to call
  unconditionally; `fig5_misfit_rmse_skill.__main__` now calls it right after
  `use_embedded_pdf_fonts()`.
  **Verified structurally**, not by eye (no `gs`/`qpdf`/`pdfinfo` on this
  machine): all 40 xref offsets resolve to their objects, and all six image
  streams now Flate-decompress *and* PNG-unfilter to exactly
  `Height * ceil(Colors*BitsPerComponent*Width/8)` bytes. Before the patch the
  two 4-bpc streams ran short mid-row -- which is the decode failure Acrobat
  was reporting. PDF still 479 KB.
- **`si_skill_over_optim.pdf` has the identical PDF bug** (3 of its 16 image
  streams are sub-8-bpc) and needs the same one-line call added to its
  `__main__` and a re-render. Not done here. Scan for it with:
  `grep -a -c '/BitsPerComponent [1247]' output/*.pdf`.

## 2026-08-14: new module `fig5_misfit_rmse_skill.py`, gridlines matched to Fig. 3

Matt asked for a per-figure module behind `misfit_rmse_skill_opt_20ONLY.png`
(`results.tex:9`), a port of `smart_cables/osse/fullnatl_skill.ipynb` cells
1-11 onto this package's conventions, with **everything matching the notebook
except the lat/lon gridline weight, which should match `fig3_bp_std.png`'s**.
Writes `output/fig5_misfit_rmse_skill.{png,pdf}` and the cache
`data/fig5_misfit_rmse_skill.nc`.

- **Run: `runc68v_froman_partialcables_jraspread/201201/fullnatl`, iterations 0
  and 20** -- the notebook's first (uncommented) `run_dir_root`. Unlike most
  of the runs the other modules depend on, this one is *intact* on `/scratch`:
  `iter0000` and `iter0020` both still carry `bpdatanom_*`, `bpdifanom_*` and
  `m_bpday`, so `BPReader` constructs normally and none of the
  data.ecco-fallback workarounds that `fig3_bp_std` / `smart_grace_mo_skill` /
  `gen_appendixB_skill_cache` need apply here. `cable_sensor_lonlat` just uses
  `osse.fm.bpr.sensor_args` (157 sensors, from `bpdifanom_raw`), with a
  defensive `get_sensors()` call in case that stops holding.
- **Gridline weight: 1.0 pt / `'gray'`, and it is `import`ed from
  `fig3_bp_std` (`GL_LINEWIDTH`, `GL_COLOR`), not re-declared**, so the two
  figures can't drift. **Which value that is was settled against the saved
  PNG, not the source**, because the two disagree on their face:
  `fig3_bp_std.py`'s mtime (2026-07-31) is *later* than
  `output/fig3_bp_std.png`'s (2026-07-14), and the 2026-07-14 STATUS entry
  below records `GL_LINEWIDTH=1.8, GL_COLOR='k'` while the file today says
  `1` / `'gray'`. Measured directly in `output/fig3_bp_std.png`: parallels are
  3-4 px wide at dpi=300 (1.0 pt = 4.2 px; 1.8 pt would be 7.5 px) with core
  pixels at RGB 128, i.e. `gray` -- so the standing render *is* 1.0/`'gray'`
  and the 07-31 edit is what's reflected in it. The 1.8/`'k'` note below is
  stale; don't "restore" it.
  The notebook itself called a bare `spna(1, 3)`, i.e. matplotlib's
  `grid.linewidth`/`grid.color` rcParam defaults (0.8 pt, `'#b0b0b0'`).
- **Verified as a real render against the notebook's own PNG, not by
  inspection.** Same canvas (5507x1507 px) and **98.07% of pixels identical**;
  of the 128k that differ, 91% are the gridline pixels themselves and the rest
  are gridline/fill antialiasing blends over panel (b)'s dark `Purples` (new
  `[87,69,104]` vs old `[52,0,103]`, etc.). Nothing in the data, colormaps,
  ranges, level counts, colorbar ticks/labels, cable markers or panel-label
  placement moved.
- **Panels (a)/(c) multiply by `hFacC[0]` while (b) uses `.where(hFacC[0])`** --
  the notebook's asymmetry, deliberately preserved. It is not a slip: land
  going to *0* rather than NaN is what puts it at the centre of the two
  diverging colormaps; `.where` on (b) keeps land blank under `Purples`.
- **One `llc_map` for the whole figure, not one per panel.** `ds.plotpc()`
  constructs a fresh `llc_map` (a KD-tree over the full ASTE swath) on every
  call, so the notebook built three. `draw_panel` calls a prebuilt one
  directly -- which is all `plotpc` does internally -- for the identical
  regrid and `contourf`. Same pattern as `smart_grace_mo_skill` /
  `advfw_skill_maps`.
- **`contourf` fills rasterized per-collection** (matplotlib 3.4's `ContourSet`
  is not an Artist, so `rasterized=` handed to `contourf` is dropped):
  **PDF 4.3 MB -> 479 KB**, no change to the PNG at all. `--no-rasterize` /
  `rasterize=False` for fully vector fills.
- The notebook's hand-written "hide the 'N' labels on `gls[1:]`" loop is
  replaced by `plot.retain_only_perimiter_gl_labels` (post-`fig.canvas.draw()`,
  as in `smart_grace_mo_skill`); checked in the render -- latitude labels on
  (a) only, panels (b)/(c) clean.
- Panel letters go through `figs_utils.add_panel_label`, i.e. `$\mathrm{(a)}$`
  rather than the notebook's plain `'(a)'`. Under `use_latex_times()` +
  `mathptmx` both are upright Times; the pixel diff above covers this.
- Cache holds the three 2-D panel fields **plus the 157 sensor lon/lats**, so
  re-laying-out the figure needs only `data/fig5_misfit_rmse_skill.nc` and the
  `/work` grid -- nothing from `/scratch`, which is the part that will be
  purged first. Numbers: misfit |max| 0.0257 (p98 0.0072, nothing beyond the
  +/-0.02 colorbar), RMSE max 50.1 cm / mean 3.35 cm (22.9% of wet cells run
  past the 5 cm top, as in the published panel -- the coastal/semi-enclosed
  maxima `results.tex` describes), skill mean +0.048.
- `BPReader.get_cost()` prints `Error during computation: 'dim_0' not found in
  array dimensions` during the cache build. **Pre-existing and harmless** --
  `get_cost` sums over `('time', 'dim_0')`, but `get_sensors` now labels its
  index DataArrays `dims='sensor'`, so the selection comes back as
  `(ioptim, time, sensor)` and the old auto-generated `dim_0` name is gone. It
  is caught inside `BPReader`, only `self.cost` is lost, and the figure never
  reads it. The notebook prints the same line. Not fixed here (it would touch
  every `BPReader` caller); worth a separate pass.
- Font embedding checked with the project's standard
  `grep -a -o '/Subtype */Type[0-9C]*\|/FontFile[0-9]*'` recipe: real embedded
  Type 1 (`/FontFile` present).

### Next steps / open items

- Not swapped into the manuscript -- `smartosse-manuscript/figures/
  misfit_rmse_skill_opt_20ONLY.png` is still what `results.tex:9` includes.
  Flag for Matt's visual review of the darker gridlines first, same as Fig. 3.
- Fig. 3 itself has **not** been re-rendered from its current 1/`'gray'`
  source in this session, and its own standing item below (swap
  `bp_day_var_cm_withcable.png` for `output/fig3_bp_std.png` in the
  manuscript) is still open.
- `fig5_misfit_rmse_skill.py` is untracked in git, like the other per-figure
  modules here.

---

# SMART vs GRACE annual monthly skill (`smart_grace_mo_skill`)

## 2026-08-14: notebook ported into the package; panel (b) intentionally blank

`smart_day_skill_grace_mo_skill.png` (the SPNA_cable_annual / GRACE_annual pair)
now has a module: `smart_grace_mo_skill.py`, a port of
`smart_cables/osse/grace_llc4320_year_clean.ipynb` cells 42-47 onto this
package's conventions (`llc_map` regrid done once per panel instead of a
`ds.plotpc` regrid, `figs_utils` panel labels + cable scatter,
`retain_only_perimiter_gl_labels` instead of the notebook's hand-written
"hide the 'N' labels on axes[1]" loop, netCDF cache, rasterized contour fills).
Writes `output/smart_day_skill_grace_mo_skill.{png,pdf}` and
`data/smart_grace_mo_skill.nc`. Color scale, colormap, layout, f/H contour and
sensor scatter are the notebook's, unchanged.

- **Run: `runc68v_froman_natl_1month_alldailyxx_gracellc4320_sc_spread/2012/
  fullnatl`, iterations 0 and 2** (Matt's, 2026-08-14). This is the
  reanalysis-spread cable run, i.e. NOT the run behind the currently published
  PNG -- that one (`..._gracellc4320_sc/2012/`) has had its `m_bpday` `.data`
  purged, only `.meta` survives, so the published panel (a) cannot be
  regenerated as-is. The figure will therefore differ in detail from what is
  in the manuscript today; the biggest visible change is more negative skill
  along the Gulf Stream / Grand Banks.
- **Panel (b) is blank on purpose.** The GRACE-equivalent counterpart of the
  spread cable run does not exist yet. The panel's code path is written and
  *tested* (`compute_grace_skill` / `load_bpmon_anom`, exercised against the
  old non-spread `..._gracellc4320/2012/` run: mean skill +0.0065, and it
  reproduces the published panel (b)'s broad pale-green domain-wide skill,
  pink Gulf Stream and Iceland-Scotland striping). When the run lands, point
  `--grace-run-dir` at it, or update `GRACE_RUN_DIR`, and rerun with
  `--rebuild`; nothing else changes. `--grace-run-dir <old run>` also previews
  what (b) will look like.
- **The NR runs out on 2012-11-15, so November is dropped by default.**
  `phibot_daily` covers 2011-09-13 - 2012-11-15; the FM writes 367 daily
  records through 2013-01-01. The notebook's plain `resample('1M')` on both
  sides therefore built a 15-day NR November mean and a 30-day FM November mean
  and compared them. `complete_months_only=True` (default) keeps Jan-Oct 2012,
  10 monthly samples. **This is not cosmetic**: the two maps correlate at only
  0.84, mean skill +0.0026 vs +0.0019, fraction of cells with positive skill
  0.313 vs 0.256. `--all-months` reproduces the notebook's numbers exactly.
- **Skill is scored on MONTHLY means even though the cable assimilates DAILY
  OBP** -- that is the entire point of the pair (panel (b)'s observing system is
  monthly), and it is why the filename says "smart_day_skill" while the metric
  is monthly. Daily-scored skill is a different, larger number; don't quote this
  panel for it.
- **`BPReader` is bypassed** on both sides (`gen_appendixB_skill_cache.
  load_bp_anom` for `m_bpday`, `load_bpmon_anom` here for `m_bpmon`): the spread
  run's directory holds only `m_bpday` + `costfunction`, no `data.ecco`. Same
  workaround as `gen_appendixB_skill_cache` and `fig3_bp_std`. The 157 cable
  sensors come from `SENSOR_RUN_DIR` = the matching non-spread cable run, whose
  `gencost_datafile(1)` is a symlink into `/work` (purge-proof) and is the same
  static mask for both runs.
- The f/H contour is drawn from **raw** `f/H`, i.e. with `Depth = 0` on land
  giving `inf`, which is why the 1e-7 line also traces coastlines. That is how
  the published panel looks; masking land first removes those segments. Left
  alone deliberately.

# SI: skill over optimization iterations (`si_skill_over_optim`)

## 2026-08-13: new module backing the "standing pattern of amplification" claim

`sections/grace_equivalent_osse.tex` defends stopping the two annual OSSEs at 3
iterations by asserting that skill evolves as "a standing pattern of
amplification to first order (see Supplementary Information)". There was no
Supplementary Information. `si_skill_over_optim.py` is it: a port of Matt's
`bpskill_vmax_one_half_quarter` GIF frames (`smart_cables/osse/
lookat_skill_over_optim.ipynb`, cells 8-13) onto this package's conventions,
with row (a) = cost curve + raw skill maps at iterations 1/5/10/20 on one color
scale, and row (b) = the same maps each rescaled by its own amplitude
`m_i` (RMS skill over the SPNA window) to the final iteration's amplitude.
Writes `output/si_skill_over_optim.{png,pdf}`, 21 per-iteration frames + a GIF
under `output/si_skill_over_optim_frames/` (via `dinocean`'s `GIFmaker`, as the
notebook did), and the cache `data/si_skill_over_optim.nc`.

- **Run: `runc68v_froman_partialcables_jraspread/201201/fullnatl` (full SPNA
  cable, Jan 2012, 20 iterations).** Not a free choice -- it is the only OSSE
  on $SCRATCH that still has per-iteration `m_bpday`. Every other run,
  including the `jrastd` partial-cable set the notebook used (whose `subgyre/`
  is where the original GIF came from), has had its intermediate iterations'
  `.data` purged and only `.meta` remains; `selected_iters.tar.gz` and
  `smart_osse_data/*.tar.gz` don't contain them either. The only 24-iteration
  survivor, `..._gracellc4320_sc_may2026`, is degenerate (`m_bpday` identical
  to float32 across all 24 iterations, gencost exactly 0) -- do not use it.
  If those iterations are ever restored from Ranch/Pleiades, `--run-dir`
  points the script at them and the cache rebuilds in ~30 s.
- **The claim holds, but not via pattern correlation, and the figure says so.**
  Amplitude `m_i` grows monotonically 0.023 -> 0.228 (x10, no overshoot, no
  sign reversal). Sign agreement `f_i` with the iteration-20 map (over cells
  with |s_20| > 0.1) is already 0.88 at iteration 1 and 0.90 at iteration 3 --
  *where* assimilation helps or hurts is settled immediately, which is what
  "to first order" can defensibly mean. But the spatial correlation `rho_i`
  with the final map builds up gradually: 0.27 (1), 0.39 (3), 0.55 (5), 0.88
  (10), 0.95 (15). That is real, not tail noise -- it survives clipping at
  +/-0.5, restriction to |s_20| > 0.1, and a Spearman version (all within
  0.09). Successive iterations correlate at 0.98-0.99 throughout, i.e. the
  pattern never reorganizes; it keeps *extending*, the far field
  (Iceland-Scotland, Rockall, open gyre) filling in behind the near-cable
  maxima. Panel (b) plots `rho_i` and `f_i` together for exactly this reason.
  **If the SI text wants one number, use f_3 = 0.90, not rho_3 = 0.39.**
- `read_costfunction()` replaces `utils.grep_cost` here (left untouched for its
  other callers): the grep version shells out per term per file and `float()`s
  the result, so it raises the moment a term name matches more than one line
  and silently returns the wrong line when one term name is a substring of
  another. The Python parser reads each file once and returns every term, which
  is how the figure gets the gencost misfit next to `fc` for free (they differ
  by exactly `mult_gencost` = 1e14 here -- the control penalties are
  negligible, so plotting `fc` is plotting the OBP misfit).
- Skill definition is `osse._compute_skill`'s, unchanged; it is recomputed
  inline only so iteration 0 is loaded once instead of 20 times.
- `contourf` fills are rasterized per-collection (matplotlib 3.4's `ContourSet`
  is not an Artist, and `rasterized=` passed to `contourf` is silently
  dropped): 18 MB -> 0.8 MB PDF.

# Inverted-barometer control-frequency sweep (`inverted_barometer_ctrl_freqs`)

## 2026-08-12: ported out of the notebook into `fig_ib_ctrl_freqs.py`, two renderings

Ported `smart_cables/osse/lookat_ib_assim.ipynb` (cells 15/17/22) into the
package as `fig_ib_ctrl_freqs.py`, rendering the same numbers two ways at
Matt's request: the notebook's original line plot restyled onto the fig-9 /
appendix-B relcon greys, and a 100%-stacked-bar version showing the
contributions as the partition of unity they actually are. Four files in
`output/`: `inverted_barometer_ctrl_freqs.{png,pdf}` and
`inverted_barometer_ctrl_freqs_stacked.{png,pdf}`.

- **Data source is `adxx`, not `xx`.** The metric is
  `||adxx_c * weight_c**-0.5||_2` normalized across controls, so it reads the
  adjoint gradients; the `xx_*` control fields never enter it. This matters
  operationally because `xx_apressure` is 7.1 GB per frequency while the whole
  8-control `adxx` set is ~430 MB -- a run archive built with a `*xx*` glob
  comes out at 58 GB instead of ~450 MB. `tar_ib_adxx.sh` (new, this dir)
  stages exactly what's needed; it also fixes a `--transform` in the original
  archiving loop that was prepending `$d/iter0000/` to paths already rooted
  there, producing doubled `24hr/iter0000/24hr/iter0000/` nesting.
- **240 hr is excluded from `HOURS`.** That run survives only one adjoint
  record (nt=1) and its relcon is degenerate: uwind, vwind and apressure all
  come back *exactly* 0.0 with swdown taking 0.76. It is an empty data point,
  not a 10-day one. Dropping it leaves lags 1.0-4.0 d, which is the range the
  published figure already showed -- the notebook got there differently, by
  slicing `[:-2]` off a 24-120 hr sweep.
- **Record count falls with the adjustment interval** (nt = 8, 6, 5, 4, 4, 3,
  3 across the seven frequencies) since a fixed window holds fewer knots as
  they spread apart, so the time-mean averages fewer records at long lag.
  Inherited deliberately so the figure matches the published one -- this is
  the caveat the notebook flagged in its own cell-18 markdown.
  `load_relcon_sweep` returns `nrec` as a coord if it ever needs weighting.
- **Result** (`other` / `winds` / `patm` by lag in days): 1.0 -> .015/.342/.643;
  1.5 -> .021/.396/.583; 2.0 -> .026/.414/.560; 2.5 -> .031/.567/.403;
  3.0 -> .026/.438/.536; 3.5 -> .048/.765/.186; 4.0 -> .050/.755/.195. Note
  the non-monotonic bump at 3.0 d (patm recovers to .54 from .40 at 2.5 d)
  -- present in both renderings, not a plotting artifact.
- **Greys** come from `_shade_color(RELCON_BAR_GREY, REGION_SHADE_FACTORS[g])`,
  i.e. appendix B's neutral `'0.55'` run through fig 9's shade factors, so
  'other' is lightest and patm darkest. Imported from those modules rather
  than re-derived -- don't hand-pick replacements here. The line variant adds
  per-series dash patterns (`LINE_STYLES`) because three greys alone are thin
  encoding at print size, and outlines its markers (`markeredgecolor='0.25'`)
  so the light 'other' fill still reads.
- Cached to `data/ib_ctrl_freqs.nc`; `load_relcon_sweep(use_cache=False)` to
  recompute from scratch.
- **Open question for Matt**: which rendering goes in the manuscript. The
  stacked version makes the winds/patm crossover a single moving boundary and
  is the better argument-carrier; the line version shows absolute levels and
  matches what's already published.

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

## Update 2026-08-01 (latest): recolored (silver land / blue ASTE ocean / white elsewhere), global-panel legend removed

Matt's styling pass on `fig1_global_cables.py`. The previous scheme (white
land, `#cccccc` ASTE ocean, `#f5f5f5` non-ASTE ocean) was a prior session's
own judgment call, flagged for review in the 2026-07-14 entry below -- now
superseded:

- **Land -> `silver`** on both panels (`LAND_COLOR` `'#ffffff'` ->
  `'silver'`), i.e. `region_cartopy`/`spna`'s own default `landfacecolor`
  (`smartosse/plot.py`), so Fig. 1's land matches every other map figure in
  the package rather than being a per-figure override.
- **ASTE-domain ocean -> `#7fb9da`** (`Blues` at 0.45), after two rounds of
  Matt's review: `#6baed6` (0.5, picked by sampling Fig. 2's PNG) -> `#4a98c9`
  (0.6, "slightly darker") -> `#7fb9da` (0.45, "paler"). Dial it with the one
  constant; the `Blues` ladder is 0.4 `#94c4df` / 0.45 `#7fb9da` / 0.5
  `#6aaed6` / 0.55 `#5ba3d0` / 0.6 `#4a98c9`. (The Fig. 2 sampling wasn't
  wasted -- it also showed Fig. 2's land is `(192,192,192)` = `silver`,
  independently confirming the land choice above -- but Matt clarified he
  meant "blue" generally, not a Fig. 2 match.) The SPNA inset uses the same
  blue (`OCEAN_COLOR` aliases `ASTE_OCEAN_COLOR`); it lies entirely inside ASTE.
- **Thin black outline on the inset's partial-cable markers**, new
  `PARTIAL_EDGE_COLOR`/`PARTIAL_EDGE_LW = 'k'/0.5`, applied to both the
  `scatter` (`edgecolors`/`linewidths`) and the legend key
  (`markeredgecolor`/`markeredgewidth`) so the two can't drift. Matters most
  for `LS_cable`, whose blue would otherwise sit on the blue ocean.
- **The inset was already pure cartopy** -- `spna()`'s NaturalEarthFeature
  land + `cf.OCEAN`, no `ds.plotpc`/model data anywhere in it (checked when
  Matt raised it). Only the *global* panel's ASTE-domain fill touches model
  data, and it can't not: the domain shape comes from `hFacC` via
  `llc_map.regrid` (cartopy has no notion of where ASTE ends). That fill
  bypasses `ds.plotpc` too -- see `plot_aste_domain` and the 2026-07-14
  entry below for why.
- **Real cartopy bug found and fixed: white speckles along the inset's
  coastlines.** Matt reported them and correctly noted they shouldn't happen
  from plain cartopy fills. They were genuine holes -- pixels with **alpha
  exactly 0** (checked in the PNG, so nothing was drawn there; not an
  antialiasing blend, which would give intermediate alpha, and not something
  painting white).
  - **Cause: land and ocean were being drawn at different Natural Earth
    scales.** `region_cartopy` hardcodes land at `scale='110m'`, while the
    inset's ocean came from `cf.OCEAN`. The two datasets are exactly
    complementary only *within* a scale, so a 110m land polygon over a 50m
    ocean polygon leaves uncovered slivers wherever the coastline is
    convoluted (Canadian archipelago, fjords) -- which is precisely where the
    speckles were.
  - **`cf.OCEAN.scale` reports `'110m'` and is a plain `str`, which is
    misleading** -- cartopy 0.22 resolves module-level features' scale at
    draw time from the axes extent. Caught by A/B render, not by reading the
    attribute: `cf.OCEAN` produced a transparent-pixel count *identical* to an
    explicit `'50m'` ocean (88030) and different from explicit `'110m'`
    (85050). Don't trust `.scale` on `cf.LAND`/`cf.OCEAN`; pass an explicit
    `NaturalEarthFeature`.
  - **Fix**: explicit, per-panel matched scales -- new `GLOBAL_FEATURE_SCALE
    = '110m'` / `INSET_FEATURE_SCALE = '50m'`, with both panels' land *and*
    ocean built as explicit `NaturalEarthFeature`s. The inset now passes
    `show_land=False` to `spna()` and draws its own land at 110m's place in
    region_cartopy's zorder stack (ocean 0, land 1, below the gridlines' 2),
    so nothing else about the `spna()` view changes. **Side effect worth
    knowing**: the inset's coastlines are now 50m, i.e. visibly finer than
    before -- deliberate (better at that zoom), and revertible by setting
    `INSET_FEATURE_SCALE = '110m'`.
  - Measured, not eyeballed: holes in a coastal window went 1416 -> **0**,
    and every matched-scale combination (110/110, 50/50) gave 0 while only
    the mismatched one was nonzero. Re-measured on the real figure after the
    fix: 0 in both variants. Ocean also keeps `edgecolor='face'` (cf.OCEAN's
    own default, which the first pass had overridden to `'none'`) -- it
    stitches the subpixel antialiasing seam that remains once the geometry
    matches; `'face'` on the *land* is worse, since its dashed `linestyle`
    makes the stroke intermittent.
- **Non-ASTE ocean -> white** (`NONASTE_OCEAN_COLOR` `'#f5f5f5'` ->
  `'#ffffff'`), so the domain reads as the figure's subject. Land/ocean
  zorder is unchanged (ocean 0 -> ASTE patch ~0.5 -> outline ~0.6 -> land 1
  -> cable dots 2/3 -> SPNA box 10); checked in the render that the `dimgray`
  representative dots stay legible against both silver land and the blue
  patch, which was the risk in dropping white land.
- **Global panel's Representative/Funded legend removed entirely** --
  `plot_global_panel`'s `legend`/`legend_kwargs` params and the `Line2D`
  proxy block are gone, not just defaulted off (its only caller is
  `make_fig1`). `LEGEND_FONTSIZE` survives, now driving the inset's region
  legend alone.
- **Comments/docstrings compressed throughout** at Matt's request -- the long
  explanatory blocks (module docstring, `plot_aste_domain`'s bypass-`plotpc`
  rationale, the legend-tuning writeups) are cut to the operative facts. No
  behavior tied to them changed. Unused `matplotlib.patches` import dropped.
- Verified by a real end-to-end render (`module load texlive`, `esmpy_3.10`,
  `python -m smartosse.figures.fig1_global_cables`), not by inspection --
  output visually checked at full resolution, and PDF font embedding
  re-checked with the project's standard `grep -a -o '/Subtype
  */Type[0-9C]*\|/FontFile[0-9]*'` recipe: real embedded Type 1 (`/FontFile`
  present). Current render: `figures/output/fig1_global_cables.png`/`.pdf`.
- **Both standing variants re-rendered** at the new colors:
  `figures/output/fig1_global_cables.png`/`.pdf` (single-line, the default)
  and `figures/output/fig1_global_cables_multiline_legend.png`/`.pdf`
  (`make_fig1(legend_multiline=True)`). The multiline legend's box height is
  still matched to the inset's after the recolor (nothing this pass touched
  `INSET_MULTILINE_LEGEND_LABELSPACING` or the fontsize), confirmed in the
  render; its PDF fonts check out the same way.

## Update 2026-07-14: multiline legend height-matched to the inset, fontsize bumped on both legends

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

## Update 2026-08-11 (night, LATEST): Appendix B figure FINISHED — SPG's real
## iter0020 is in, panel (c)'s two legends stacked, all four of Matt's asks done

`xxsubgyre20.tar.gz` landed SPG's genuine `xx_*`/`adxx_*` at iter0020 (files
15:31). `valid_gradient_regions()` now passes it — its `adxx_apressure` /
`adxx_uwind` / `adxx_vwind` are no longer identically zero — so
`STD_EXCLUDE_REGIONS = ()` and **all four cables appear in (b), (c) and (d)**.
SPG's forward output (`m_bpday`, 13:24) was untouched by that transfer, so the
15:44 skill cache is current and (d) did not need recomputing.

Matt's four asks from this round, all done and all verified in the render:

1. **(c) all bars one grey** (`RELCON_BAR_GREY = '0.55'`) — cable identity is
   already on the x tick labels, which frees the light/mid/dark ramp to mean
   only other / winds / p_atm.
2. **(c) legends bigger, inside the headroom above y=1** — `RELCON_YLIM_TOP =
   1.75`, fontsize 16 / title 17. The constants for this were added last session
   but **never wired in**: the body still anchored the two legends
   `lower left @ (0.13, bar_top)` and `lower right @ (1.0, bar_top)`, i.e. side
   by side, and at fontsize 16 they were jointly wider than the axes — "winds"
   ran through the STD swatch in the 15:46 render. Now both anchor at
   `RELCON_LEGEND_X = 0.24`, with the shade key `RELCON_LEGEND_DY = 0.185`
   above the hatch key, both `loc='lower left'`. Stacking spends headroom (free)
   instead of font size (the thing asked for). This is the first time (c)'s
   legend placement has been checked against a real render.
3. **(b) subscript is `i,j`, not a bold x** — `fig9_spread_3panel.RATIO_YLABEL`,
   so Fig. 9b and Appendix B (b) stay in sync and both use the index letters the
   paper introduces earlier.
4. **(d) widened to `SCATTER_LIM = (-0.7, 0.7)`** — the "(d)" letter and the two
   RMS lines no longer crowd. Still clips almost nothing: outside-view 0.02%
   (p_b) / 0.40% (V_bt), and the annotated RMS is computed on all points anyway.

Two further asks, same session, also done and re-rendered:

5. **(b) legend moved from upper right to upper LEFT** — `RATIO_LEGEND_X = 0.13`
   rather than flush at 0.0, because the "(b)" panel letter is fontsize 40 at
   x=0.02 and a flush-left legend runs through it. The left half of the top
   strip is the emptier one anyway: the curves' tall excursions (NS 5.0, LS 4.3)
   are all in the last three days of January.
6. **(d) RMS folded into the legend entries** — `plot_skill_scatter(...,
   rms_in_legend=True)`, now the default, labels the swatches
   "$p_b$: RMS = 0.055" / "$V_{bt}$: RMS = 0.061" and drops the separate
   top-left annotation, so each field name appears once instead of twice. The
   old split layout is still reachable with `rms_in_legend=False,
   annotate=True`.

Final numbers, four cables:

    (b) max |dp_atm|/sigma   LS  med 0.59 max 4.31, >1sigma 16% of days
                             SPG med 0.43 max 2.99 ... 13%
                             NS  med 0.93 max 5.01 ... 48%
                             Nfl med 1.34 max 3.59 ... 74%
    (c) relcon p_atm  STD    0.961 / 0.964 / 0.967 / 0.965  (LS/SPG/NS/Nfl)
                      SPREAD 0.624 / 0.549 / 0.492 / 0.644
    (d) p_b  n=161840  rms(std-spread)=0.0547  median diff +0.0132
        V_bt n=166332  rms(std-spread)=0.0614  median diff +0.0055

SPG slots in where expected on every panel — relcon p_atm 0.55 -> 0.96 like the
other three, ratio curve the quietest of the four — so nothing about the earlier
three-cable reading changes.

Render: `figures/output/figB_patm_std_4panel.{png,pdf}`, 7x `/FontFile` +
7x `/Subtype /Type1` (real embedded fonts), 676 KB.

### Fig. 9 itself regenerated, for the `i,j` subscript only

`RATIO_YLABEL` is **shared** between `fig9_spread_3panel` and Appendix B's
panel (b) — deliberately, since the two panels are meant to be flipped between —
so editing it left Fig. 9's saved render (Jul 22) stale and disagreeing with
Appendix B. Re-ran `python -m smartosse.figures.fig9_spread_3panel`; no code
change was needed or made, and nothing else about the figure moved (its (b)
legend stays upper right, ylim 0-1.7, 3x2 handle order). New
`figures/fig9_spread_3panel_test.{png,pdf}` — the one `controls.tex:22`
includes — 7x `/FontFile` + 7x `/Subtype /Type1`, 1.5 MB. The two figures'
(b) axis labels now match character for character.

**Trap, hit immediately after this render:** there are TWO
`fig9_spread_3panel_test.png` on disk. `__main__` writes it **next to the
module** (`figures/`), because that is where `tex/figures ->` points and so
where `controls.tex:22` resolves it; `figures/output/` also held a copy, left
there Jul 22 and never regenerated since. Matt opened the `output/` one and
reasonably read it as "the i,j change didn't take" — it is in fact
*pre-redesign*: panel (b) still the +/-sigma envelope in hPa rather than the
normalized whole-domain max, panel (c) still the per-cable colours. Both copies
are now the 22:22 render. If they diverge again, `figures/` is the canonical
one; `output/` is a convenience mirror that nothing compiles from. (Every other
figure here writes to `output/` — fig9 is the exception, and that asymmetry is
what makes this easy to trip over.)

**Still open, unchanged by this session:** Appendix B's *text*
(`sections/appendix.tex`) is still the old spread-based version with the
inverted causality, and the figure is not `\input` anywhere. The text must not
overreach from (d) to the gateways — see "The tension this figure now has to be
read against" below.

## Update 2026-08-11 (evening): gradients arrived — ALL FOUR PANELS of
## Appendix B now carry real data; SPG held out; panel (b) ylim had to change

`xx.tar.gz` (extracted 14:37) delivered `adxx_*` and `xx_apressure.effective`
for every region. Panels (b) and (c) are built. Current render:
`figures/output/figB_patm_std_4panel.{png,pdf}` (8x `/FontFile`, 8x
`/Subtype /Type1`).

### SPG is held out of the std side of (b), (c) and (d)

`subgyre/iter0020`'s `adxx_apressure`, `adxx_uwind` and `adxx_vwind` are
**identically zero** over all 4 691 648 elements, and its other gradients are ~8
orders of magnitude below the other cables' (`adxx_atemp` absmax 1.2e-01 vs
1.7e+08 for labsea). Its *forward* output is NOT degenerate — `m_bpday` and
`trsp_3d_set1` both differ between iter0000 and iter0020 — so this is an adjoint
/ archiving problem, not a failed solve. Matt confirmed the iter0020 is not
final and will re-send it.

Held out via `STD_EXCLUDE_REGIONS = ('subgyre',)`; empty that tuple and run
`gen_appendixB_skill_cache --regions subgyre --runs std` when the run lands.
The std/subgyre entry in `data/appendixB_skill_maps.nc` was explicitly set to
NaN (with a `subgyre_std_note` attribute recording why), because the cache
merges with `combine_first` — recomputing the other three would otherwise have
left the stale subgyre values in place.

**Why a zero gradient could not be left to fall through.** `ControlDataset`
forms `std_cost = sum((adxx*unc)^2)^0.5` and then normalizes by its sum over
controls. Zero p_atm and wind gradients therefore do not blank those bars —
they renormalize the *remaining* controls to 1.0, and SPG plotted as a
confident, entirely wrong `other = 1.00` bar. That is worse than a gap, hence
`valid_gradient_regions()` tests the array contents, not file presence.

### Correction carried out: (c) needs `adxx_*`, and a NEW data.ctrl dir

Confirmed against `smartuq/ctrl.py`: `ControlDataset` reads
`ad{ctrl}{ext}.{iter}.data` with `ext=''` — the plain `adxx_*` gradients, not
`xx_*`, not `.effective`. The control list and weight filenames come from
`data_ctrl_dir`/`weight_dir`, so the run's own `data.ctrl` is never opened.

The standing `data_ctrl_dir_std/data.ctrl` is a **symlink into the live run
template** (`input_weight/data.ctrl_jrastd`) and still names the sub-daily
`wApressure_ASTE270_EXFpress_std_new.bin`. It was NOT edited — repointing a file
that runs are launched from, in order to serve a figure, is the wrong trade.
Instead `input_weight/data_ctrl_dir_std_daytoday/` holds a real copy differing
in exactly one line (`xx_gentim2d_weight(8)` ->
`wApressure_jra2012_daytoday_std_Pa.bin`), verified by `grep_ctrl` to give 8
controls <-> 8 correctly paired weights. `figB` uses it via
`DATA_CTRL_DIR_STD_DAYTODAY`.

### Panel (b): the shared-ylim design had to be abandoned, and that IS the result

The plan was ylim identical to Fig. 9b (0-1.7) so the eye compares without a
key. Not tenable — whole-domain max |dp_atm|/sigma under the day-to-day prior:

    LS   min 0.05  med 0.59  max 4.31   above 1 sigma on 16% of days
    NS   min 0.21  med 0.93  max 5.01   ... 48%
    Nfl  min 0.18  med 1.34  max 3.59   ... 74%

against the spread prior, where **no cable exceeds 1.00 on any day** (maxima
1.00 / 0.54 / 0.59 / 0.49). Clipping at 1.7 ran three curves off the top for a
quarter of January. Now `RATIO_YLIM_STD = (0, 5.3)`, yticks 0-5, 1-sigma line
and shading kept — so the cross-figure comparison survives in the stronger form
"Fig. 9b lives entirely inside the grey band; this panel does not".

### Panel (c): the redistribution is dramatic, and arithmetically expected

    STD     LS  patm 0.961  winds 0.007  other 0.032
            NS  patm 0.967  winds 0.002  other 0.031
            Nfl patm 0.965  winds 0.004  other 0.031
    SPREAD  LS  patm 0.624  winds 0.288  other 0.088
            NS  patm 0.492  winds 0.442  other 0.066
            Nfl patm 0.644  winds 0.311  other 0.045

0.96 looked implausible on sight, so it was checked rather than shipped:
`std_cost` scales with `unc = sigma`, and sigma_patm^std is ~15x sigma_patm^spread
at the sensors, so LS's spread ratio patm/winds = 0.624/0.288 = 2.17 should
become ~32 and a share of ~0.97. It does. The panel's claim ("re-weighting
p_atm redistributes attribution between wind and pressure") is carried
emphatically.

Legend fix: at fontsize 14 / handlelength 1.4 the two above-axes legends were
jointly wider than the axes and visibly overlapped ("winds" ran into the STD
swatch). Now 11.5 / 1.1 with tighter columnspacing. The SPG-omitted note sits in
the `RELCON_YLIM_TOP` headroom band (bar tops are at 0.85 in axes fraction), not
in the axes interior where a first attempt overlapped the NS bars.

### Panel (d): back to three cables

With SPG held out: p_b rms(std-spread) = 0.0605, V_bt = 0.0677, median diff
+0.0148 / +0.0074 — the three-cable numbers, recovered exactly after a full
recompute of the std side against the current run directory. The reading is
unchanged: the two OSSEs' skill fields agree to ~0.06 RMS against a
point-to-point spread of ~[-0.5, +0.4], with the std OSSE very slightly better.

### The tension this figure now has to be read against

Panels (b) and (c) say the day-to-day prior changes the *assimilation* a great
deal (p_atm relcon 0.5-0.6 -> 0.96, adjustments from <1 sigma to 3-5 sigma),
while (d) says the *p_b and V_bt skill fields* barely move. Both are true, and
the gateway table (see the 2026-08-11 session at the head of
`DavisStrait_fw_decompisition_plan.md`) sits in between: Davis Strait's mean
bias reduction falls 40.1% -> 28.1%. "The QoIs change negligibly" is defensible
for the gridded skill fields and **not** defensible for the gateway means —
Appendix B's text must not overreach from (d) to the gateways.

## Update 2026-08-11 (later): subgyre landed — panel (d) is now all four
## cables; (b) and (c) are STILL blocked, and the blocker is `adxx_*`, not `xx_*`

Matt's expectation was that the newest transfer completed everything panels (b)
and (c) need. It did not. What it *did* complete is real and worth having, and
panel (d) — the panel that carries the appendix's actual claim — is now final.

### What arrived since the entry below

- **`subgyre/` now exists** under `RUN_DIR_ROOT_STD`, extracted 2026-08-11 13:53
  from `subgyre.tar.gz`. It is **genuinely distinct** from `northsea/` this time
  (`m_bpday` iter0020 md5 `d6646aef…` vs `6780c91f…`), so the duplicated-run
  defect flagged on 2026-08-06 (§2) is fixed. All four cables + fullnatl are
  present at iter0000 and iter0020.
- **`labsea/*/diags/state_3d_set1/` now exists** (from `labsea_state3d.tar.gz`,
  extracted 14:02), 32 daily files at each of iter0000/iter0020, `fldList =
  {THETA, SALT}`. **This unblocks ADV_fw for the std_daytoday run** — i.e. the
  2026-08-06 §3 blocker on `gates_corrected.py jrastd_daytoday` is gone. Still
  needs `gen_gate_caches.py` to write the FM cache first.

### What did NOT arrive — and the correction to what we were asking for

No `xx_*`, no `adxx_*`, no `data.ctrl`, no `data.ecco`, anywhere under
`runc68v_froman_partialcables_jrastd_daytoday/`. Verified two ways: `find` over
the extracted tree, and `tar tzf | grep` over **all three** tarballs
(`selected_iters.tar.gz`, `subgyre.tar.gz`, `labsea_state3d.tar.gz`) — zero hits
in any of them. So (b) and (c) are unchanged from the entry below.

**Correction to the earlier ask.** The 2026-08-11 entry below (and the
placeholder text, and `has_control_set()`) said panel (c) needs "the `xx_*`
control set plus a `data.ctrl`". Both halves are wrong, and it matters because
it was the list being sent to the other machine:

- `smartuq.ctrl.ControlDataset._load_dataset` reads
  `f'{run_dir}/ad{ctrl}{ext}.{iter:010d}.data'` with `ext=''` — i.e. the plain
  **`adxx_*` adjoint gradients**, not `xx_*`, and not the `.effective` variants.
- It reads `data.ctrl` and the weight filenames from `data_ctrl_dir` /
  `weight_dir`, which `load_relcon_grouped` passes explicitly
  (`DATA_CTRL_DIR_STD`, `WEIGHT_DIR` — both local to this machine). The run's
  **own `data.ctrl` is never opened**, so its absence does not block (c).

`has_control_set()` was probing `data.ctrl` + `xx_uwind.effective`; it now probes
`adxx_{uwind,vwind,apressure}.{iter:010d}.data`. As written before, it would have
kept reporting (c) unbuildable even after the right files arrived.

**Exact transfer list to unblock (b) and (c)**, per region
(labsea/subgyre/northsea/newfoundland), from `iter0020/`:

    xx_apressure.effective.0000000020.data      # (b)   ~46 MB x 4 =  184 MB
    adxx_{apressure,aqh,atemp,lwdown,precip,swdown,uwind,vwind}.0000000020.data
                                               # (c)  ~368 MB x 4 = 1.5 GB

(Sizes from the superseded `BADrunc68v_.../labsea/iter0020/`, which still has the
full set locally and is the right template for what the file names look like.)

### Panel (d) rebuilt on four cables

`gen_appendixB_skill_cache --regions subgyre --runs std` (~4 min) filled the one
NaN slot; the cache is now finite for all 2 runs x 4 regions x 2 fields
(300549 p_b / 304733 V_bt points per experiment). Re-rendered figure:

    p_b    n=161840  rms(std-spread)=0.0547  median spread=+0.0177  median std=+0.0321  median diff=+0.0132  outside view=0.06%
    V_bt   n=166332  rms(std-spread)=0.0614  median spread=+0.0000  median std=+0.0054  median diff=+0.0055  outside view=0.57%

Against the three-cable version (p_b 0.0605, V_bt 0.0677) the RMS deviation from
the 1:1 line **fell slightly** with SPG added, and the small positive median
offset survives — so the reading is unchanged and, if anything, firmer: the two
OSSEs' skill fields agree to ~0.055-0.061 RMS against a point-to-point spread of
roughly [-0.5, +0.4], with the std OSSE very slightly the better of the two.
Sanity check on the pooling: the point counts scale *exactly* with the cable
count (p_b 161840/4 = 40460 = 121380/3; V_bt 166332/4 = 41583 = 124749/3), which
is what you want — every cable contributes the same SPNA mask, so SPG was added
cleanly and nothing was dropped or double-counted.

`SCATTER_LIM = (-0.6, 0.6)` still leaves <1% outside the view (0.06% / 0.57%), so
it was not retuned. PDF re-checked with the project's grep recipe: 7 x
`/FontFile` + 7 x `/Subtype /Type1`, real embedded fonts, 679 KB.

### Still open (unchanged)

- (b)/(c) await the transfer list above. Everything else about them is done —
  the rebuild after the files land is one command, no edits.
- `data_ctrl_dir_std/data.ctrl:66` still reads
  `wApressure_ASTE270_EXFpress_std_new.bin`. Repoint at
  `wApressure_jra2012_daytoday_std_Pa.bin` before trusting (c)'s STD bars.
- (c)'s two-legends-above-the-axes placement has still never rendered with real
  bars — first guess, check it on the rebuild.
- Appendix B's *text* (`sections/appendix.tex`) untouched, still the old
  spread-based version with the inverted causality.

## Update 2026-08-11 (earlier): Appendix B figure built — (a) and (d) render from
## real data, (b) and (c) are blocked on control files the rerun didn't ship

The 4-panel Appendix B figure specified in the 2026-08-06 entry below now exists
as code and renders end-to-end. Two of its four panels carry real data; the
other two are annotated placeholders because of what the reruns contain, not
because of anything unfinished in the code. Matt asked for the preliminary
render anyway ("build what you can, we will rebuild again when subgyre is
back"), and confirmed the reruns used the **Pa-corrected** weight file.

### What landed on disk (and what didn't)

`runc68v_froman_partialcables_jrastd_daytoday/201201/` was repopulated
2026-08-11 12:06-12:43 from `selected_iters.tar.gz` (11.8 GB -> 48 GB, 4 dirs x
280 files, extraction complete); the run output inside is dated 2026-08-08, so
these are the corrected-weight reruns. They contain, per iteration directory,
**only** `adm_bpday` / `bpdatanom_*` / `bpdifanom_*` / `m_bpday` and
`diags/{state_2d_set1, trsp_3d_set1}`. Checked by `find` over the whole tree:

- **No `xx_*.effective`, no `adxx_*`, no `data.ctrl`, no `data.ecco`** anywhere
  under that root. The spread runs have all of them. This is what blocks panels
  (b) (needs `xx_apressure.effective.*.data`) and (c) (needs the whole `xx_*`
  set plus a `data.ctrl`, through `smartuq.ctrl.ControlDataset`).
- **`subgyre/` is still absent** — the set is fullnatl / labsea / newfoundland /
  northsea. So (b)/(c)/(d) cover three cables (LS/NS/Nfl), not four. Panel (a)
  still shows all four cables' sensor dots: those come from the synthetic-obs
  binaries in `input_ecco/smart_phibot/`, not from a run.
- **Still no `state_3d_set1`**, so no salinity and no ADV_fw, including for
  labsea. Doesn't affect the figure (ADV_fw was already text-only per the
  2026-08-06 plan), but the labsea salinity output that was requested isn't in
  this transfer either.
- `data_ctrl_dir_std/data.ctrl:66` **still reads
  `wApressure_ASTE270_EXFpress_std_new.bin`** — the sub-daily std file, not the
  day-to-day one. Unchanged since it was flagged on 2026-08-06, and it is now
  load-bearing: it sets the sigma panel (c)'s STD bars are weighted against.
  Repoint it at `wApressure_jra2012_daytoday_std_Pa.bin` before trusting (c).

### New files

- **`figB_patm_std_4panel.py`** — the figure. All four panels are fully
  implemented; `make_figB(..., skip_unavailable=True)` (the default) draws (b)
  and (c) as dashed, annotated placeholder boxes when their inputs are missing,
  so the preliminary render still shows the final layout and says on the figure
  why the boxes are empty. `skip_unavailable=False` raises instead. Availability
  is probed by `has_patm_adjustment()` / `has_control_set()`, and `regions` is
  intersected with what the std run set actually contains, so SPG drops out of
  (b)/(c)/(d) automatically and reappears the moment its directory exists — the
  rebuild is one command, no edits.
- **`gen_appendixB_skill_cache.py`** — precomputes panel (d)'s skill maps into
  `data/appendixB_skill_maps.nc` (dims `(run, region, tile, j, i)`, variables
  `skill_bp` / `skill_Vbt`). ~12 min for the full 2 runs x 4 cables x 2 fields
  sweep, dominated by `trsp_3d_set1` reads (~80 s per V_bt, ~25 s per p_b).
  Writes are **merged** with whatever is already cached (`combine_first`), so
  `--regions subgyre` later fills SPG in without recomputing the rest.
- `data/appendixB_skill_maps.nc` — the cache itself (~57 MB), currently NaN for
  every `std`/`subgyre` entry.

### Two deliberate departures, both forced by the data

- **p_b is loaded without `BPReader`.** `ForecastModel._load_fm_bp` constructs
  one, and `BPReader.__post_init__` unconditionally calls `read_weight()`, which
  needs a `data.ecco` the std reruns don't have — it raises `FileNotFoundError`
  before any field is read. The weight feeds only the cost diagnostics, which
  skill never touches, so `gen_appendixB_skill_cache.load_bp_anom()` reproduces
  the two lines of `_load_fm_bp` that matter (`m_bpday` -> `100/9.81 * (x -
  x.mean('time'))`) and skips the reader. Same shape of workaround, for the same
  reason, as `fig3_bp_std.load_cable_sensor_lonlat()`; `bp.py` deliberately left
  alone rather than made tolerant, since other callers rely on the cost path.
- **`V_bt` is the meridional component, and skill is at iteration 20.**
  Meridional because that is what manuscript Fig. 5 plots ("zonal ... not shown
  but are quantitatively comparable") — `OSSE.toggle_uv('V')`, i.e. `fldUV[1]`
  out of `UEVNfromUXVY`. Iteration 20 because it is the only non-zero iteration
  the std reruns contain, and it matches Fig. 9's own `iternum=20`; **Fig. 5 is
  iteration 10**, so panel (d)'s numbers are not directly comparable to it.
  Both axes of (d) use iteration 20, so the panel is internally consistent.

### Panel (d), the actual preliminary result

x = skill in the spread OSSE, y = skill in the std OSSE, one point per SPNA grid
cell (`plot.spna()`'s own window, lon [-80, 10], lat [40, 80]) per cable, three
cables pooled, 1:1 line, RMS deviation from it annotated:

    p_b    n=121380  rms(std-spread)=0.0605  median spread=+0.0207  median std=+0.0373
    V_bt   n=124749  rms(std-spread)=0.0677  median spread=+0.0000  median std=+0.0055

i.e. the two OSSEs' skill fields sit on the diagonal to within ~0.06 RMS, with
correlations of 0.895 (p_b) and 0.911 (V_bt), against a point-to-point skill
spread of roughly [-0.5, +0.4]. **The std OSSE is very slightly the better one**
(median difference +0.015 p_b, +0.007 V_bt) — worth stating in that direction
rather than as "no difference", since it is a small consistent offset, not
noise. This is the quantitative backing for the "QoIs change negligibly"
sentence, and it does not depend on either blocked panel.

`SCATTER_LIM = (-0.6, 0.6)` was picked from the distribution, not guessed: the
1st-99th percentiles are about [-0.5, +0.4] for both fields, and that window
leaves 0.07% (p_b) / 0.76% (V_bt) of points outside the view. The annotated RMS
is computed on every point, clipped or not, and `skill_scatter_summary()` prints
the outside-view fraction alongside it.

### Layout notes

- 2x2 gridspec, `figsize=(15, 12)`, `hspace=0.22` / `wspace=0.28`. (a) is a
  cartopy axes at its projection's own aspect and so cannot fill its cell
  horizontally; `set_aspect('auto')` (the fig7 fix) was deliberately **not**
  applied here, because unlike fig7's cells this one isn't sized to the map, so
  'auto' would visibly stretch the Lambert projection. The row gap was tightened
  instead.
- (a) reuses `plot_sigma_patm_map` with `levels=linspace(0, 20, 11)`, ticks
  `[0, 10, 20]` — an order of magnitude above Fig. 9a's 0-2, which is the point
  of the panel. SPNA-window values are 1.8-22 hPa, median 9.5.
- (c)'s two legends sit **above** the axes (shade key lower-left, hatch key
  lower-right) rather than in the right margin as in Fig. 9 — in a 2x2 the right
  margin of (c) is the narrow inter-column gap and would collide with (d). Its
  bars also get `ylim (0, 1.18)` headroom (yticks still 0/0.5/1) so the panel
  letter has blank space to sit in. **Unverified**: (c) has never rendered with
  real bars, so treat that placement as a first guess to check on the rebuild.
- Verified end-to-end (real render, `module load texlive` + `esmpy_3.10`), not
  by inspection. PDF font embedding checked with the project's standard `grep -a
  -o '/Subtype */Type[0-9C]*\|/FontFile[0-9]*'` recipe: 7 x `/FontFile` + 7 x
  `/Subtype /Type1`, real embedded fonts. The scatter is `rasterized=True`, so
  the PDF is 675 KB despite ~250k points. Current render:
  `figures/output/figB_patm_std_4panel.png`/`.pdf`.

### Next steps

- **Needs from the other machine**: the `xx_*.effective` control set +
  `data.ctrl`/`data.ecco` for all std regions, and the `subgyre/` run. With
  those in place the rebuild is `python -m
  smartosse.figures.gen_appendixB_skill_cache --regions subgyre` followed by
  `python -m smartosse.figures.figB_patm_std_4panel`.
- Repoint `data_ctrl_dir_std/data.ctrl:66` at the `_Pa` weight before (c) is
  trusted (see above).
- Not wired into the manuscript. `sections/appendix.tex`'s Appendix B is still
  the *old* spread-based "Atmospheric pressure uncertainty" text + the
  `patm_delta_vs_sigma.png` figure; swapping in this figure means rewriting that
  section, which also has to fix the causality error flagged on 2026-08-06.
- `figB_patm_std_4panel.py` / `gen_appendixB_skill_cache.py` untracked in git,
  like the other per-figure modules here.

## Update 2026-08-06: Appendix B rerun — unit bug in the day-to-day-std
## weight file, a duplicated std run, and the planned Appendix B figure

**Read this before rebuilding Appendix B or re-running anything under
`runc68v_froman_partialcables_jrastd_daytoday/`.** Two defects in the existing
std-prior run set were found while checking whether an Appendix B twin of
Fig. 9 would work. Both invalidate parts of the drafted Appendix B text.

### 1. `wApressure_jra2012_daytoday_std.bin` was written in hPa, model wants Pa

The file stores `w = sigma_hPa^-2`. MITgcm's `xx_apressure` control is in Pa,
so every `jrastd_daytoday` OSSE ran with an effective sigma_patm of ~8.5 Pa
(0.085 hPa) -- **100x tighter** than the intended ~8.5 hPa day-to-day std, and
~40x tighter than the spread prior (ASTE median 3.4 hPa) rather than ~2.7x
looser. Decoding the .bin as `w^-1/2` gives min 0.465 / med 9.12 / max 19.53,
against the independently computed day-to-day std in
`data/sigma_patm_std_2012_daytoday.nc` of min 0.462 / med 5.03 / max 21.96
**hPa** -- the min agrees to three decimals. (Medians differ by design: the
.bin is ASTE-only/high-latitude, the .nc is global.) The other two weight
files in that directory are unambiguously Pa-based (`w^-1/2` mean 164 Pa and
1448 Pa).

Confirmed against what the runs actually did -- max |dp_atm| over the domain,
iter 20: std runs LS 0.015 / SPG 0.035 / NS 0.035 / Nfl 0.006 hPa, vs spread
runs LS 2.66 / SPG 0.83 / NS 0.43 / Nfl 0.91 hPa.

**This inverts the drafted Appendix B causality.** "Under this larger
uncertainty, OSSEs attain down-weighted p_atm adjustments" gets the observed
direction right but the mechanism backwards: with a genuinely larger sigma the
p_atm control is *cheaper*, so adjustments grow and p_atm's relcon share
rises. The observed drop (p_atm 0.49-0.64 -> 0.37-0.49, wind taking up the
slack) is the signature of a much *tighter* prior.

**Fix shipped**: `gen_patm_daytoday_weight_Pa.py` writes
`wApressure_jra2012_daytoday_std_Pa.bin` next to the original (`w_new = w_old
* 1e-4`, applied to the raw `>f4` stream so the ASTE compact layout is
byte-identical apart from the scaling; zeros/land mask untouched, max relative
error 0.0). Verified: sigma_new = 46.5-1953 Pa (med 9.1 hPa) against the .nc's
46.2-2196 Pa; at the cable sensors it gives LS 10.7 / SPG 9.1 / NS 15.9 /
Nfl 7.4 hPa against the .nc's 14.6 / 14.3 / 15.6 / 6.3 hPa at the same
lon/lats -- same order and same across-cable ordering (NS largest, Nfl
smallest), residual differences attributable to the EXF regrid onto ASTE and
nearest-neighbour sampling. That is ~15x the spread prior at the same sensors
(0.57-0.75 hPa), i.e. genuinely the "larger, variability-based alternative".
The original .bin is deliberately left in place -- it is what the existing
(mis-weighted) runs used, so deleting it makes them unreproducible. Point
`data_ctrl_dir_std/data.ctrl`'s `xx_gentim2d_weight(8)` at the new file before
re-running.

Matt is re-running the OSSEs on another machine with this file, and outputting
**salinity for labsea iters 0 and 20** (see item 3).

**Unverified, flagged not chased:** `data_ctrl_dir_std/data.ctrl:66` currently
reads `xx_gentim2d_weight(8) = 'wApressure_ASTE270_EXFpress_std_new.bin'` --
the *sub-daily* std file, not the day-to-day one the `jrastd_daytoday` runs
were built around. Either that template was reverted after those runs, or the
runs used a different data.ctrl. This matters beyond the rerun:
`load_relcon_per_region()` reads `DATA_CTRL_DIR_STD` to weight the std runs'
control costs, so if the dir names a weight the run didn't use, panel (c)'s
STD bars are computed against the wrong sigma. Confirm which weight each std
run actually used before trusting any STD relcon number, old or new.

### 2. SPG and NS are the same run in the std set

Under `runc68v_froman_partialcables_jrastd_daytoday/201201/`, `subgyre/` and
`northsea/` are bit-identical at **both** iter0000 and iter0020 --
`xx_apressure`, `xx_uwind`, `m_bpday`, `bpdifanom_smooth` all match, same
mtimes (2026-07-21 01:57). `load_relcon_per_region()` returns identical values
to 4 dp for the two (`other=0.0841 patm=0.3813 winds=0.5346`), so this is
already visible in the existing 2x2 `fig9_patm_unc.py` STD bars. The four
spread runs are all distinct. One of the two needs re-running.

Don't try to identify which one is the duplicate from `data.ecco`: it names
the *labsea* obs file in every directory of *both* run sets, so it is a stale
template copy and carries no information about the region.

### 3. ADV_fw is not computable from the existing std runs

The `jrastd_daytoday` runs archived only `state_2d_set1` (PHIBOT etc.) and
`trsp_3d_set1` (UVELMASS, VVELMASS) -- no `state_3d_set1`, hence no salinity,
hence no ADV_fw. `gates_corrected_jraspread.csv` and
`gates_corrected_jrastd.csv` both exist in `output/davis_strait/`, but the
latter is the **old** `runc68v_froman_partialcables_jrastd` run (sub-daily std
prior), NOT `_daytoday`, so it cannot be quoted as Appendix B's std run.
Once labsea is re-run with salinity, `python gates_corrected.py
jrastd_daytoday` produces the CSV (the script takes a run tag on argv).

Cheaper argument that needs no rerun, and worth making regardless: Table 4's
own p_atm-on/off columns already show that switching the p_atm control **off
entirely** moves gateway bias reduction by <=0.2 pp (40.1->40.2, 27.4->27.4,
34.7->34.7, 4.4->4.4) and skill by <=0.1 pp. If deleting the control changes
nothing, re-weighting it cannot.

### The planned Appendix B figure (Matt approved the panel (d) idea 2026-08-06)

One 4-panel figure, deliberately mirroring Fig. 9 panel-for-panel so a reader
can flip between them, plus one new panel carrying the QoI claim:

- **(a) sigma_patm map, day-to-day std.** Same projection, cable dots and
  colorbar geometry as Fig. 9a, range 0-20 hPa instead of 0-2. Beyond the
  appendix this answers R2's original complaint head-on: it puts the ~8-15 hPa
  daily-p_atm std they said should be there on the page, labelled as
  day-to-day std of daily means, while Fig. 9a is labelled as inter-reanalysis
  spread. The two figures side by side *are* the clarification they asked for.
- **(b) Global max |dp_atm|/sigma_patm, four cables.** Identical axes, shading
  and ylim (0-1.7) to Fig. 9b. Free: `fig9_spread_3panel.load_global_ratio_
  series` already takes `run_dir_root` -- pass `RUN_DIR_ROOT_STD` and the new
  `load_sigma_patm_std()`. Keep it a separate panel rather than overlaying on
  Fig. 9b; identical ylim lets the eye do the comparison without a
  solid/dashed key that risks re-triggering "unclear what is plotted".
- **(c) Paired relcon bars**, std (hatched) vs spread (plain), one pair per
  cable. Carries "redistributes the attribution between wind and pressure".
  `fig9_patm_unc.plot_relcon_bars_grouped` already does exactly this and is
  tested -- don't rebuild it.
- **(d) 1:1 scatter of skill, std vs spread.** THE PANEL THAT BACKS THE
  "QoIs change negligibly" SENTENCE. x = skill in the spread OSSE, y = skill
  in the std OSSE, over SPNA grid points, four cables pooled, p_b and V_bt as
  two colors, 1:1 line, annotate RMS deviation from the line. Everything on
  the diagonal *is* "changes negligibly", stated quantitatively in one panel.
  Preferred over a row of four skill-difference maps: those eat four panels
  and a near-empty diverging map invites "what's that patch?".

ADV_fw stays out of the figure -- caption/text numbers only, per item 3.

Buildability: (a), (b), (c) load from data on disk. (d) needs p_b and V_bt
skill for the four std runs, computable from `state_2d_set1` PHIBOT and
`trsp_3d_set1` via `smartosse.osse.OSSE`/`MultiOSSE` -- nothing missing. Note
Fig. 5's own source is **not in the repo** (no `.py` references
`regions_skill_bp_and_uvbt`; it came from a notebook), so (d) means writing
that skill computation fresh rather than reusing it.

## Update 2026-08-05: `fig9_spread_3panel.py` — legend to 3x2, PDF output, `__main__`

**Read this before touching Fig. 9.** The figure the manuscript actually
includes is no longer `fig9_patm_unc.py`'s 2x2 mosaic. It is
`fig9_spread_3panel.py`, a spread-only 1x3 rendition ((a) sigma_patm map,
(b) global max |dp_atm|/sigma_patm, (c) per-cable relcon bars), and
`tex/sections/controls.tex:22` includes its output as
`figures/fig9_spread_3panel_test.png`. All the 2026-07-13 entries below
describe the 2x2 layout and apply to Fig. 9 only through the loaders and
low-level helpers the 3-panel module imports from it.

This session (Matt's asks):

- **PDF as well as PNG.** The module had no `__main__` block -- the previous
  render came from an ad-hoc driver that no longer exists -- so it now has
  one, following `fig1_global_cables.py`'s pattern: `use_latex_times()` +
  `use_embedded_pdf_fonts()`, `open_astedataset()`, then both files. Run as
  `module load texlive && conda activate .../esmpy_3.10 && python -m
  smartosse.figures.fig9_spread_3panel` (~3 min). Output goes NEXT TO the
  module, not under `output/`, because that is where controls.tex's
  `\includegraphics` path resolves (`tex/figures` symlinks to `figures/`).
  PDF font embedding checked with the project's standard recipe: 8 x
  `/FontFile` + `/Subtype /Type1`, i.e. real embedded fonts, not Type 3.
  **This closes the "serif + embedded-font PDF" TODO for Fig. 9** (see
  `smartosse-manuscript/README.md`).
- **Panel (b) legend 2x3 -> 3x2, larger.** `ncol=3 -> 2`, fontsize `14 -> 18`
  (new `RATIO_LEGEND_FONTSIZE`), grey band swatch alone on the bottom row.
  matplotlib fills legend cells COLUMN-major, so the on-screen row layout is
  NOT the handle order: getting LS/SPG on row 1, NS/Nfl on row 2 and the band
  on row 3 means handing it the columns, `[LS, NS, band]` then `[SPG, Nfl]`,
  i.e. the permutation `(0, 2, 4, 1, 3)` of the natural order. That is what
  the new `legend_handle_order` kwarg on `plot_patm_adjustment_ratio` is for.
- **ylim 1.45 -> 1.7** (`RATIO_YLIM`). The legend has to sit in the
  guaranteed-empty strip above the ratio=1 line (no curve can enter it by
  construction); three rows at 18 pt did not fit in the old headroom. Curves
  unaffected.

**Still stale, flagged not fixed:** the caption in `controls.tex` still
describes the OLD panel (b) -- "maximum absolute adjustment across the cable
sensors" against a "constant spread-based uncertainty envelope" -- which is
not what the panel plots (it is the whole-domain max, normalized pointwise by
sigma_patm). Needs rewriting before submission.

## Update 2026-07-13 (latest for the 2x2 `fig9_patm_unc.py`): (c) legend height, split the difference

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

---

# Davis Strait / gateway freshwater diagnostics — see the dedicated doc

Not a figure-styling thread, so it is kept out of this file: the gateway
transport recompute (the published Table 4 quantity was not a section-normal
flux), the Nares gate truncation, the corrected Table 4, the Fig. 7d
`get_advfw` fix, and the 2026-08-05 p_b -> volume transport -> ADV_fw chain
diagnostics all live in **`DavisStrait_fw_decompisition_plan.md`** in this
directory. Read that before touching Fig. 6, Fig. 7, Table 4, or
`tex/sections/case_study.tex`.

Scripts in this directory belonging to that thread:
`gen_gate_caches.py`, `gates_corrected.py`, `gates_significance.py`,
`gate_sign_probe.py`, `gates_surface_layer.py`,
`gates_surface_nares_detail.py`, `nares_along_channel.py`,
`nares_gate_corrected.py`, `davis_strait_*.py`, and the newest pair
`davis_chain_extract.py` / `davis_chain_figs.py`.

One item from that thread DOES affect a figure in this file:
`osse.ForecastModel._load_fm_bt` computes `UVELMASS * hFacW * dyG * drF`, but
`UVELMASS` is already `u*hFacW`, so partial bottom cells are squared. That is
Fig. 6's own barotropic-velocity quantity. Small (bottom cells only) and not
yet fixed.
