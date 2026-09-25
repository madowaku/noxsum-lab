from __future__ import annotations

from copy import deepcopy
from typing import Any


def import_grant_stage(
    stage: dict[str, Any],
    *,
    repo: str = "madowaku/shadow-sum",
    ref: str | None = None,
    path: str | None = None,
) -> dict[str, Any]:
    """Convert a current NOXSUM Grant stage into canonical Lab format.

    The importer intentionally keeps mechanics generic. New piece types and
    gimmicks can be added without changing the provenance / curation envelope.
    """

    source_id = str(stage["id"])
    posts = int(stage.get("posts", len(stage.get("solution", []))))
    solution_cells = list(stage.get("solution", []))

    placements = [
        {"piece": "POST", "cell": str(cell), "orientation": None}
        for cell in solution_cells
    ]

    mechanics: dict[str, Any] = {}
    for key in (
        "installed_lights",
        "fixed_posts",
        "free_light_selection",
        "active_light_count",
        "initial_lights",
        "hint_surface",
    ):
        if key in stage:
            mechanics[key] = deepcopy(stage[key])

    annotations: dict[str, Any] = {}
    if "hints" in stage:
        annotations["hints"] = deepcopy(stage["hints"])

    metrics: dict[str, Any] = {}
    if "expected_states" in stage:
        metrics["expected_states"] = stage["expected_states"]

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
            "mask": None,
        },
        "inventory": {
            "POST": posts,
        },
        "solution": {
            "placements": placements,
            "lights": list(stage.get("solution_lights", [])),
        },
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
