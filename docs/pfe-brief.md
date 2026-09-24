# Working brief: the pfe side

Companion to ROADMAP.md §4b. Everything here is about **pfe** (NASA), which is where
the OSSE runs execute and where the model output actually lives. Analysis currently
happens at TACC because the pfe Python environment is broken.

## Why this matters

Today, bulk run output is copied pfe → Stampede3 `/scratch`, and the extraction step
(`gen_*.py` → `.nc` caches) runs at the TACC end. Stampede3 purges scratch, so those
copies evaporate periodically.

If extraction instead ran **on pfe, next to the data**, only the ~180 MB of `.nc`
caches would ever cross the wire — onto `/work2` (Stockyard), which is shared across
TACC systems and is **not** purged. The purge problem disappears rather than being
managed, and the transfer shrinks by orders of magnitude.

```
pfe  ──────────────────────────►  TACC /work2  ──────────►  anywhere
run output          gen_*.py      .nc caches      make_fig      figures
(TB, stays put)   (extraction)   (~180 MB)       (plotting)
                   needs: numpy, xarray,          needs: + cartopy,
                   pandas, xmitgcm, netcdf4       matplotlib, LaTeX
```

## Measured facts that shape the pfe env

Verified on Stampede3 against the `esmpy_3.10` env, 2026-09-24:

- The cache builders (`gen_gate_caches`, `gen_appendixB_skill_cache`,
  `gen_patm_uncertainty_fields`, `gen_patm_daytoday_weight_Pa`) import only
  numpy / xarray / pandas / xmitgcm / ecco_v4_py. **They never plot.**
- `ecco_v4_py.ecco_utils` pulls `cartopy, matplotlib, shapely, pyproj, xgcm, scipy`
  — for exactly two functions, `get_llc_grid` and `UEVNfromUXVY`.
- `import smartosse.bp` pulls cartopy and matplotlib too, via the `from .plot import *`
  chain in `smartosse/__init__.py`.
- `asteoptim` is imported by `dataset.py`, `osse.py`, `wind_bp_fw.py`, `slope_cable.py`
  and declared in neither `setup.py` nor `environment.yml`.

So cartopy — the hardest thing to install anywhere, and the most likely thing broken on
pfe — is needed only for plotting, which pfe should never do. Three decoupling tasks in
ROADMAP.md §4b remove it from the extraction path.

## The session prompt

Use this when starting a Claude session on pfe. It is deliberately framed around
*diagnosis before prescription*, and around the small env rather than repairing the
old one.

```
I need a working Python environment on pfe for a narrow purpose, and I'd
rather you diagnose before prescribing.

GOAL: run the data-extraction half of /nobackup/mgoldbe1/smartosse next to
the model output that lives on this machine. That means numpy, xarray,
pandas, xmitgcm, netcdf4, dask. It explicitly does NOT need cartopy,
matplotlib, or LaTeX -- all plotting happens elsewhere. If cartopy is what's
broken, that is good news, not a problem to solve.

CURRENT STATE: `source activate esmpy_3.10` works but takes forever. That
env was built years ago against a machine that has since changed
substantially. I don't care about preserving it -- if starting fresh with a
new miniforge/micromamba install is faster and cleaner, do that and say so.

PLEASE DO, IN ORDER:
1. Measure before changing anything. Time the activation. Find out WHERE it
   goes: shell rc / conda init hooks, the conda solver, or filesystem
   metadata latency. Report the actual breakdown.
2. Check which filesystem the env lives on and what that filesystem is
   (Lustre? NFS? home vs /nobackup?), and how many files the env contains.
   A conda env of ~100k small files on a shared parallel filesystem is a
   known pathology -- I want to know if that's what this is.
3. Check whether we're on a login node and whether outbound network access
   works (proxy needed?), before assuming any install will succeed.
4. THEN recommend: repair, or rebuild small. Tell me which and why.
5. Build whatever you recommend, and pin what you install.

SUCCESS CRITERION:
  time python -c "import numpy, xarray, pandas, xmitgcm, netCDF4, dask; print('ok')"
completes in a couple of seconds, from a cold shell, reproducibly. Then
write the recipe to environment-extract.yml in the repo so it's rebuildable.

SECOND TASK, once that works: inventory what exists ONLY on this machine and
nowhere else -- the job submission scripts, the nature-run extraction
pipeline, the llc4320 handling, and the ECCO `optim` driver settings for the
adjoint iterations. Don't move anything yet; just list what's there, where,
and how big.
```

### Why it is written that way

