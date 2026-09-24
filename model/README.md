# Model provenance (ROADMAP.md §5b)

Rescued from pfe (`/nobackupp27/mgoldbe1/MITgcm_c68v/mysetups/aste_270x450x180/osses/`,
2026-09-24), the system-of-record for the paper's runs. TACC's `/scratch` and `/work` copies
referenced throughout `smartosse/figures/STATUS.md` are periodic copies of this tree, not the
original.

MITgcm version: **checkpoint68v**, upstream commit `285cda8c7` — `/nobackupp27/mgoldbe1/MITgcm_c68v`
is itself a git clone at that commit/tag, so `git clone https://github.com/MITgcm/MITgcm && git
checkout 285cda8c7` reproduces the source exactly.

## `jobs/`

The 16 PBS job-submission scripts (`script_*.bash`) that actually launch the paper's OSSE runs,
copied verbatim from `osses/`, plus `run_logic.sh` (a shared hang-detection wrapper around
`mpiexec` that every script sources — watches for a stall on the `dyG` log line and kills/restarts).
Naming matches the `runc68v_froman_*` / experiment names used throughout `STATUS.md` (partial
cables, `jra_std` variant, subgyre, daily, year2012, spacing sweep, inverted-barometer, etc.).

Representative resource request (`script_partialcables.bash`): `#PBS -l
select=15:ncpus=40:model=sky_ele`, `walltime=10:00:00`, `nprocs=580`, tile decomposition
`snx=18 sny=18` (the `18x18x580` `data.exch2` variant). Not yet confirmed whether every script
in this directory uses the same tile decomposition — check each before assuming.

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
