from __future__ import annotations

from collections import Counter
import csv
import hashlib
import itertools
import json
from pathlib import Path
import random
from typing import Any, Iterable

from .analysis import ReasoningIndex, texture_metrics
from .generator import _edge_loss, _piece, _target_dict, generation_stage
from .rules import object_states, packed_shadow, readable_objects, shadow
from .scoring import score_candidate
from .symmetry import canonical_puzzle_signature


DEFAULT_INVENTORIES = (
    (3, 0, 0),
    (4, 0, 0),
    (2, 1, 0),
    (3, 1, 0),
    (2, 0, 1),
    (1, 1, 1),
)

DEFAULT_LIGHT_SETS = (
    ("TOP", "LEFT"),
    ("TOP", "BOTTOM"),
    ("TOP", "LEFT", "RIGHT"),
    ("TOP", "LEFT", "RIGHT", "BOTTOM"),
)


def _stable_seed(seed: int, token: str) -> int:
    digest = hashlib.sha256(f"{seed}:{token}".encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "big")


def _profile_id(inventory: tuple[int, int, int], lights: tuple[str, ...]) -> str:
    normal, tall, plate = inventory
    light_code = "".join(name[0] for name in lights)
    return f"N{normal}T{tall}P{plate}-{light_code}"


def _build_level(
    *,
    seed: int,
    serial: int,
    profile_id: str,
    objects,
    values: tuple[int, ...],
    lights: tuple[str, ...],
    inventory: tuple[int, int, int],
    search_space: int,
    metrics: dict[str, Any],
    reasoning: dict[str, Any],
    flow_score: float,
    aha_score: float,
    tags: list[str],
    canonical_hash: str,
) -> dict[str, Any]:
    normal, tall, plate = inventory
    source_id = f"NX-MINE-{seed}-{serial:05d}"

    placements = []
    for item in readable_objects(objects):
        piece, orientation = _piece(item["type"])
        placements.append(
            {
                "piece": piece,
                "cell": item["cell"],
                "orientation": orientation,
                "kind": item["type"],
            }
        )

    inventory_map: dict[str, int] = {}
    if normal:
        inventory_map["POST"] = normal
    if tall:
        inventory_map["TALL"] = tall
    if plate:
        inventory_map["PLATE"] = plate

    scalar_reasoning = {
        key: value
        for key, value in reasoning.items()
        if not isinstance(value, (list, dict))
    }

    return {
        "schema_version": "noxsum.level.v1",
        "id": source_id,
        "title": source_id,
        "source": {
            "kind": "generated",
            "source_id": source_id,
            "parent_id": None,
            "repo": "madowaku/noxsum-lab",
            "ref": None,
            "path": None,
            "seed": seed,
        },
        "board": {
            "width": 5,
            "height": 5,
            "mask": None,
        },
        "inventory": inventory_map,
        "solution": {
            "placements": placements,
            "lights": list(lights),
        },
        "mechanics": {
            "installed_lights": ["TOP", "LEFT", "RIGHT", "BOTTOM"],
            "fixed_lights": list(lights),
            "free_light_selection": False,
            "movable_shutter": False,
        },
        "observations": [
            {
                "id": "A",
                "active_lights": list(lights),
                "target": _target_dict(values),
            }
        ],
        "annotations": {
            "profile_id": profile_id,
            "canonical_hash": canonical_hash,
            "best_pair_cells": reasoning["best_pair_cells"],
            "witness_trace": reasoning["witness_trace"],
        },
        "metrics": {
            "search_space": search_space,
            "exact_survivors": 1,
            **metrics,
            **scalar_reasoning,
            "edge_loss": _edge_loss(objects, lights),
            "flow_score": flow_score,
            "aha_score": aha_score,
        },
        "curation": {
            "bucket": "UNREVIEWED",
            "target": "NONE",
            "tags": tags,
            "notes": "",
        },
    }


def _prepare_profile(
    inventory: tuple[int, int, int],
    lights: tuple[str, ...],
) -> tuple[list[Any], list[tuple[int, ...]], list[int]]:
    normal, tall, plate = inventory
    template = generation_stage(
        normal=normal,
        tall=tall,
        plate=plate,
        lights=lights,
    )

    worlds = list(object_states(template))
    targets = [shadow(world, lights) for world in worlds]
    packed = [packed_shadow(world, lights, None) for world in worlds]
    counts = Counter(packed)
    unique_indices = [
        index for index, signature in enumerate(packed)
        if counts[signature] == 1
    ]
    return worlds, targets, unique_indices


def _candidate_capacity(
    inventory: tuple[int, int, int],
    lights: tuple[str, ...],
) -> int:
    _, _, unique = _prepare_profile(inventory, lights)
    return len(unique)