| Choice | Reason |
|---|---|
| Names the goal, not the symptom | "Make activation faster" invites repairing a 40-package env you do not want. The goal is a small env; slowness is a clue, not the task. |
| Lists the packages, and the explicit NOs | Without this, Claude will reasonably assume you want your old env back, cartopy and all. |
| "If cartopy is broken, that is good news" | Pre-empts hours spent fixing the one dependency that should not be there. |
| Measure first, in numbered order | Slow conda activation has at least four unrelated causes. Prescribing before measuring picks one at random. |
| Asks about the filesystem explicitly | A conda env of ~100k small files on Lustre is the single most likely cause, and it is invisible unless you look. |
| Asks about login node / network | NAS network access is restricted enough that "just conda install" can fail in a confusing way. Better to know up front. |
| Concrete success criterion | "Faster" is unfalsifiable. A timed import of the exact six packages is not. |
| Asks for `environment-extract.yml` | Makes the result reproducible instead of a one-off fix that rots again in two years. |
| Second task is inventory, not migration | Moving files is a decision; listing them is not. Get the list first, decide at leisure. |

## What to bring back from pfe

See ROADMAP.md §5b for the full provenance list. Known to be already on TACC (so **not**
needed from pfe): MITgcm checkpoint68v source (`285cda8c7`), the `code_froman/` code
modifications, and the 41-file namelist sets.

### Inventory, 2026-09-24 (list only — nothing copied yet)

Found the pfe system-of-record: `/nobackupp27/mgoldbe1/MITgcm_c68v` is itself a git clone
at `285cda8c7` / tag `checkpoint68v` — matches ROADMAP §5b exactly, confirming the TACC
copy really is a copy. Run tree: `mysetups/aste_270x450x180/osses/` (**127 GB** total —
do not `git add` this wholesale).

- [x] **Job submission scripts** — found: 16 `script_*.bash` files directly under `osses/`
      (13–14 KB each, ~205 KB total — `script_partialcables.bash`, `script_partialcables_
      jra_std.bash`, `script_subgyre.bash`, `script_daily.bash`, `script_year2012*.bash`,
      `script_spacing.bash`, `script_ib*.bash`, `script_uv0.bash`/`script_uvwind.bash`,
      `script_test_ctrl_gen_rec.bash`), naming matches the `runc68v_froman_*` experiment
      names used throughout `STATUS.md`. Each is a PBS script; representative header
      (`script_partialcables.bash`): `#PBS -l select=15:ncpus=40:model=sky_ele`,
      `walltime=10:00:00`, `nprocs=580`, `snx=18 sny=18` (tile decomposition — matches the
      `18x18x580` `data.exch2` variant ROADMAP §5b already flagged as needing identification).
      All 16 source a shared `run_logic.sh` (hang-detection wrapper around `mpiexec` — checks
      for a stall on `dyG` and kills/restarts). **Copied**, this session — see `model/jobs/`
      and `model/README.md`.
- [ ] Nature-run extraction pipeline — **deprioritized, manual intervention needed** (per
      Matt, 2026-09-24). Not inventoried.
- [ ] llc4320 handling — **deprioritized, manual intervention needed** (same). Not inventoried.
- [x] **ECCO `optim` driver configuration** — found: `OPTIM/`, `OPTIM_daily/`,
      `OPTIM_daily_coldstarttrue/`, `OPTIM_DEBUG/`, `OPTIM_fullyear/`, `OPTIM_subgyre/`
      (6 variants, one per experiment family, 3–70 GB each). The actual config is tiny and
      mixed in with huge per-iteration state dumps: `data.optim`, `data.ctrl`, `Makefile`,
      `optim.x` (the m1qn3-linked binary), `reset.bash` are all <10 KB each; the bulk of each
      directory's size is `ecco_ctrl_MIT_CE_000.optNNNN` / `OPWARM.optNNNN` per-iteration
      pickup/control-vector binaries (hundreds of MB–8 GB *each*) — **not brought back**,
      only the small config files. **Copied**, this session — see `model/optim/` and
      `model/README.md` for the directory-name mapping. `optim.x`/`optim_debug.x` (the
      compiled binaries) also deliberately excluded, rebuildable from `genmake.log`'s
      compiler/flags + `code_froman/` (not yet pulled).
- [x] **Build recipe, partial** — `build_froman/genmake.log` + `taf_ad.log` present
      (compiler: `ifort (IFORT) 19.1.3.304`, flags include `-convert big_endian
      -assume byterecl ... -axCORE-AVX2 -xSSE4.2 -traceback -ftz`, MPI: HPE MPT 2.30).
      **Optfile name itself not pinned down yet** — genmake.log doesn't echo it verbatim in
      the header; would need a closer read of the log or the actual `genmake2` command used.
      `data.exch2` present under `input_froman/`, `input_phibot/`, `input_phibot_daily/`,
      `input_ib/`, `input_labsea_daily/` (one per experiment family, not yet diffed against
      each other or against TACC's copies).
