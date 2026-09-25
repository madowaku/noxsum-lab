from __future__ import annotations

from collections import Counter
from copy import deepcopy
import csv
import json
from pathlib import Path
import random
from typing import Any


BANDS = (
    ("ELITE", 1, 50, 8),
    ("STRONG", 51, 200, 6),
    ("MID", 201, 600, 4),
    ("CONTROL", 601, 1500, 2),
)


def _inventory_key(level: dict[str, Any]) -> tuple[int, int, int]:
    inventory = level.get("inventory", {})
    return (
        int(inventory.get("POST", 0)),
        int(inventory.get("TALL", 0)),
        int(inventory.get("PLATE", 0)),
    )


def _light_key(level: dict[str, Any]) -> str:
    lights = level.get("solution", {}).get("lights", [])
    abbreviations = {
        "TOP": "T",
        "LEFT": "L",
        "RIGHT": "R",
        "BOTTOM": "B",
    }
    return "".join(abbreviations[str(light)] for light in lights)


def _eligible(level: dict[str, Any], bucket: str) -> bool:
    metrics = level["metrics"]
    tags = set(level.get("curation", {}).get("tags", []))

    if "bruteforce_smell" in tags:
        return False

    witness = int(metrics.get("witness_length", 0))
    penultimate = int(metrics.get("penultimate_survivors", 0))

    if bucket == "FLOW":
        return 3 <= witness <= 9 and 2 <= penultimate <= 6

    if bucket == "AHA":
        synergy = float(metrics.get("pair_synergy_bits", 0.0))
        late_gain = float(metrics.get("late_max_information_gain", 0.0))
        return 4 <= witness <= 10 and (synergy >= 1.0 or late_gain >= 4.0)

    raise ValueError(f"unknown bucket: {bucket}")


def _select_bucket(
    levels: list[dict[str, Any]],
    *,
    bucket: str,
    excluded_ids: set[str],
) -> list[dict[str, Any]]:
    rank_field = "flow_rank" if bucket == "FLOW" else "aha_rank"
    profile_counts: Counter[str] = Counter()
    inventory_counts: Counter[tuple[int, int, int]] = Counter()
    light_counts: Counter[str] = Counter()
    selected: list[dict[str, Any]] = []
    selected_ids: set[str] = set()

    for band, low, high, wanted in BANDS:
        candidates = [
            level
            for level in levels
            if low <= int(level["metrics"][rank_field]) <= high
            and level["id"] not in excluded_ids
            and level["id"] not in selected_ids
            and _eligible(level, bucket)
        ]
        candidates.sort(
            key=lambda level: (
                int(level["metrics"][rank_field]),
                str(level.get("annotations", {}).get("canonical_hash", "")),
            )
        )

        picked = 0
        for limits in (
            (2, 5, 8),
            (3, 6, 10),
        ):
            max_profile, max_inventory, max_light = limits
            for level in candidates:
                if level["id"] in selected_ids:
                    continue

                profile = str(level.get("annotations", {}).get("profile_id", ""))
                inventory = _inventory_key(level)
                light = _light_key(level)

                if profile_counts[profile] >= max_profile:
                    continue
                if inventory_counts[inventory] >= max_inventory:
                    continue
                if light_counts[light] >= max_light:
                    continue

                selected.append(
                    {
                        "level": level,
                        "bucket": bucket,
                        "band": band,
                    }
                )
                selected_ids.add(level["id"])
                profile_counts[profile] += 1
                inventory_counts[inventory] += 1
                light_counts[light] += 1
                picked += 1
                if picked >= wanted:
                    break
            if picked >= wanted:
                break

        if picked != wanted:
            raise ValueError(
                f"could not select {wanted} {bucket} candidates in {band}; got {picked}"
            )

    return selected


def _sanitize_level(level: dict[str, Any], public_id: str, ordinal: int) -> dict[str, Any]:
    return {
        "schema_version": "noxsum.level.v1",
        "id": public_id,
        "title": f"BLIND TEST {ordinal:02d}",
        "source": {
            "kind": "generated",
            "source_id": public_id,
            "parent_id": None,
            "repo": "madowaku/noxsum-lab",
            "ref": None,
            "path": None,
            "seed": None,
        },
        "board": deepcopy(level["board"]),
        "inventory": deepcopy(level["inventory"]),
        "solution": deepcopy(level["solution"]),
        "mechanics": deepcopy(level["mechanics"]),
        "observations": deepcopy(level["observations"]),
        "annotations": {
            "blind_pack": "FLOW20_AHA20_v0.1",
        },
        "metrics": {
            "exact_survivors": 1,
        },
        "curation": {
            "bucket": "UNREVIEWED",
            "target": "NONE",
            "tags": [],
            "notes": "",
        },
    }