def mine_candidates(
    *,
    seed: int,
    count: int = 10_000,
    inventories: Iterable[tuple[int, int, int]] = DEFAULT_INVENTORIES,
    light_sets: Iterable[tuple[str, ...]] = DEFAULT_LIGHT_SETS,
) -> dict[str, Any]:
    if count < 1:
        raise ValueError("count must be at least 1")

    profiles = [
        (inventory, lights)
        for inventory in inventories
        for lights in light_sets
    ]
    if not profiles:
        raise ValueError("no mining profiles")

    per_profile = (count + len(profiles) - 1) // len(profiles)
    raw_records: list[dict[str, Any]] = []
    profile_stats: list[dict[str, Any]] = []
    serial = 0

    for inventory, lights in profiles:
        pid = _profile_id(inventory, lights)
        worlds, targets, unique_indices = _prepare_profile(inventory, lights)
        rng = random.Random(_stable_seed(seed, pid))
        rng.shuffle(unique_indices)

        selected_indices = unique_indices[:per_profile]
        reasoning_index = ReasoningIndex(worlds, targets)

        for world_index in selected_indices:
            serial += 1
            objects = worlds[world_index]
            values = targets[world_index]

            reasoning = reasoning_index.analyze(values)
            texture = texture_metrics(objects, values, lights)
            metrics = {
                **texture,
                "search_space": len(worlds),
            }
            flow_score, aha_score, tags = score_candidate({
                **metrics,
                **reasoning,
            })

            canonical = canonical_puzzle_signature(
                target=values,
                lights=lights,
                inventory=inventory,
            )
            canonical_hash = hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:20]

            raw_records.append(
                {
                    "profile_id": pid,
                    "inventory": inventory,
                    "lights": lights,
                    "objects": objects,
                    "values": values,
                    "metrics": metrics,
                    "reasoning": reasoning,
                    "flow_score": flow_score,
                    "aha_score": aha_score,
                    "tags": tags,
                    "canonical": canonical,
                    "canonical_hash": canonical_hash,
                }
            )

        profile_stats.append(
            {
                "profile_id": pid,
                "inventory": list(inventory),
                "lights": list(lights),
                "search_space": len(worlds),
                "exact_unique_targets": len(unique_indices),
                "sampled": len(selected_indices),
            }
        )

    # If a small profile could not meet its balanced quota, top up
    # deterministically from remaining exact-unique worlds in other profiles.
    if len(raw_records) < count:
        needed = count - len(raw_records)
        for inventory, lights in profiles:
            if needed <= 0:
                break

            pid = _profile_id(inventory, lights)
            worlds, targets, unique_indices = _prepare_profile(inventory, lights)
            rng = random.Random(_stable_seed(seed, pid))
            rng.shuffle(unique_indices)
            start = min(per_profile, len(unique_indices))
            extras = unique_indices[start:start + needed]
            if not extras:
                continue

            reasoning_index = ReasoningIndex(worlds, targets)
            for world_index in extras:
                serial += 1
                objects = worlds[world_index]
                values = targets[world_index]
                reasoning = reasoning_index.analyze(values)
                texture = texture_metrics(objects, values, lights)
                metrics = {**texture, "search_space": len(worlds)}
                flow_score, aha_score, tags = score_candidate({**metrics, **reasoning})
                canonical = canonical_puzzle_signature(
                    target=values,
                    lights=lights,
                    inventory=inventory,
                )
                canonical_hash = hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:20]
                raw_records.append(
                    {
                        "profile_id": pid,
                        "inventory": inventory,
                        "lights": lights,
                        "objects": objects,
                        "values": values,
                        "metrics": metrics,
                        "reasoning": reasoning,
                        "flow_score": flow_score,
                        "aha_score": aha_score,
                        "tags": tags,
                        "canonical": canonical,
                        "canonical_hash": canonical_hash,
                    }
                )
                needed -= 1
                if needed <= 0:
                    break

    raw_records = raw_records[:count]
    if len(raw_records) < count:
        raise ValueError(
            f"profiles produced only {len(raw_records)} raw exact-unique candidates; "
            f"requested {count}"
        )

    # Symmetry dedupe. Keep the stronger representative if multiple raw
    # candidates collapse into one D4 orbit.
    deduped_by_key: dict[str, dict[str, Any]] = {}
    for record in raw_records:
        existing = deduped_by_key.get(record["canonical"])
        if existing is None:
            deduped_by_key[record["canonical"]] = record
            continue

        current_key = (
            max(record["flow_score"], record["aha_score"]),
            record["flow_score"] + record["aha_score"],
            record["profile_id"],
        )
        existing_key = (
            max(existing["flow_score"], existing["aha_score"]),
            existing["flow_score"] + existing["aha_score"],
            existing["profile_id"],
        )
        if current_key > existing_key:
            deduped_by_key[record["canonical"]] = record

    deduped = list(deduped_by_key.values())

    flow_order = sorted(
        range(len(deduped)),
        key=lambda i: (
            -deduped[i]["flow_score"],
            -deduped[i]["aha_score"],
            deduped[i]["canonical_hash"],
        ),
    )
    aha_order = sorted(
        range(len(deduped)),
        key=lambda i: (
            -deduped[i]["aha_score"],
            -deduped[i]["flow_score"],
            deduped[i]["canonical_hash"],
        ),
    )
    flow_rank = {index: rank for rank, index in enumerate(flow_order, 1)}
    aha_rank = {index: rank for rank, index in enumerate(aha_order, 1)}

    levels: list[dict[str, Any]] = []
    for record_index, record in enumerate(deduped):
        output_serial = record_index + 1
        level = _build_level(
            seed=seed,
            serial=output_serial,
            profile_id=record["profile_id"],
            objects=record["objects"],
            values=record["values"],
            lights=record["lights"],
            inventory=record["inventory"],
            search_space=int(record["metrics"]["search_space"]),
            metrics=record["metrics"],
            reasoning=record["reasoning"],
            flow_score=record["flow_score"],
            aha_score=record["aha_score"],
            tags=record["tags"],
            canonical_hash=record["canonical_hash"],
        )
        level["metrics"]["flow_rank"] = flow_rank[record_index]
        level["metrics"]["aha_rank"] = aha_rank[record_index]
        levels.append(level)

    # Sort output by stable ID / canonical hash rather than score. Rankings are
    # fields so the same pool can be sliced independently for Mobile and Steam.
    levels.sort(key=lambda level: level["annotations"]["canonical_hash"])

    return {
        "schema_version": "noxsum.mine.v0.2",
        "seed": seed,
        "requested_raw_candidates": count,
        "raw_candidates": len(raw_records),
        "after_symmetry_dedupe": len(levels),
        "symmetry_duplicates_removed": len(raw_records) - len(levels),
        "profiles": profile_stats,
        "levels": levels,
    }


