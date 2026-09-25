# `cable_data/` — shipped Tier 0 inputs for Fig. 1

Two small CSVs of global SMART-cable coordinates, both with plain
`Longitude,Latitude` columns. They are **inputs to the figure, not model output**,
so they ship with the package rather than being regenerated:

| file | rows | used as |
|---|---|---|
| `smart_cables_may2024.csv` | 265 | `GLOBAL_CABLE_FILE_REPRESENTATIVE` — the May 2024 representative network |
| `global_total_coord.csv` | 3320 | `GLOBAL_CABLE_FILE_ALL` — all candidate routes, concatenated end to end |
| `partial_cable_coords/labsea_cable_coords.csv` | 64 | SPNA inset, `LS_cable` |
| `partial_cable_coords/northsea_cable_coords.csv` | 41 | SPNA inset, `NS_cable` |
| `partial_cable_coords/newfoundland_cable_coords.csv` | 27 | SPNA inset, `Nfl_cable` |
| `partial_cable_coords/subgyre_cable_coords.csv` | 25 | SPNA inset, `SPG_cable` |

The `partial_cable_coords/` files are headerless with three columns, read as
`(data_variable, Longitude, Latitude)`; only the last two are used. 157 sensors
total. They were originally mirrored from the OSSE run directories on TACC
`/scratch`, which is purged — that is why they are vendored here.

Together these six files (~98 KB) are everything Fig. 1 reads, which is what makes
it a **Tier 0** figure: no model output, no site configuration.

**Provenance:** the two global CSVs copied 2026-09-24 from
`/nobackup/mgoldbe1/cable_data_new/` on pfe
(the same set previously read from `/work2/08381/goldberg/ls6/cable_data_new/` at
TACC). The source directory also holds `FarNorthFiber.csv` and
`smart_aste_latlon.csv`; Fig. 1 does not read either, so they are deliberately
not copied here.

**Why not `figures/data/`?** That directory is gitignored (it holds the large
regenerable `.nc` caches), so anything placed there would not ship. These files
are small, static, and not regenerable from anything in the repo, so they live
here and are declared as `package-data` in `pyproject.toml`.

Note `global_total_coord.csv` concatenates many routes, which is why
`fig1_global_cables.py` carves the Azores loop out by contiguous row block
(`AZORES_ROW_SLICE`) rather than by a lon/lat box alone.
