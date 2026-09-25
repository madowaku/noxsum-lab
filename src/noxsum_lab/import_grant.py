from __future__ import annotations

from collections import Counter
from copy import deepcopy
from typing import Any


def _solution_kind(stage: dict[str, Any], cell_name: str) -> str:
    declared = stage.get("solution_post_types", {})
    if cell_name in declared:
        return str(declared[cell_name])
    if cell_name in set(stage.get("solution_tall", [])):
        return "tall"
    if stage.get("tall"):
        return "tall"
    return "normal"


def _canonical_piece(kind: str) -> tuple[str, str | None]:
    if kind == "normal":
        return "POST", None
    if kind == "tall":
        return "TALL", None
    if kind == "plate_v":
        return "PLATE", "V"
    if kind == "plate_h":
        return "PLATE", "H"
    raise ValueError(f"unknown NOXSUM piece type: {kind}")


def import_grant_stage(
    stage: dict[str, Any],
    *,
    repo: str = "madowaku/shadow-sum",
    ref: str | None = None,
    path: str | None = None,
) -> dict[str, Any]:
    """Convert a current NOXSUM Grant stage into canonical Lab format."""

    source_id = str(stage["id"])
    solution_cells = [str(value) for value in stage.get("solution", [])]

    placements: list[dict[str, Any]] = []
    inventory_counts: Counter[str] = Counter()
    for cell_name in solution_cells:
        kind = _solution_kind(stage, cell_name)
        piece, orientation = _canonical_piece(kind)
        inventory_counts[piece] += 1
        placements.append(
            {
                "piece": piece,
                "cell": cell_name,
                "orientation": orientation,
                "kind": kind,
            }
        )

    mechanics: dict[str, Any] = {}
    mechanic_keys = (
        "installed_lights",
        "fixed_posts",
        "fixed_post_types",
        "free_light_selection",
        "active_light_count",
        "initial_lights",
        "movable_shutter",
        "fixed_shutters",
        "rotatable_plate",
        "fog_cells",
        "normal_posts",
        "tall_posts",
        "plate_posts",
        "tall",
    )
    for key in mechanic_keys:
        if key in stage:
            mechanics[key] = deepcopy(stage[key])

    annotations: dict[str, Any] = {}
    for key in (
        "hints",
        "hint_surface",
        "reasoning_signature",
        "generator_candidate_id",
        "generator_profile",
        "review_only",
    ):
        if key in stage:
            annotations[key] = deepcopy(stage[key])

    metrics: dict[str, Any] = {}
    for key in (
        "expected_states",
        "expected_solutions",
        "shape_required",
        "shape_without_mask_survivors",
        "typed_inventory_exact",
        "tall_required",
        "plate_required",
        "fog_removes_shortcut",
    ):
        if key in stage:
            metrics[key] = deepcopy(stage[key])

    board_mask = None
    if isinstance(stage.get("boardShape"), dict):
        board_mask = deepcopy(stage["boardShape"].get("mask"))

    solution: dict[str, Any] = {
        "placements": placements,
        "lights": list(stage.get("solution_lights", [])),
    }
    if "solution_shutter" in stage:
        solution["shutter"] = int(stage["solution_shutter"])
    if "solution_complete_shadow" in stage:
        solution["complete_shadow"] = deepcopy(stage["solution_complete_shadow"])

    return {
        "schema_version": "noxsum.level.v1",
        "id": source_id,
        "title": str(stage.get("title", source_id)),
        "source": {
            "kind": "imported",
            "source_id": source_id,
            "parent_id": None,
            "repo": repo,
            "ref": ref,
            "path": path,
            "seed": None,
        },
        "board": {
            "width": 5,
            "height": 5,
            "mask": board_mask,
        },
        "inventory": dict(inventory_counts),
        "solution": solution,
        "mechanics": mechanics,
        "observations": deepcopy(stage.get("observations", [])),
        "annotations": annotations,
        "metrics": metrics,
        "curation": {
            "bucket": "UNREVIEWED",
            "target": "NONE",
            "tags": [],
            "notes": "",
        },
    }


def import_grant_pack(
    stages: list[dict[str, Any]],
    *,
    repo: str = "madowaku/shadow-sum",
    ref: str | None = None,
    path: str | None = None,
) -> list[dict[str, Any]]:
    return [
        import_grant_stage(stage, repo=repo, ref=ref, path=path)
        for stage in stages
    ]