def _to_game_stage(
    source_level: dict[str, Any],
    *,
    public_id: str,
    ordinal: int,
) -> dict[str, Any]:
    inventory = source_level["inventory"]
    placements = source_level["solution"]["placements"]
    normal = int(inventory.get("POST", 0))
    tall = int(inventory.get("TALL", 0))
    plate = int(inventory.get("PLATE", 0))

    solution_post_types: dict[str, str] = {}
    solution_tall: list[str] = []
    solution_cells: list[str] = []

    for placement in placements:
        cell = str(placement["cell"])
        kind = str(placement.get("kind") or "normal")
        solution_cells.append(cell)
        solution_post_types[cell] = kind
        if kind == "tall":
            solution_tall.append(cell)

    observations = deepcopy(source_level["observations"])
    for observation in observations:
        target = observation.get("target", {})
        observation["target"] = {
            key: int(value)
            for key, value in target.items()
            if int(value) != 0
        }

    stage: dict[str, Any] = {
        "id": public_id,
        "title": f"BLIND TEST {ordinal:02d}",
        "posts": normal + tall + plate,
        "normal_posts": normal,
        "tall_posts": tall,
        "plate_posts": plate,
        "solution": solution_cells,
        "solution_post_types": solution_post_types,
        "installed_lights": list(source_level["solution"].get("lights", [])),
        "observations": observations,
        "expected_states": int(source_level["metrics"]["search_space"]),
        "expected_solutions": 1,
        "typed_inventory_exact": True,
        "review_only": True,
    }
    if tall:
        stage["solution_tall"] = solution_tall
    if plate:
        stage["rotatable_plate"] = True
    return stage


def build_blind_pack(
    manifest: dict[str, Any],
    *,
    shuffle_seed: int = 20260925,
) -> dict[str, Any]:
    levels = list(manifest["levels"])

    flow = _select_bucket(levels, bucket="FLOW", excluded_ids=set())
    flow_ids = {item["level"]["id"] for item in flow}
    aha = _select_bucket(levels, bucket="AHA", excluded_ids=flow_ids)

    rng = random.Random(shuffle_seed)
    flow_pool = flow[:]
    aha_pool = aha[:]
    rng.shuffle(flow_pool)
    rng.shuffle(aha_pool)

    pattern = ["FLOW"] * len(flow_pool) + ["AHA"] * len(aha_pool)
    for _ in range(10_000):
        rng.shuffle(pattern)
        if all(
            not (pattern[index] == pattern[index + 1] == pattern[index + 2])
            for index in range(len(pattern) - 2)
        ):
            break
    else:
        raise RuntimeError("could not create balanced blind sequence")

    queues = {"FLOW": flow_pool, "AHA": aha_pool}
    public_levels: list[dict[str, Any]] = []
    game_stages: list[dict[str, Any]] = []
    answer_key: list[dict[str, Any]] = []

    previous_profile: str | None = None
    for ordinal, bucket in enumerate(pattern, 1):
        pool = queues[bucket]

        choice_index = 0
        if previous_profile is not None:
            for index, item in enumerate(pool):
                profile = str(item["level"]["annotations"].get("profile_id", ""))
                if profile != previous_profile:
                    choice_index = index
                    break

        item = pool.pop(choice_index)
        level = item["level"]
        profile = str(level["annotations"].get("profile_id", ""))
        previous_profile = profile

        public_id = f"PT-{ordinal:03d}"
        public_levels.append(_sanitize_level(level, public_id, ordinal))
        game_stages.append(
            _to_game_stage(level, public_id=public_id, ordinal=ordinal)
        )

        answer_key.append(
            {
                "pt_id": public_id,
                "source_id": level["id"],
                "target_bucket": bucket,
                "calibration_band": item["band"],
                "profile_id": profile,
                "canonical_hash": level["annotations"].get("canonical_hash"),
                "flow_rank": level["metrics"].get("flow_rank"),
                "flow_score": level["metrics"].get("flow_score"),
                "aha_rank": level["metrics"].get("aha_rank"),
                "aha_score": level["metrics"].get("aha_score"),
                "witness_length": level["metrics"].get("witness_length"),
                "penultimate_survivors": level["metrics"].get("penultimate_survivors"),
                "pair_synergy_bits": level["metrics"].get("pair_synergy_bits"),
                "late_max_information_gain": level["metrics"].get(
                    "late_max_information_gain"
                ),
                "solution": deepcopy(level["solution"]),
                "best_pair_cells": deepcopy(
                    level.get("annotations", {}).get("best_pair_cells", [])
                ),
                "witness_trace": deepcopy(
                    level.get("annotations", {}).get("witness_trace", [])
                ),
            }
        )

    return {
        "pack_id": "FLOW20_AHA20_BLIND_v0.1",
        "shuffle_seed": shuffle_seed,
        "selection": {
            "flow": 20,
            "aha": 20,
            "bands": {
                "ELITE": 8,
                "STRONG": 6,
                "MID": 4,
                "CONTROL": 2,
            },
        },
        "public_levels": public_levels,
        "game_stages": game_stages,
        "answer_key": answer_key,
    }


