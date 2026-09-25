# Model provenance (ROADMAP.md §5b)

Rescued from pfe (`/nobackupp27/mgoldbe1/MITgcm_c68v/mysetups/aste_270x450x180/osses/`,
2026-09-24), the system-of-record for the paper's runs. TACC's `/scratch` and `/work` copies
referenced throughout `smartosse/figures/STATUS.md` are periodic copies of this tree, not the
original.

MITgcm version: **checkpoint68v**, upstream commit `285cda8c7` — `/nobackupp27/mgoldbe1/MITgcm_c68v`
is itself a git clone at that commit/tag, so `git clone https://github.com/MITgcm/MITgcm && git
checkout 285cda8c7` reproduces the source exactly.

## `jobs/`

The PBS job-submission scripts (`script_*.bash`) that launch the runs the *currently tracked*
figure/cache code actually reads, plus `run_logic.sh` (a shared hang-detection wrapper around
`mpiexec` that every script sources — watches for a stall on the `dyG` log line and
kills/restarts).

**Curated down from the 16 scripts originally rescued from pfe**, 2026-09-24: grepped every
tracked `smartosse/figures/*.py` and `gen_*.py` for the `runc68v_*` run-directory strings they
actually open, then kept only the scripts whose `rundir=` line — active *or* commented out —
produces one of those names. Several of these scripts are hand-edited, re-submitted templates
(multiple `rundir=` lines, only one uncommented at a time), so a script whose *current* active
line isn't referenced can still be the right generator for a referenced run under an earlier
edit — that's why some entries below list a run the script doesn't currently produce.

| script | referenced run(s) it can produce | currently active `rundir` |
|---|---|---|
| `script_ib.bash` | `..._ib_freq2` | same (active) |
| `script_partialcables_jra_std.bash` | `..._partialcables_jraspread` (commented), `..._partialcables_jrastd_daytoday` | `..._jrastd_daytoday` |
| `script_spacing.bash` | `..._partialcables_jraspread` (commented), `..._partialcables_jraspread_spacing` | `..._jraspread_spacing` |
| `script_year2012.bash` | `..._gracellc4320_sc_spread` | same (active) |
| `script_year2012_grace.bash` | `..._gracellc4320_spread` (commented) | `..._gracellc4320_stdold` |
| `script_year2012_stamp3.bash` | `..._noapress` (commented) | `..._gracellc4320_sc_may2026` |

10 scripts removed as not generating anything the current figure set reads: `script_daily.bash`,
`script_daily_coldstarttrue.bash`, `script_ib_apr52025.bash` (superseded by `script_ib.bash`),
`script_partialcables.bash` (bare `_partialcables`, confusingly similar name to
`script_partialcables_jra_std.bash` but a different, unreferenced run — only 4 of 5 regions,
missing `fullnatl`), `script_partialcables_jra_std_nopatm.bash`, `script_subgyre.bash`,
`script_subgyre_2mo.bash`, `script_test_ctrl_gen_rec.bash`, `script_uv0.bash`,
`script_uvwind.bash`. Still recoverable from pfe (`git log` this commit, or the pfe source tree
directly) if a reason to want them back turns up.

One reference not resolved either way: `fig8_smart_grace_mo_skill.py` also reads
`..._gracellc4320_sc/2012/` (older `2012/` not `201201/` naming) — no script in the original 16
produces that exact name, active or commented. Per `STATUS.md`, that run's `m_bpday` data is
already purged (only `.meta` survives), so it's moot for regenerating it either way, but the
generating script (if it still exists anywhere) hasn't been found.

Representative resource request (`script_partialcables_jra_std.bash`): `#PBS -l
select=15:ncpus=40:model=sky_ele`, `walltime=10:00:00`, `nprocs=580`, tile decomposition
`snx=18 sny=18` (the `18x18x580` `data.exch2` variant). Not yet confirmed whether every
remaining script uses the same tile decomposition — check each before assuming.

## `optim/`

