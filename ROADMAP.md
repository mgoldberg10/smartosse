# smartosse — repo cleanup roadmap

Working checklist for turning this from "the code that made the paper figures" into a
public artifact that stands up to two different audiences at once:

- **Scientific readers / reviewers.** The paper's data availability statement already
  names `github.com/mgoldberg10/smartosse` by URL. This repo is a *cited artifact of the
  manuscript*. It needs to be honest about what it can and cannot reproduce.
- **Technical interviewers.** They will not have ASTE, will not download a nature run, and
  will spend about four minutes. They judge structure, tests, CI, docs, and whether the
  README makes them go "huh, neat."

These two goals conflict less than they appear. The thing that satisfies both is the same:
**make the reproducibility boundary explicit and make the innermost tier actually run.**

---

## 0. The framing decision (do this first — everything else follows from it)

The honest problem: full reproduction needs ASTE + its inputs, the run directories, and a
nature run that is increasingly hard to source. That is not fixable and should not be
pretended away.

The fix is to stop treating "reproducible" as binary and publish **tiers**. Good news —
the code is *already* built this way, it just isn't named or documented as such. There is a
latent two-stage architecture in `smartosse/figures/`: `gen_*.py` / `build_cache()`
functions read run output and write small `.nc` caches into `figures/data/`, and `make_fig()`
functions render purely from those caches.

Proposed tiers, to be stated up front in the README:

| Tier | What you can do | What you need | Status today |
|---|---|---|---|
| **0** | Regenerate **every paper figure** from shipped caches | `docker run`, ~200 MB download | Latent in the code; needs a driver + published caches |
| **1** | Regenerate the caches from run output | The optimization run directories (pfe; copies on TACC `/scratch`) | Works, paths hardcoded; runs on the wrong machine (§4b) |
| **2** | Regenerate run output | ASTE build + adjoint + nature run + JRA-55 | Inputs located and tiny (§5b) — needs rescuing off `/scratch` |

Tier 0 is the whole game. It is what an interviewer clicks, and it is what a reviewer
needs to check a number. It is genuinely achievable because `figures/data/` is only 180 MB
and several of those files are superseded variants that can be dropped.

> Naming the tiers is itself the flex. "I know exactly which layer of my pipeline is
> reproducible by a stranger and I built a Docker image for that layer" reads far better
> than a repo that quietly implies everything runs.

- [ ] Decide on the tier framing (or a variant of it) — every task below assumes it
- [ ] **Tag the current commit `v1.0-paper-submitted` before touching anything.** The
      manuscript is in review. Freeze the exact tree that produced the submitted figures so
      no amount of refactoring can cost you the ability to answer a reviewer.

---

## 1. Repo hygiene — what is actually in the repo

**Verified state:** 66 `.py` files on disk, **23 files tracked by git**. The gap is not an
oversight — `smartosse/.gitignore` line `**/figures/*` ignores the entire figures
directory, plus `**/*.png`, `**/*.nc`, `**/*.pdf`. The handful of tracked figure modules
were force-added past it.

- [x] ~~Fix `smartosse/.gitignore`.~~ **already gone on this branch** (checked 2026-09-24,
      pfe checkout) — no `smartosse/.gitignore` file exists; the root `.gitignore` handles
      `smartosse/figures/output/` and `smartosse/figures/data/` correctly and has none of the
      MATLAB-era cruft this item described. Unclear whether it was deleted upstream of this
      branch or never existed here — worth a `git log -- smartosse/.gitignore` check on
      `main` before assuming this is universally resolved.
