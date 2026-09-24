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

Likely to exist only on pfe:

- [ ] Job submission scripts (current versions) → `model/jobs/`
- [ ] Nature-run extraction pipeline
- [ ] llc4320 handling
- [ ] ECCO `optim` driver configuration for the adjoint iterations
- [ ] The build recipe: optfile, `genmake2` invocation, which `data.exch2` decomposition
      the paper's runs used