def write_blind_pack(pack: dict[str, Any], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    (output_dir / "blind_pack_canonical.json").write_text(
        json.dumps(pack["public_levels"], ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (output_dir / "blind_pack_game.json").write_text(
        json.dumps(pack["game_stages"], ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (output_dir / "_DO_NOT_OPEN_answer_key.json").write_text(
        json.dumps(pack["answer_key"], ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (output_dir / "blind_pack_game_session_A_01-20.json").write_text(
        json.dumps(pack["game_stages"][:20], ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (output_dir / "blind_pack_game_session_B_21-40.json").write_text(
        json.dumps(pack["game_stages"][20:], ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    reveal_lines = [
        "# DO NOT OPEN BEFORE FIRST RATINGS",
        "",
        "各問題を十分考え、初回評価を記録してから必要な問題だけ見てください。",
        "",
    ]
    audit_lines = [
        "# Selection Audit (DO NOT OPEN BEFORE PLAYTEST)",
        "",
        "This file exposes FLOW/AHA labels and score bands.",
        "",
        "| PT | Bucket | Band | Source | Profile | FLOW rank | FLOW | AHA rank | AHA |",
        "|---|---|---|---|---|---:|---:|---:|---:|",
    ]

    for item in pack["answer_key"]:
        reveal_lines.append(f"## {item['pt_id']}")
        parts: list[str] = []
        for placement in item["solution"]["placements"]:
            kind = str(placement.get("kind") or placement.get("piece"))
            cell = str(placement["cell"])
            orientation = placement.get("orientation")
            if orientation:
                parts.append(f"{kind}@{cell}({orientation})")
            else:
                parts.append(f"{kind}@{cell}")
        reveal_lines.append("- Solution: " + ", ".join(parts))
        reveal_lines.append(
            "- Lights: " + " + ".join(item["solution"].get("lights", []))
        )
        pair = item.get("best_pair_cells", [])
        if pair:
            reveal_lines.append("- Solver attention pair: " + " + ".join(pair))
        trace = item.get("witness_trace", [])
        if trace:
            trace_text = " → ".join(
                f"{step['cell']}={step['value']} "
                f"[{step['before']}→{step['after']}]"
                for step in trace
            )
            reveal_lines.append("- Constraint trace: " + trace_text)
        reveal_lines.append("")

        audit_lines.append(
            f"| {item['pt_id']} | {item['target_bucket']} | "
            f"{item['calibration_band']} | {item['source_id']} | "
            f"{item['profile_id']} | {item['flow_rank']} | "
            f"{float(item['flow_score']):.3f} | {item['aha_rank']} | "
            f"{float(item['aha_score']):.3f} |"
        )

    (output_dir / "_DO_NOT_OPEN_reveal_guide.md").write_text(
        "\n".join(reveal_lines) + "\n",
        encoding="utf-8",
    )
    (output_dir / "_DO_NOT_OPEN_selection_audit.md").write_text(
        "\n".join(audit_lines) + "\n",
        encoding="utf-8",
    )

    with (output_dir / "ratings.csv").open(
        "w", encoding="utf-8", newline=""
    ) as file:
        fieldnames = (
            "pt_id",
            "solved_without_reveal",
            "time_seconds",
            "flow_feel_1_5",
            "aha_1_5",
            "frustration_1_5",
            "want_next_1_5",
            "reveal_reaction",
            "notes",
        )
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        for ordinal in range(1, 41):
            writer.writerow({"pt_id": f"PT-{ordinal:03d}"})

    readme = """# FLOW 20 + AHA 20 Blind Playtest Pack v0.1

40問の出自・ランキング・FLOW/AHA区分を隠した校正用パックです。

Files:
- blind_pack_game.json: 現行NOXSUM形式でプレイするための40問
- blind_pack_canonical.json: Lab canonical形式
- blind_pack_game_session_A_01-20.json: 前半20問
- blind_pack_game_session_B_21-40.json: 後半20問
- ratings.csv: プレイ後に記録する評価表
- _DO_NOT_OPEN_answer_key.json: 機械可読の答え合わせ用
- _DO_NOT_OPEN_reveal_guide.md: 人間向け解答確認
- _DO_NOT_OPEN_selection_audit.md: FLOW/AHA区分と元スコア

Protocol:
1. PT-001から順にプレイする。
2. 解けたら、その時点でratingsへ記録する。
3. 詰まった問題は無理に総当たりせず、十分考えた時点で一度止める。
4. 初回評価を記録してから必要ならanswer keyで解答を見る。
5. 解答を見た場合は reveal_reaction を記録する。

Recommended ratings:
- flow_feel_1_5: 解いていて気持ちよかったか
- aha_1_5: 気づき・見方の変化があったか
- frustration_1_5: 理不尽・総当たり感があったか
- want_next_1_5: 直後にもう一問やりたいか
- reveal_reaction: NA / NARUHODO / FLAT / UNFAIR

40問を一気にやる必要はありません。20問ずつ2セッション程度を推奨します。

スコアは候補探索用の仮説です。人間評価を正解としてv0.3を校正します。
"""
    (output_dir / "README.md").write_text(readme, encoding="utf-8")