- [x] ~~**Triage `smartosse/figures/` (66 scripts).**~~ **Paper-figures bucket: tracked**
      (Matt, `d764631`, merged in this session) — `fig1_global_cables`, `fig3_bp_std`,
      `fig5_misfit_rmse_skill`, `fig6_regions_skill_bp_uvbt`, `fig8_smart_grace_mo_skill`
      (renamed from `smart_grace_mo_skill`), `fig9_spread_3panel`, `fig11_ib_ctrl_freqs`
      (renamed from `fig_ib_ctrl_freqs`), `figB_patm_std_4panel`,
      `figD1_sensor_spacing_skill_diff` (renamed from `sensor_spacing_skill_diff`) now
      exist and import fine on this pfe checkout — the original ⚠️ below (from earlier this
      session, before that push) is stale for this bucket specifically. `fig7_greenland_fwflux`
      and `si_*` are the only paper-figure-bucket names from the original list not yet tracked.
      Exploratory/superseded bucket and the untracked core modules below are **still not
      present on pfe** — still needs a TACC session:
  - *Paper figures* — `fig1_global_cables`, `fig3_bp_std`, `fig5_misfit_rmse_skill`,
    `fig6_regions_skill_bp_uvbt`, `fig7_greenland_fwflux`, `fig9_*`, `fig10_patm_mechanism`,
    `figB_patm_std_4panel`, `figD1_sensor_spacing_skill_diff`, `fig8_smart_grace_mo_skill`,
    `fig11_ib_ctrl_freqs`, `si_*`, `advfw_skill_maps`, plus the `gen_*` cache builders. **Track these.**
  - *Exploratory / superseded* — the `davis_*` family (13 files), `gates_*`, `nares_*`,
    `gate_sign_probe`, `debug_panel_c`, `fig7_panel_a_*`, `fig7_skeleton`,
    `davis_strait_repro_old_pipeline`. Decide: a clearly-labeled `figures/exploratory/`
    subdir, or cut. Leaning **keep in a subdir with a one-line README** — showing the
    exploration is not a weakness, showing it *undifferentiated from the final figures* is.
  - [x] ~~*Delete outright* — `.fig7_skeleton.py.swp`~~ (not present on this checkout — see
    the pfe note above; presumably TACC-only, unaffected by this branch's fix) ~~,
    `fig9_patm_unc.py.pre_2x2_redesign`~~ **deleted** (`git rm`, this session) — it was
    tracked, git history is the backup. `debug_panel_c.py` was already
    gone (`914fb69`) — it was a Jupyter paste-buffer whose IPython magics were an E999.
- [ ] Untracked core modules: `curl.py` (48 lines), `plot_new.py` (581), `slope_cable.py` (329),
      `wind_bp_fw.py` (526). ~1500 lines of real code invisible to git. Track or cut, but decide.
      Note `plot.py` (23 KB) and `plot_new.py` (20 KB) coexisting is a smell — resolve or rename.
      **Also not present on this pfe checkout** (same story as the figure triage above) —
      needs a TACC session.
- [ ] Move the eight stray PNGs out of the repo root (`i2_ocean*.png`, `inset_*.png`,
      including one with parentheses and the word "current" in the filename). **Not present
      on this pfe checkout** — needs a TACC session.
- [ ] Decide on `smartosse/tex/` (the full manuscript source, currently untracked). Options:
      keep it out entirely until acceptance; a private sibling repo; or a `paper/` dir added
      at acceptance. **Recommend: leave it out for now**, revisit post-review.
- [x] ~~`smartosse/__init__.py` six `from .x import *` lines~~ done (`ee84bf4`). Not a
      30-second cosmetic fix as originally filed — it was the blocker for both CI and pfe.
- [ ] Scrub the public tree for the TACC account number (`08381`) and personal absolute paths.
      Deferred on purpose: the real fix is §4's `paths.py`/`sites.yml` env-var resolver, not
      find-and-redact; scrubbing first would just mean re-editing the same lines twice.
- [x] ~~`LICENSE` file — there is none.~~ done, this session: added `LICENSE` (MIT, matching
      `setup.py`'s pre-existing `keywords='MIT License'` signal) and fixed `setup.py`'s
      `license=''`/`keywords='MIT License'` (the license-in-keywords typo) to `license='MIT'`.

---

## 2. Make the tests pass and CI green

**Verified:** `pytest tests/` → **1 passed, 1 failed** under the `esmpy_3.10` conda env.

The failure is trivial API drift, not a real bug:

```
tests/test_bp.py:136: TypeError: BPReader.get_sensors() got an unexpected keyword argument 'bad_val'
```

`bp.py:210` is `def get_sensors(self, bad_vals=[0., -9999.])` — the parameter was pluralized
and the test never followed. Fixing the kwarg will likely expose a second failure: the test
asserts `"Found 33 sensors"` while the run printed `Found 5400 sensors`, because the
deterministic fixture is being overwritten but the `bad_vals` default now also excludes
`-9999.`. Expect to re-derive the expected arrays.

- [x] ~~Fix `test_bp.py`~~ done (`90cfaad`). The sensor assertions did **not** need re-deriving.
- [x] ~~Mutable default argument~~ done (`90cfaad`), now a tuple.
- [ ] The library prints debug output on every call — 14 `print()` in `bp.py`, 13 in `osse.py`.
      Test output is a wall of `/tmp/pytest-of-goldberg/...` paths and dimension tuples.
      Convert to `logging` with a module logger. High visual payoff for low effort.
- [ ] There is a swallowed error printing `Error during computation: 'dim_0' not found in
      array dimensions ('ioptim', 'time', 'sensor', 'k')` during the passing test.
      `STATUS.md` notes this "still affects nothing" — either fix it or make the code say
      out loud why it is benign.
- [ ] **Broaden the test suite.** One test file for a 4000-line package is the single
      weakest signal in the repo. Cheap, genuinely useful targets that need no model data:
  - `utils.write_float32` / `read_float32` roundtrip (big-endian correctness is load-bearing)
  - `utils.grep_ctrl` / `grep_cost` — parsers, ideal for fixture-based tests
  - `dataset.get_extra_metadata_aste1080` — pure function, exact expected dict
  - `figs_utils.latex_escape`, `style_colorbar` tick generation — pure, fast
  - the cache merge/reuse logic (`combine_first` path) described in `STATUS.md` — that is
    real logic with real edge cases
  - a smoke test that every tracked figure module imports cleanly
- [x] ~~CI's light dep set could not import the package~~ fixed at the source (`ee84bf4`): the
      suite now passes with cartopy/cmocean/ecco_v4_py/matplotlib/pyresample blocked, so the
      existing pip line suffices. The flake8 step blocked separately and is fixed in `914fb69`.
- [ ] Still open on CI (`.github/workflows/python-tests.yml`): it pip-installs a *partial* dependency
      set (no `cartopy`, no `ecco_v4_py`, no `matplotlib`) — so it cannot currently import
      most of the package. Either install the full env (conda/micromamba action) or mark the
      map-plotting tests as optional and keep CI to the pure-Python core.
- [ ] Add a coverage badge next to the existing tests badge.

---

## 3. Packaging and environment

**Verified bug:** `osse.py` imports `ecco_v4_py`, and `setup.py` lists it — but
`environment.yml` does not. Anyone following the README's env gets an ImportError.

- [x] ~~`environment.yml` says `name: base`. Rename to `smartosse`.~~ done.
- [x] ~~Add `ecco_v4_py` to `environment.yml`~~ done (verified installable via conda-forge — the
      exact build present in the working `esmpy` conda env on this machine, `conda-meta` checked
      directly rather than assumed). ~~drop `typing` from both files~~ done (also dropped from
      `pyproject.toml`'s deps, which never had it to begin with).
- [x] ~~`setup.py` → `pyproject.toml`.~~ done — version `0.1.0`, `[tool.setuptools.packages.find]`
      (fixes `smartosse.figures` not being installed — verified with a real `pip install -e .`
      + `import smartosse.figures` in the extract env, not just read by inspection). Split
      dependencies: light `numpy/scipy/xarray/xmitgcm/tabulate` as the base install (matches
      what `environment-extract.yml` needs), heavy plotting stack as an optional
      `smartosse[plotting]` extra, dev tools as `smartosse[dev]`. `setup.py` deleted.
      `pytest tests/` still 2 passed against the reinstalled package.
- [ ] Pin versions. `STATUS.md` records rendering workarounds specific to **matplotlib 3.4.3**
      (`patch_pdf_indexed_image_bitdepth()`, the `transparent=True` coastline-speckle bug).
      Those pins are load-bearing for figure fidelity — say so in a comment.
- [ ] Ship a lockfile (`conda-lock` or `environment-lock.yml`) for the exact figure-producing env.

### Docker

Worth doing, and it is the natural home for Tier 0.

- [ ] `Dockerfile` — micromamba base + the locked env + the package. Target: `docker run
      ghcr.io/mgoldberg10/smartosse make figures` reproduces the paper figures into a mounted
      volume, with zero ASTE access.
- [ ] Publish to GHCR from CI on tag. A `docker pull` line in the README that actually works
      is worth more than any amount of prose about reproducibility.
- [ ] Optional second stage for Tier 1 (adds the heavier ASTE-reading deps), but do not build
      it until Tier 0 is solid.

---

## 4. Paths and configuration

**Verified:** 6 hardcoded `/work/08381/goldberg/...` paths in the core modules and **161** in
`smartosse/figures/`. These are baked into function *defaults* (`osse.py:20`, `osse.py:86`,
`dataset.py:51`, `utils.py:73`), so the package literally cannot be imported-and-used off TACC.

- [ ] Add `smartosse/paths.py`: a small resolver with env-var overrides
      (`SMARTOSSE_DATA_ROOT`, `SMARTOSSE_GRID_DIR`, `SMARTOSSE_NR_DIR`, `SMARTOSSE_CACHE_DIR`)
      falling back to a `config.yml`, falling back to the shipped cache directory.
- [ ] Sweep the core modules first (6 sites, an afternoon). The 161 figure-script sites can go
      gradually, or mostly resolve themselves once they read from `SMARTOSSE_CACHE_DIR`.
- [ ] Make the error message good: if a path is unset and the data is absent, say *which tier*
      the user is attempting and what they would need. That error message is a documentation
      surface.

---

## 5. Turn the figure pipeline into a real thing

This is the highest-leverage engineering work in the repo, because the architecture already
exists and just needs a name and a driver.

- [ ] Write `figures/MANIFEST.yml` (or a Python dict): for each paper figure — figure number,
      module, cache inputs, output filenames, which tier it needs. This doubles as the
      reviewer's index and the README's figure gallery source.
- [ ] A single driver: `make figures`, or `python -m smartosse.figures --all`, or a
      `smartosse-figures` console script. It should render everything from cache and report
      what it skipped and why.
- [ ] Give the ~20 figure modules that lack `__main__` a consistent CLI, or explicitly mark
      them library-only (`figures/__init__.py` already says modules are "meant to be imported
      into a notebook, not run as a script" — but 29 of them now have `__main__` blocks, so
      that docstring is stale either way).
- [ ] **Publish the caches to Zenodo, get a DOI.** `figures/data/` is 180 MB and contains
      obvious superseded variants (`smart_grace_mo_skill_stdold.nc`,
      `..._oldgrace.nc`, `..._it4.nc` — 6.7 MB each). Trimmed, this is likely ~100 MB.
      Add `smartosse fetch-data` to pull it. The Zenodo DOI then goes into the paper's data
      availability statement alongside the GitHub URL — which closes the loop on the
      reproducibility claim the manuscript already makes.
- [ ] Audit the caches for anything not intended to be public before uploading.

---

## 4b. Multi-site topology — pfe / Stampede3 / anywhere

**The situation.** Runs execute and live on **pfe** (NASA). Output is periodically copied to
**Stampede3 `/scratch`** because the pfe Python environment is broken, and analysis happens
at TACC. Stampede3 purges scratch, so the copies evaporate; pfe remains the system of record.

**Verified facts that decide the design:**

- This machine is `c454-082.stampede3.tacc.utexas.edu`. `/work2` is the **shared Stockyard
  filesystem** (6.8 PB, mounted across TACC systems, **not purged**) — which is why paths say
  `ls6` while we are on Stampede3. `/scratch` is Stampede3-local and **is** purged.
  So the "rescue off scratch" in §5b is mostly just `cp` to `/work2`, which is already there.
- **The cache builders need neither cartopy nor matplotlib.** `gen_gate_caches`,
  `gen_appendixB_skill_cache`, `gen_patm_uncertainty_fields`, `gen_patm_daytoday_weight_Pa`
  import only numpy / xarray / pandas / xmitgcm / ecco_v4_py.
- **But `ecco_v4_py` drags in the entire plotting stack.** Measured: importing
  `ecco_v4_py.ecco_utils` pulls `cartopy, matplotlib, shapely, pyproj, xgcm, scipy` — and it
  is used for exactly **two functions**, `get_llc_grid` and `UEVNfromUXVY`.
- **`import smartosse.bp` pulls cartopy and matplotlib too**, via the `from .plot import *`
  chain in `__init__.py`. So the §1 "star imports are ugly" item is not cosmetic — it is the
  thing that makes a lightweight install impossible.
- ~~`asteoptim` is an undeclared dependency~~ **correction, 2026-09-24**: `dataset.py`/
  `osse.py` only ever matched this grep via `open_asteoptimdataset` (a function *name*, not
  an import) — that function is defined locally in `dataset.py`. The one real
  `from asteoptim.dataset import ...` was in `gen_gate_caches.py`, and it turned out to be
  an outdated predecessor of this package, not a real external dependency — see §4b below.
  `wind_bp_fw.py`/`slope_cable.py` weren't re-checked (still untracked, not present on this
  branch — see §1).

### Recommended architecture: move the extraction to the data, not the data to the extraction

```
pfe  ──────────────────────────►  TACC /work2  ──────────►  anywhere
run output          gen_*.py      .nc caches      make_fig      figures
(TB, stays put)   (extraction)   (~180 MB)       (plotting)
                   needs: numpy, xarray,          needs: + cartopy,
                   pandas, xmitgcm, netcdf4       matplotlib, LaTeX
```

Today the split is in the wrong place: **bulk run output** crosses the wire onto purgeable
scratch, and extraction happens at the far end. Run `gen_*` **on pfe, next to the data**, and
only the ~180 MB of `.nc` caches ever move — onto `/work2`, which is not purged. The purge
problem disappears rather than being managed.

The happy accident is that this is the *same* boundary as the Tier 0 / Tier 1 split in §0.
One piece of work fixes the purge problem, the transfer problem, the pfe problem, and
reproducibility at once.

### So: is it worth fixing Python on pfe? Yes — but a much smaller env than you think

Not a full analysis environment. An **extraction-only** environment: numpy, xarray, pandas,
xmitgcm, netcdf4, dask. No cartopy (almost certainly what is broken — it needs GEOS/PROJ
system libraries), no matplotlib, no LaTeX. Micromamba in user space, no admin needed.
Call it a half-day.

Three decoupling tasks make that env possible, and all three are things the repo wants anyway:

- [x] ~~**Stop `__init__.py` importing the plotting stack.**~~ done (`ee84bf4`), via PEP 562
      lazy `__getattr__`. `from smartosse.bp import BPReader` now pulls none of cartopy,
      matplotlib, cmocean, pyresample or ecco_v4_py. `utils.py`'s module-level matplotlib
      import went local at the same time.
- [x] ~~**Break the `ecco_v4_py` dependency out of the extraction path.**~~ done: vendored
      `get_llc_grid` / `UEVNfromUXVY` into `smartosse/llc_grid.py` (MIT, attributed, copied
      from `ecco_v4_py` 1.6.0 — both functions only ever needed numpy/xarray/xgcm; the
      cartopy/matplotlib/shapely/pyproj pull was `ecco_v4_py`'s own `__init__.py`, not
      these two functions). `osse.py` and `figures/gen_gate_caches.py` now import from
      `.llc_grid` instead. `osse.py`'s `_plot_skill` also gained local `from .plot import
      spna` / `from .cmaps import Colormaps` (were module-level, so importing `osse.py`
      for `NatureRun`/`ForecastModel`/`OSSE` — as every `gen_*.py` cache builder does —
      silently pulled the whole plotting stack in anyway). Same fix applied to `patm.py`'s
      module-level `matplotlib.pyplot` (moved local to `plot_jra_vs_aste_cable_variability`,
      the one function that needs it) after it turned out `gen_patm_uncertainty_fields.py`
      imports `patm.load_forcing_generic` and was tripping over it. One more found the same
      way: `gen_appendixB_skill_cache.py` imported three path constants from
      `fig9_patm_unc.py` — a plotting module — for no other reason; those three are now
      duplicated locally there (a comment says to keep them in sync) rather than editing
      `fig9_patm_unc.py` itself, per the "don't touch figure modules mid-review" risk below.
      **`asteoptim` turned out not to need declaring at all** — its one call site
      (`gen_gate_caches.py`'s `from asteoptim.dataset import open_astedataset,
      open_asteoptimdataset`) was pointed at an outdated predecessor of this very package;
      swapped for `smartosse.dataset`'s own (signature-compatible) versions. Same for
      `smartcables`, elsewhere flagged as a wildcard-import smell — also an outdated
      predecessor, not a real dependency.
      **Verified** (`use-extract` env on pfe, 2026-09-24): all four `gen_*.py` cache
      builders import clean with zero `cartopy`/`matplotlib`/`ecco_v4_py`/`cmocean`/
      `pyresample` in `sys.modules` afterward, and `pytest tests/ -q` still 2 passed.
- [x] ~~Then: `environment-extract.yml`~~ existed already; added `xgcm` + `future` (both
      light — xgcm depends on nothing but xarray/dask/numpy/future) for `llc_grid.py`, and
      installed them into the live `/home3/mgoldbe1/envs/extract` env. CI-on-ubuntu still open.

### The config file: key on *site*, not on machine-type branching in code

Yes, do this — but resist `if on_pfe: ... elif on_stampede: ...` scattered through modules.
One `config/sites.yml`, one resolver (`smartosse/paths.py`, §4):

```yaml
sites:
  pfe:
    detect: {hostname: ["pfe*", "r*i*n*"]}
    run_root:  /nobackup/<user>/aste_270x450x180/osses
    grid_dir:  ...
    cache_dir: ...
  stampede3:
    detect: {hostname: ["*.stampede3.tacc.utexas.edu"]}
    run_root:  /scratch/08381/goldberg/aste_270x450x180/osses   # purgeable, Tier 1 only
    grid_dir:  /work2/08381/goldberg/ls6/aste_270x450x180/GRID_noblank_real4
    cache_dir: /work2/08381/goldberg/ls6/smartosse/smartosse/figures/data
  docker:
    cache_dir: /data          # note: no run_root at all
```

Design rules that matter:

- **Detect by hostname, but `SMARTOSSE_SITE` and `SMARTOSSE_*_DIR` env vars always win.**
  Detection is a convenience, never the only way in — otherwise a new machine is a code change.
- **`run_root` must be allowed to be absent.** The `docker` site above has no run_root, and
  that is the point: it is what lets a stranger regenerate figures with no model data. Any
  code that assumes run_root exists is code that cannot run at Tier 0.
- **Make the missing-path error the documentation.** "`run_root` is not configured for site
  `docker`; this figure needs Tier 1 inputs (see docs/reproducibility.md). Tier 0 figures
  work from the cache — run `make figures`." That error message is read more often than
  the README.
- Add a `sites.yml` entry for a generic `laptop`/`local` site so contributors have an
  obvious template, and keep the file free of anything user-specific beyond your own entry.

### Job scripts

- [ ] Pull the current job scripts from pfe into `model/jobs/` (§5b) verbatim, plus a note
      saying which scheduler and queue they target. They encode node counts, wall times, and
      the tile decomposition that has to match `SIZE.h` / `data.exch2` — that is provenance,
      not boilerplate, and it is the part nobody can reconstruct from the paper.
- [ ] While on pfe, inventory what else exists *only* there: the nature-run extraction
      pipeline, the llc4320 handling, and the `optim` driver settings are the likely ones.

---

## 5b. Model provenance — Tier 2 (namelists, code mods, MITgcm version)

**This turned out far better than expected. Almost none of it is on pfe — it is on this
machine, and it is tiny.** Verified:

| Piece | Location | Size |
|---|---|---|
| MITgcm source | `/work/08381/goldberg/ls6/MITgcm_c68v` — a **git clone**, `285cda8c7`, tagged `checkpoint68v` (2024/02/03) | — |
| Code modifications | `.../osses/<run>/code_froman/` — ~40 `.F`/`.h` files + `packages.conf`, incl. `cost_gencost_bpv4.F`, `CTRL_SIZE.h`, `ECCO_OPTIONS.h` | **354 KB** |
| Namelists | `.../osses/<run>/data*` — 41 files (`data`, `data.cal`, `data.ctrl`, `data.ecco`, `data.exf`, `data.pkg`, `data.autodiff`, `data.diagnostics`, …) | **187 KB** |
| Per-experiment deltas | `<run>/201201/<region>/iter####/` carries only `data.ctrl` + `data.ecco` — i.e. exactly the two namelists that vary per OSSE | ~KB |
| Grid | `/work/.../aste_270x450x180/GRID_noblank_real4/` | larger |

So the "Modifications to the forecast model configuration" that the paper's data
availability statement already promises is **~550 KB per run** and can live in git directly.
That is not a stretch goal, it is an afternoon.

> ⚠️ **Time-sensitive.** The OSSE run directories are on `/scratch/08381/goldberg/...`.
> TACC purges `$SCRATCH`. The provenance the manuscript cites is currently sitting on
> purgeable storage. **Confirm LS6's current purge policy and get the namelists + code mods
> off scratch before anything else in this section.** Copying 550 KB is cheap insurance;
> re-deriving a lost namelist set after acceptance is not.

- [x] ~~**Rescue first, organize later.**~~ done, 2026-09-24 — `model/code/froman/` (the
      `code_froman/` modifications) and `model/namelists/<run>/` for all **7 run families** the
      currently-tracked figure code actually reads: `partialcables_jraspread` (all 5 regions),
      `partialcables_jraspread_spacing` (70/140/210km), `partialcables_jrastd_daytoday`,
      `ib_freq2` (7 frequencies), `gracellc4320_sc_spread`, `gracellc4320_spread`. Not the
      `noapress`/`fixbpweight` candidates originally guessed at above — those turned out not to
      match what the code imports (see ROADMAP's own correction near the `asteoptim` note); the
      actual set was determined by grepping the tracked `smartosse/figures/*.py`/`gen_*.py` for
      the `runc68v_*` strings they open, not guessed from `STATUS.md` prose. Nature-run
      extraction under `osses/naturerun/` explicitly deferred (Matt, needs manual intervention).
      **Found and worked around en route**: a `cleanup.bash` at each run root had *already*
      deleted the real namelists from `partialcables_jraspread` (4/5 regions) and
      `partialcables_jraspread_spacing` (all 3 spacings) before this session — reconstructed
      from `STDOUT.0000`, which MITgcm always echoes every namelist into and which `cleanup.bash`
      preserves; see `model/README.md` for the exact method and how it was verified.
- [x] ~~Record the MITgcm version precisely~~ done: **checkpoint68v, upstream commit
      `285cda8c7`** — `model/README.md`.
- [ ] Capture the build recipe: the optfile used, `genmake2` invocation is only partially done
      (compiler `ifort 19.1.3.304`, MPI HPE MPT 2.30, from `genmake.log` — but not the optfile
      name itself yet). `SIZE.h`/`data.exch2` tile decomposition: multiple variants are now
      committed (`model/namelists/*/base/data_exch2_*`), but which one each run actually used at
      submission time hasn't been cross-checked against `STDOUT.0000` the way the ctrl/ecco
      values were. Job submission scripts: done, `model/jobs/`.
- [x] ~~Capture the **optimization** side too~~ done — `model/optim/` (collapsed to a single
      template across the 6 `OPTIM*/` families once it turned out `data.optim`'s only real
      per-run content, `numiter`/`nupdate`/`coldstart`, is regenerated by every job script's own
      heredoc; see `model/README.md`).
- [x] ~~Diff the namelist sets across experiments and commit **one base set plus per-experiment
      deltas**~~ done — `model/namelists/<run>/base/` + one dir per region/frequency/spacing
      holding only `data.ctrl`/`data.ecco` (or just `data.ctrl` for the `ib_freq2` frequency
      sweep, where only that file varies). 2.0 MB total across all 7 run families, not 7×187 KB.
- [ ] `docs/model-setup.md`: version → clone → apply `code/` → build → namelists → run →
      what output feeds Tier 1. Be explicit that this needs HPC and is not push-button.
- [ ] Anything genuinely only on **pfe** (nature-run extraction scripts? the llc4320 pipeline?)
      — list it here as you find it, and pull it over the same way. Deferred (Matt).

---

## 5c. Repo reorganization

Worth doing, and the moment is right: the `v1.0-paper-submitted` tag protects the old state
and `git mv` preserves per-file history. The current layout has real problems — figure
scripts, cache builders, exploratory one-offs and a 139 KB devlog all sit flat in one
directory, and `smartosse.figures` is not even installed (§3).

Proposed target:

```
smartosse/
├── README.md  ROADMAP.md  LICENSE  CITATION.cff
├── pyproject.toml  environment.yml  environment-lock.yml
├── Dockerfile  Makefile
├── docs/
│   ├── reproducibility.md      # the tier table
│   ├── data-access.md          # ASTE, nature run, JRA-55
│   ├── model-setup.md          # §5b
│   └── devlog/                 # STATUS.md, split per figure
├── model/                      # §5b — Tier 2 provenance
│   ├── README.md               # MITgcm c68v @ 285cda8c7
│   ├── code/                   # code_froman
│   ├── namelists/{base,experiments}/
│   └── build/  jobs/
├── src/smartosse/              # src layout
│   ├── paths.py                # §4
│   ├── io/        bp.py dataset.py nr.py utils.py
│   ├── osse/      osse.py patm.py
│   ├── viz/       plot.py cmaps.py
│   └── figures/
│       ├── MANIFEST.yml        # §5
│       ├── paper/              # fig1..fig10, SI
│       ├── cache/              # gen_*.py builders
│       └── exploratory/        # davis_*, gates_*, nares_*
├── tests/
└── data/                       # DOI-backed caches, gitignored
```

Decisions embedded above, each arguable:

- **Keep `figures/` inside the package.** It is importable today and `python -m
  smartosse.figures.fig10_patm_mechanism` already works for 29 modules. Moving it out would
  trade a working interface for tidiness.
- **Adopt `src/` layout.** Cheap now, and it would have caught the "`smartosse.figures` isn't
  in `packages=`" bug (§3) immediately.
- **Split `io`/`osse`/`viz`.** Optional. It is the most invasive change here and the one
  most likely to churn imports for modest gain — reasonable to skip or defer.
- **`model/` at top level, not under the package.** It is Fortran and namelists, not Python.

Sequencing: do this **after** §3 (packaging) and §4 (paths), so imports are already
centralized, and **before** §6 (README/gallery), so the docs describe the final shape.
Add a smoke test that every module still imports (§2) *before* starting, and move with
`git mv` only.

One caution: the manuscript is in review. Nothing above changes figure output, but if a
reviewer asks for a re-render mid-reorg, render from the `v1.0-paper-submitted` tag rather
than racing to fix the working tree.

---

## 6. Documentation

- [ ] **README rewrite.** It is currently four lines. Target structure:
  1. Hero image (see §7) + title + badges (tests, coverage, DOI, license, docker)
  2. Two sentences on what a SMART cable OSSE *is* — most readers, technical or scientific,
     will not know
  3. The tier table from §0
  4. Quickstart: three commands to a reproduced figure
  5. Figure gallery — thumbnail grid linking each paper figure to the script that made it.
     This is the single best README element available to you; the figures are genuinely
     striking and there are ~15 of them.
  6. Architecture: the `gen_* → cache → make_fig` flow, as a diagram
  7. Repo map, citation, license
- [ ] `CITATION.cff` — so GitHub renders a "Cite this repository" button.
- [ ] **`STATUS.md` (139 KB, 59 sections) is an asset, but it is in the wrong place.** It is a
      detailed engineering log with real rigor in it ("verified after writing: PNG alpha == 255
      everywhere, and both image streams in the PDF unfilter to exactly their expected byte
      counts"). That is exactly the kind of thing that impresses a careful reader — and exactly
      the kind of thing that drowns a casual one. Split it per-figure into `docs/devlog/`,
      link from the figure gallery, and pull three or four of the best findings into a short
      "Notes on figure fidelity" page. Same for `SI_FH_HOVMOLLER_STATUS.md`,
      `SI_BAROTROPIC_TIMESCALE_STATUS.md`, `DavisStrait_fw_decompisition_plan.md` (117 KB).
- [ ] A `docs/` site (mkdocs-material → GitHub Pages) once the above exists. Low effort,
      disproportionate polish.
- [ ] Short `CONTRIBUTING.md` / `docs/data-access.md` explaining, without apology, exactly how
      to get ASTE, the nature run (ECCO portal + the Poseidon Project reference already cited
      in the paper), and JRA-55. Being the person who wrote down where the hard-to-find data
      lives is a contribution in itself.

---

## 7. The flashy visuals

Ranked by impact-per-hour. Pick one hero, not three.

1. **Animated skill evolution over optimization iterations** — *recommended hero.* You already
   have `data/si_skill_over_optim.nc` cached, so this needs no new model runs. A GIF of the
   skill map filling in as the adjoint iterates is immediately legible to someone who knows
   nothing about oceanography: "the model learns the ocean from cable data." Put it at the top
   of the README.
2. **Fig. 1 global cable network** as a README banner — already rendered
   (`fig1_global_cables_multiline_legend.png`), needs only cropping. Nearly free.
3. **Daily OBP anomaly animation over the SPNA with the cable overlaid** — the "what is being
   observed" shot. Needs the nature run, so it is a one-time render you commit as a GIF/MP4.
4. **Redraw `osse_flowchart.pdf` as a clean SVG** for the README's architecture section.
   Theme-aware SVG so it reads in dark mode.
5. A skill dashboard / interactive figure browser — genuinely cool, clearly out of scope until
   everything above is done. Flag as stretch.

Practical notes: keep GIFs under ~5 MB or host them in a `gh-pages`/release asset rather than
the repo. Every README image needs alt text.

---

## 8. Stretch / nice-to-have

- [ ] `pre-commit` with `ruff` + `black`. CI already runs flake8 with `--exit-zero`, i.e. it
      reports and ignores. Either enforce or drop the pretense.
- [ ] Type hints on the public API (`BPReader`, `NatureRun`, `NRLoader` are already dataclass-ish
      and would take them cleanly).
- [ ] A Colab/Binder notebook that renders **one** figure from the small caches
      (`sigma_patm_std_2012.nc` is 816 KB, `ib_ctrl_freqs.nc` is 12 KB). "Run it in your
      browser, no install" is a strong README button and needs almost nothing.
- [ ] GitHub release tagged to the accepted paper, wired to the Zenodo DOI.
- [ ] Repo social preview image + topics/tags so it looks intentional when shared.

---

## Suggested order

The dependency structure matters more than the numbering above:

0. ~~**Tag `v1.0-paper-submitted`.**~~ ✅ done (`1a7a1b4`, tagged locally, not yet pushed).
1. ~~**§2 — fix the two failing tests.**~~ ✅ done (`49cd5a5`, 2 passed). Prints and CI still open.
2. **§5b — get the namelists and code mods off `/scratch` onto `/work2`.** It is ~550 KB,
   it is what the paper already promises, and `/work2` (Stockyard) is not purged. The only
   item here with a deadline imposed by someone else's policy.
2b. **§4b — decouple the imports** (`__init__.py`, `ecco_v4_py`, `asteoptim`), then build the
   extraction-only env on pfe. Unblocks running `gen_*` next to the data, which retires the
   purge problem permanently rather than managing it.
3. **§1 — hygiene and triage.** Mostly deletion and `git add`. Makes everything after easier
   to reason about.
4. **§3/§4 — env + paths.** Unblocks Docker and Tier 0.
5. **§5c — reorganization.** After paths, before docs.
6. **§5 — the manifest and the driver.** The real engineering.
7. **§2 (rest) — logging, broader tests, green CI.**
8. **§6/§7 — README, gallery, hero image.** Do this *last*, when the claims it makes are true.

---

## Risks to keep in view

- **Do not refactor the figures out from under the manuscript.** It is in review; reviewers may
  ask for a re-render. The `v1.0-paper-submitted` tag is the insurance policy, but also prefer
  additive changes (add a driver, add a path resolver with old defaults intact) over rewrites
  until the paper is accepted.
- **Matplotlib version fidelity.** Per `STATUS.md`, figure correctness depends on 3.4.3-era
  behavior and explicit PDF post-processing. A "let's modernize the deps" pass could silently
  degrade published figures. Pin, comment, and visually diff if you ever bump.
- **`/scratch` purge.** See §5b. The single irreversible risk in this document; everything
  else here is work that can be done later at the same cost.
- **Scope.** Every item here is optional except the tier framing and the green CI. A repo with
  a clear README, passing tests, and one great animation beats a repo with a half-finished
  docs site.
- **Don't oversell.** The README should say plainly that Tiers 1–2 need HPC-scale inputs. A
  reader who discovers that themselves after a failed `docker run` trusts nothing else on the
  page; a reader who was told up front reads the rest as credible.
