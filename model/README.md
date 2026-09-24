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

The ECCO `optim` driver configuration for each experiment family's adjoint iterations —
`data.optim`, `data.ctrl`, `reset.bash`, `Makefile`, cost-function/output logs. Directory names
map to the pfe source as:

| here | pfe (`osses/`) |
|---|---|
| `base/` | `OPTIM/` |
| `daily/` | `OPTIM_daily/` |
| `daily_coldstarttrue/` | `OPTIM_daily_coldstarttrue/` |
| `debug/` | `OPTIM_DEBUG/` |
| `fullyear/` | `OPTIM_fullyear/` |
| `subgyre/` | `OPTIM_subgyre/` |

**Deliberately excluded**: the per-iteration state binaries that live alongside this config on
pfe — `ecco_ctrl_MIT_CE_000.optNNNN`, `ecco_cost_MIT_CE_000.optNNNN`, `OPWARM.optNNNN` (hundreds
of MB to 8 GB *each*) — and the compiled `optim.x`/`optim_debug.x` executables (rebuildable from
this config + `code_froman/` with the compiler/flags in `genmake.log`, not committed as binaries).
Each pfe `OPTIM*/` directory is 3–70 GB in total; what's here is the <1 MB config slice of it.

`OPTIM/goldberg_optim_memory_error/` (a nested debug-incident copy of several of the same
filenames) was left out — redundant with `base/` and not itself provenance for a paper run.

## Still needed (not done yet)

- `code_froman/` (the ~57 F/h code modifications) and the namelist sets — see ROADMAP.md §5b;
  not pulled from pfe in this pass (this session only did `jobs/` and `optim/`).
- The build recipe is only partially captured: compiler (`ifort 19.1.3.304`) and MPI (HPE MPT
  2.30) versions are known from `genmake.log`, but the optfile name itself hasn't been pinned
  down yet.
- Nature-run extraction pipeline and llc4320 handling — deferred, needs manual intervention
  (Matt, 2026-09-24).