This is **ECCO's `optim_m1qn3`** — the off-line large-scale optimization driver that wraps the
M1QN3 quasi-Newton solver (see the `Makefile`'s own header: "Makefile for the off-line large
scale optimization with m1qn3") and steps the adjoint iterations between MITgcm forward/adjoint
runs, reading/writing `ecco_ctrl_MIT_CE_000.optNNNN` control vectors. Not to be confused with
`smartuq`'s unrelated `omp`/greedy sensor-selection optimization, or with MITgcm's own `data.ctrl`
namelist (same filename, different file — see `namelists/` above).

**Down to a single template**, 2026-09-24 (Matt's call): pfe had six near-identical `OPTIM*/`
directories, one per experiment family (`OPTIM`, `OPTIM_daily`, `OPTIM_daily_coldstarttrue`,
`OPTIM_DEBUG`, `OPTIM_fullyear`, `OPTIM_subgyre`). Checked byte-for-byte: `data.ctrl`,
`reset.bash`, and `Makefile` were **identical across all six** (same md5sum). `data.optim` only
ever differed in `optimcycle` (which iteration) and `fmin` (that iteration's cost value) — and
every kept `jobs/` script *regenerates* `data.optim` itself at each iteration via a `mv data.optim
data.optim_bk; cat > data.optim <<EOF ... EOF` heredoc with `numiter=10, nupdate=4` hardcoded and
`coldstart` substituted from a shell variable — so the per-family copies weren't six different
configurations, they were six stale snapshots of a template already fully visible in `jobs/`.
One `data.optim` kept here as an illustrative rendered example (from the old `OPTIM/` family);
its `fmin`/`optimcycle` values are specific to that snapshot and not meaningful on their own —
read the heredoc in `jobs/` for what actually varies.

**Deliberately excluded**, same reasoning as before (pruned within each family before the
single-template consolidation):

1. *Too big to commit*: the per-iteration state binaries that lived alongside this config on
   pfe — `ecco_ctrl_MIT_CE_000.optNNNN`, `ecco_cost_MIT_CE_000.optNNNN`, `OPWARM.optNNNN`
   (hundreds of MB to 8 GB *each*) — and the compiled `optim.x`/`optim_debug.x` executables
   (rebuildable from this config + `code_froman/` with the compiler/flags in `genmake.log`, not
   committed as binaries). Each pfe `OPTIM*/` directory was 3–70 GB in total.
2. *Run-instance operational artifacts, not configuration*: `costfunctionNNNN`,
   `m1qn3_output.txt`/`optim.out`/`optim_c68v.out`/`output_optim_itNNNN.txt`/`stdout` (solver/run
   logs), `data.optim_bk`, and small `OPWARM.optNNNN` stubs. `OPTIM/goldberg_optim_memory_error/`
   (a nested debug-incident copy of several of the same filenames) was also left out.

All of the above still recoverable from git history (`2b94375`, the per-family pruning commit;
this commit, the consolidation) or the pfe source tree if ever wanted back.

## `code/froman/`

The `code_froman/` code modifications (57 `.F`/`.h` files + `packages.conf`, 543 KB) from the
build tree, `.../MITgcm_c68v/mysetups/aste_270x450x180/osses/code_froman/`. All 6 kept `jobs/`
scripts use `whichexp="_froman"`, i.e. this one code directory, so no other `code_*` variant
(`code_froman_fwd`, `code_froman_year2012`, `code_mon`, `code_phibot*`, `code_c68v`,
`code_xx_clean`) was needed.

## `namelists/`

**Time-sensitive finding, 2026-09-24**: each run root has a `cleanup.bash` that deletes every
namelist file (`data`, `data.pkg`, `data.exf`, `data.ecco`, plain `data.ctrl`, …) from `iter*/`
directories to save space, keeping only files matching `*xx*`/`*bp*`/`costfunction*`/
`STDOUT.0000`. **It had already been run on `runc68v_froman_partialcables_jraspread`** — the
single most-referenced run (fig5, fig6, fig10, `gen_gate_caches`, figD1) — before this session:
4 of its 5 regions (`fullnatl`, `labsea`, `newfoundland`, `northsea`) had already lost their
namelists; only `subgyre` still had a complete set. The other 6 referenced run families were
checked and still have theirs intact (not yet pulled into git — see below).

`namelists/partialcables_jraspread/` is organized `base/` (48 files, 272 KB — everything that's
identical across all 5 regions: `data`, `data.pkg`, `data.exf`, `data.diagnostics`, `data.exch2`
variants, etc., taken from `subgyre`, the surviving region) plus one directory per region
(`fullnatl/`, `labsea/`, `newfoundland/`, `northsea/`, `subgyre/`) holding only the two files
that actually vary: `data.ctrl` (which `xx_gentim2d_weight(8)` — i.e. which atmospheric-pressure
prior — is active) and `data.ecco` (the `gencost_datafile(1)` cable/sensor identifier, e.g.
`..._64sensors_labsea`).

**How the 4 cleaned regions were reconstructed, not just copied** — two different techniques,
chosen because `STDOUT.0000` survives cleanup and MITgcm echoes every namelist it reads into it
(prefixed `(PID.TID 0000.0001) >`):

- `data.ctrl`: the candidate-value pool (`data.ctrl_dailyxx_multgen*`) also survives cleanup (it
  matches the `*xx*` keep-rule) — these are the same files the job scripts `cp` into place as
  `data.ctrl` at submission time. Confirmed via `STDOUT.0000` which one was actually active in
  each region (all 5 regions turned out to use `data.ctrl_dailyxx_multgen`, i.e. the
  `wApressure_ASTE270_jra55_jra3q_era_spread.bin` prior — consistent with the run family being
  named `jraspread`), then copied that exact surviving file — not hand-transcribed from STDOUT.
- `data.ecco`: no candidate pool survives, so this one *is* reconstructed — `subgyre`'s real
  `data.ecco` as a template, with only the `gencost_datafile(1)` line substituted to match what
  `STDOUT.0000` shows for that region (verified this is the *only* line that differs, by diffing
  the full `ECCO_GENCOST_NML` block STDOUT echoes for all 5 regions before trusting the
  template-substitution approach). Sensor counts (`142/64/27/41` sensors for
  `fullnatl/labsea/newfoundland/northsea`) came from `STDOUT.0000` directly, not assumed.

### The other 6 run families

All confirmed intact on pfe (no `cleanup.bash` damage) except one — pulled straight, same
base+delta pattern where more than one variant exists:

- **`ib_freq2/`** — the inverted-barometer control-frequency sweep (fig11), `base/` (everything
  shared) + one dir per frequency (`24hr/` … `96hr/`, matching fig11's `HOURS = (24, 36, 48, 60,
  72, 84, 96)` — `240hr` and `BAD120hrBAD` exist on pfe but aren't read by any tracked figure, so
  weren't pulled) holding just `data.ctrl`, whose only per-frequency difference is
  `xx_gentim2d_period(8)` (the sweep's actual independent variable, in seconds:
  `86400/129600/172800/216000/259200/302400/345600`). Verified `data.ecco` and everything else
  are byte-identical (single md5sum) across all 8 frequency dirs before trusting this split.
- **`partialcables_jraspread_spacing/`** (figD1) — **also hit by `cleanup.bash`**, same
  reconstruction as `partialcables_jraspread` above (no surviving region here at all, so `base/`
  reuses `partialcables_jraspread/subgyre`'s surviving set — verified via `STDOUT.0000`'s
  `PACKAGES`/`PARM01` echo that the shared domain config really is identical, since nothing here
  survived to diff directly). `70km/`, `140km/`, `210km/` each hold a reconstructed `data.ctrl`
  (same `data.ctrl_dailyxx_multgen`/spread-prior pattern as `jraspread`) and `data.ecco`
  (`gencost_datafile(1)` = `..._{spacing}_{157,106,71}sensors_fullnatl`, sensor counts from
  `STDOUT.0000`, matching `STATUS.md`'s own `210km_71sensors_fullnatl` naming).
- **`partialcables_jrastd_daytoday/`** (fig9/`gen_appendixB_skill_cache`'s `REGIONS = ['labsea',
  'subgyre', 'northsea', 'newfoundland']`) — **correction, same session**: first pass wrongly
  pulled a bare `fullnatl/` directory that turned out to be a different, much smaller (1
  iteration vs. 21), unrelated run — this run family exists on pfe in *two* directory layouts,
  a bare one (`.../jrastd_daytoday/fullnatl/`) and the real one under `201201/` that the code
  actually reads (`.../jrastd_daytoday/201201/<region>/`), and the first pass didn't check for
  the second. The real one **was also hit by `cleanup.bash`**, on all 4 regions — reconstructed
  the same way as `jraspread`/`jraspread_spacing` (base reused from `jraspread/subgyre`, per-region
  `data.ctrl` from the surviving `data.ctrl_dailyxx_multgen_jrastd_daytoday` variant — the
  day-to-day-std prior, `wApressure_jra2012_daytoday_std_Pa.bin`, confirmed active in all 4 via
  `STDOUT.0000` — and `data.ecco` reconstructed from the same template, sensor counts
  64/25/41/27 for labsea/subgyre/northsea/newfoundland from `STDOUT.0000`).
- **`gracellc4320_sc_spread/fullnatl/`**, **`gracellc4320_spread/fullnatl/`** — each genuinely a
  single region (no second layout to miss), namelists intact, straight copies (51–52 files each),
  no reconstruction or base/delta split needed.

`model/namelists/` is 2.0 MB total across all 7 run families.

## First real end-to-end smoke test, 2026-09-24: `gen_gate_caches.py` on pfe

Matt's stated bar for "the package is ready": load real data and regenerate a real
cache, on pfe, using what's in this repo. First attempt, `python -m
smartosse.figures.gen_gate_caches jraspread` against the real
`partialcables_jraspread/201201/labsea/` data (using `smartosse.paths` for
`RUN_DIR`/`GRID_DIR` for the first time — see below) — found and fixed three real
bugs, all xgcm API drift (this repo's xgcm pin predates 0.8; the installed
`environment-extract.yml` version is 0.10.1):

- `smartosse/llc_grid.py`: `xgcm.Grid(..., periodic=False)` → removed, needs
  `padding='fill'`; `grid.interp_2d_vector(..., boundary='fill')` → renamed,
  needs `padding='fill'`.
- `smartosse/osse.py` (`ForecastModel._load_fm_fwflx`) and
  `smartosse/figures/gen_gate_caches.py` (`advfw_staggered`): same rename,
  `grid.interp(..., boundary='extend')` → `padding='extend'`.

Also fixed as part of the same pass: `gen_gate_caches.py`'s `RUN_DIR`/`GRID_DIR`
and `gen_appendixB_skill_cache.py`'s `RUN_DIR_ROOT_{STD,SPREAD}` now resolve via
`smartosse.paths` (`run_root()`/`grid_dir()`) instead of hardcoded
`/scratch/08381/.../work/08381/...` TACC paths — the first real use of the §4
resolver outside its own tests. Confirmed `paths.grid_dir()`'s pfe guess
(`GRID_froman/`, flagged uncertain when written) is in fact correct: it loads
and produces the expected 270×270×50×6-tile ASTE dims. `NR_BT_DIR` (nature run,
`gen_appendixB_skill_cache.py`) is still hardcoded/TACC-only — deferred with the
rest of the nature-run work.

**With all of that fixed, the run got substantially further** — grid load (0.9s),
opened real `trsp_3d_set1`/`state_3d_set1` binaries (12.9s), computed the first
iteration's `ADV_fw` — before being **OOM-killed by the login node's per-session
memory cgroup** at ~4.8 GB RSS partway through the second iteration (confirmed via
`dmesg`: `oom-kill:constraint=CONSTRAINT_MEMCG ... Killed process ... (python)`).
This is not a code bug — the same computation is what every `model/jobs/` PBS
script already requests real compute-node resources for (`select=15:ncpus=40`,
etc.); running it interactively on a pfe login node (`pfe20`) hits that node's own
resource policy, not a package limitation. Not yet re-attempted through an actual
PBS job/interactive compute allocation — that's the natural next step toward the
full regenerate-caches-and-replot bar, but submitting one wasn't done unprompted
since it spends real queue allocation.

## Still needed (not done yet)

- The build recipe is only partially captured: compiler (`ifort 19.1.3.304`) and MPI (HPE MPT
  2.30) versions are known from `genmake.log`, but the optfile name itself hasn't been pinned
  down yet.
- Nature-run extraction pipeline and llc4320 handling — deferred, needs manual intervention
  (Matt, 2026-09-24).
