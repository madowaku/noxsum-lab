# NOXSUM Generator v0.2 Mining Summary

Seed: `20260925`

## Result

- Raw exact-unique candidates: **10,000**
- After D4 symmetry dedupe: **9,099**
- Rotation / reflection duplicates removed: **901**
- Full mining runtime on GitHub Actions: about **29 seconds**
- Canonical schema validation: **PASS**

The full JSON / CSV / Markdown output is retained as the GitHub Actions artifact
`noxsum-mining-v0.2-seed-20260925` for the full-mining run.

## Profile balance

Two of the 24 default profiles have no exact-unique target:

- `N2T0P1-TB`: Normal x2 + Plate x1, TOP + BOTTOM
- `N1T1P1-TB`: Normal x1 + Tall x1 + Plate x1, TOP + BOTTOM

Both returned **0 exact-unique candidates**.

This is structurally plausible: with only opposite vertical illumination, Plate orientation cannot always be distinguished strongly enough to determine the physical state uniquely.

The miner redistributes those missing quotas across the remaining 22 viable profiles. The balanced run samples approximately 454-455 raw candidates from each viable profile.

## FLOW top observations

Current top candidates are concentrated in four-light profiles.

Top examples:

| Rank | Candidate | Profile | FLOW | AHA | Witness | Finish survivors |
|---:|---|---|---:|---:|---:|---:|
| 1 | NX-MINE-20260925-08162 | N1T1P1-TLRB | 84.004 | 32.304 | 5 | 3 |
| 2 | NX-MINE-20260925-08402 | N1T1P1-TLRB | 83.295 | 32.304 | 5 | 3 |
| 3 | NX-MINE-20260925-08021 | N1T1P1-TLRB | 82.748 | 32.304 | 5 | 3 |
| 4 | NX-MINE-20260925-04382 | N2T1P0-TLRB | 82.086 | 41.492 | 5 | 3 |
| 5 | NX-MINE-20260925-04110 | N2T1P0-TLRB | 82.086 | 40.697 | 5 | 3 |

The scoring function is finding exactly the pattern it was designed to find:

- a strong foothold
- roughly 4-5 useful reasoning steps
- a final ambiguity of 2-3 states
- then a clean final constraint

This is a plausible Mobile candidate shape, but the four-light concentration must be checked by human playtest rather than treated as proof that four lights are intrinsically better.

## AHA top observations

The top of the current AHA ranking is dominated by **Normal x3 + Tall x1**.

| Rank | Candidate | Profile | AHA | FLOW | Witness | Pair synergy | Late gain |
|---:|---|---|---:|---:|---:|---:|---:|
| 1 | NX-MINE-20260925-05987 | N3T1P0-TLRB | 70.437 | 68.497 | 5 | 4.898 | 16.667 |
| 2 | NX-MINE-20260925-08103 | N1T1P1-TLRB | 67.956 | 49.612 | 8 | 2.052 | 9.000 |
| 3 | NX-MINE-20260925-04547 | N3T1P0-TL | 67.214 | 45.177 | 8 | 1.945 | 9.750 |
| 4 | NX-MINE-20260925-05749 | N3T1P0-TLRB | 66.827 | 56.408 | 7 | 4.898 | 3.000 |
| 5 | NX-MINE-20260925-05979 | N3T1P0-TLRB | 66.827 | 55.445 | 7 | 4.898 | 3.000 |

Candidate `NX-MINE-20260925-05987` is especially interesting because its greedy constraint trace is:

```text
50,600
  ↓ E3=2
4,473
  ↓ B4=2
150
  ↓ B5=1
9
  ↓ A5=0
3
  ↓ C3=2
1
```

This has a strong combination-of-constraints shape rather than a single-cell giveaway.

## Important caveat

FLOW and AHA are **candidate search heuristics**, not puzzle-quality scores.

Next calibration step:

1. Export a small blind playtest pool.
2. Let madowaku classify candidates without seeing the score.
3. For FLOW: record `気持ちいい / 普通 / 捨て`.
4. For AHA: record `自力で解けた / 解説でなるほど / 理不尽`.
5. Compare human labels with v0.2 features.
6. Fit Generator v0.3 scoring to actual NOXSUM taste.

That turns the current hand-written scoring model into a model trained on NOXSUM-specific human judgment.