def ranking_rows(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for level in manifest["levels"]:
        metrics = level["metrics"]
        rows.append(
            {
                "id": level["id"],
                "profile": level["annotations"]["profile_id"],
                "canonical_hash": level["annotations"]["canonical_hash"],
                "flow_rank": metrics["flow_rank"],
                "flow_score": metrics["flow_score"],
                "aha_rank": metrics["aha_rank"],
                "aha_score": metrics["aha_score"],
                "search_space": metrics["search_space"],
                "witness_length": metrics["witness_length"],
                "best_single_survivors": metrics["best_single_survivors"],
                "best_pair_survivors": metrics["best_pair_survivors"],
                "penultimate_survivors": metrics["penultimate_survivors"],
                "pair_synergy_bits": metrics["pair_synergy_bits"],
                "late_max_information_gain": metrics["late_max_information_gain"],
                "overlap_cells": metrics["overlap_cells"],
                "target_entropy": metrics["target_entropy"],
                "tags": ",".join(level["curation"]["tags"]),
            }
        )
    return rows


def write_mining_outputs(
    manifest: dict[str, Any],
    *,
    json_path: Path,
    csv_path: Path,
    report_path: Path | None = None,
    top_n: int = 25,
) -> None:
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    rows = ranking_rows(manifest)
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with csv_path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(sorted(rows, key=lambda row: (row["flow_rank"], row["aha_rank"])))

    if report_path is None:
        return

    by_id = {level["id"]: level for level in manifest["levels"]}
    flow_top = sorted(rows, key=lambda row: row["flow_rank"])[:top_n]
    aha_top = sorted(rows, key=lambda row: row["aha_rank"])[:top_n]

    lines = [
        "# NOXSUM Generator v0.2 mining report",
        "",
        f"- Seed: `{manifest['seed']}`",
        f"- Raw exact-unique candidates: **{manifest['raw_candidates']}**",
        f"- After D4 symmetry dedupe: **{manifest['after_symmetry_dedupe']}**",
        f"- Symmetry duplicates removed: **{manifest['symmetry_duplicates_removed']}**",
        "",
        "## FLOW top",
        "",
        "| Rank | ID | Profile | FLOW | AHA | Witness | Finish survivors | Tags |",
        "|---:|---|---|---:|---:|---:|---:|---|",
    ]

    for row in flow_top:
        lines.append(
            f"| {row['flow_rank']} | {row['id']} | {row['profile']} | "
            f"{row['flow_score']:.3f} | {row['aha_score']:.3f} | "
            f"{row['witness_length']} | {row['penultimate_survivors']} | {row['tags']} |"
        )

    lines += [
        "",
        "## AHA top",
        "",
        "| Rank | ID | Profile | AHA | FLOW | Witness | Pair synergy | Late gain | Tags |",
        "|---:|---|---|---:|---:|---:|---:|---:|---|",
    ]
    for row in aha_top:
        lines.append(
            f"| {row['aha_rank']} | {row['id']} | {row['profile']} | "
            f"{row['aha_score']:.3f} | {row['flow_score']:.3f} | "
            f"{row['witness_length']} | {row['pair_synergy_bits']:.3f} | "
            f"{row['late_max_information_gain']:.3f} | {row['tags']} |"
        )

    lines += [
        "",
        "## Score caveat",
        "",
        "FLOW/AHA are candidate-ranking heuristics, not quality verdicts. "
        "Human playtest remains authoritative. In particular, AHA is designed "
        "to reject pure opacity: a long witness trace can receive a brute-force penalty.",
        "",
    ]

    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines), encoding="utf-8")
