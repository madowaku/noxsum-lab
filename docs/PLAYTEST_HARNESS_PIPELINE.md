# NOXSUM Lab -> Playtest Harness

The lab can now emit the exact default file consumed by the NOXSUM Playtest Harness.

## Fresh 10,000-candidate run

From the noxsum-lab repository:

```powershell
noxsum-lab playtest
```

This performs:

1. mine 10,000 exact-unique candidates
2. D4 symmetry dedupe
3. FLOW/AHA analysis and ranking
4. blind FLOW20 + AHA20 selection
5. write `exports/playtest_current.json`
6. write the hidden audit pack to `playtests/current/`

The exported game stages include a hidden `source_id` so the NOXSUM Harness can save provenance with human ratings. The playtest UI must not display it.

Then, from the shadow-sum repository:

```powershell
.\tools\playtest.ps1
```

The Harness validates and copies the export, then launches the current NOXSUM playtest screen.

## Reuse an existing mining manifest

```powershell
noxsum-lab playtest --input generated/mining_v0_2.json
```

## Custom seed / pool size

```powershell
noxsum-lab playtest --seed 20260926 --count 10000
```

## Contract

- Product Grant36 data is never modified.
- Public blind stages are PT-001 style IDs.
- FLOW/AHA bucket, rank, score, and audit metadata stay out of the game-facing export.
- `source_id` is retained for joining human results back to generator candidates.
- Hidden answer keys and selection audits live under `playtests/current/`.
