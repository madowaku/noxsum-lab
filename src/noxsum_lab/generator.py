from __future__ import annotations

from collections import Counter
from copy import deepcopy
import random
from typing import Any

from .rules import (
    CELL_COUNT,
    code,
    object_states,
    pack,
    packed_shadow,
    readable_objects,
    shadow,
)


def _piece(kind: str) -> tuple[str, str | None]:
    if kind == "normal":
        return "POST", None
    if kind == "tall":
        return "TALL", None
    if kind == "plate_v":
        return "PLATE", "V"
    if kind == "plate_h":
        return "PLATE", "H"
    raise ValueError(f"unknown generated object kind: {kind}")


def _target_dict(values: tuple[int, ...]) -> dict[str, int]:
    # Canonical generated levels store zeros explicitly. This makes the
    # observation semantics unambiguous before product-specific export.
    return {code(index): int(value) for index, value in enumerate(values)}


def _edge_loss(objects, lights: tuple[str, ...]) -> int:
    # Count theoretical rays that leave the board. This is a simple v0.1
    # texture metric, not a difficulty score.
    loss = 0
    for index, kind in objects:
        x, y = index % 5, index // 5
        reach = 2 if kind == "tall" else 1
        allowed = set(lights)
        if kind == "plate_v":
            allowed &= {"LEFT", "RIGHT"}
        elif kind == "plate_h":
            allowed &= {"TOP", "BOTTOM"}

        vectors = {
            "TOP": (0, 1),
            "LEFT": (1, 0),
            "RIGHT": (-1, 0),
            "BOTTOM": (0, -1),
        }
        for light in allowed:
            dx, dy = vectors[light]
            for distance in range(1, reach + 1):
                tx = x + dx * distance
                ty = y + dy * distance
                if not (0 <= tx < 5 and 0 <= ty < 5):
                    loss += 1
    return loss


def generation_stage(
    *,
    normal: int,
    tall: int,
    plate: int,
    lights: tuple[str, ...],
    board_mask: list[str] | None = None,
) -> dict[str, Any]:
    posts = normal + tall + plate
    if posts < 1:
        raise ValueError("generator needs at least one object")

    stage: dict[str, Any] = {
        "id": "GEN-TEMPLATE",
        "posts": posts,
        "normal_posts": normal,
        "tall_posts": tall,
        "plate_posts": plate,
        "installed_lights": ["TOP", "LEFT", "RIGHT", "BOTTOM"],
        "observations": [{"id": "A", "active_lights": list(lights), "target": {}}],
    }
    if plate:
        stage["rotatable_plate"] = True
    if board_mask is not None:
        stage["boardShape"] = {"mask": list(board_mask)}
    return stage


def generate_levels(
    *,
    seed: int,
    count: int,
    normal: int = 3,
    tall: int = 0,
    plate: int = 0,
    lights: tuple[str, ...] = ("TOP", "LEFT", "RIGHT"),
    board_mask: list[str] | None = None,
) -> list[dict[str, Any]]:
    """Generate deterministic exact-unique NOXSUM candidates.

    v0.1 deliberately generates from a fixed physical profile. It enumerates
    every legal world, groups worlds by complete shadow signature, and samples
    only signatures with exactly one physical solution.
    """

    if count < 1:
        return []

    template = generation_stage(
        normal=normal,
        tall=tall,
        plate=plate,
        lights=lights,
        board_mask=board_mask,
    )

    worlds = list(object_states(template))
    signatures = [packed_shadow(world, lights, None) for world in worlds]
    counts = Counter(signatures)

    unique_indices = [
        index for index, signature in enumerate(signatures)
        if counts[signature] == 1
    ]

    rng = random.Random(seed)
    rng.shuffle(unique_indices)
    if len(unique_indices) < count:
        raise ValueError(
            f"profile only has {len(unique_indices)} unique targets; requested {count}"
        )

    levels: list[dict[str, Any]] = []
    for serial, world_index in enumerate(unique_indices[:count], 1):
        objects = worlds[world_index]
        values = shadow(objects, lights)
        source_id = f"NX-GEN-{seed}-{serial:04d}"

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

        inventory: dict[str, int] = {}
        if normal:
            inventory["POST"] = normal
        if tall:
            inventory["TALL"] = tall
        if plate:
            inventory["PLATE"] = plate

        nonzero = sum(value > 0 for value in values)
        overlap = sum(value > 1 for value in values)

        level = {
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
                "mask": list(board_mask) if board_mask is not None else None,
            },
            "inventory": inventory,
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
            "annotations": {},
            "metrics": {
                "search_space": len(worlds),
                "exact_survivors": 1,
                "visible_nonzero_cells": nonzero,
                "overlap_cells": overlap,
                "edge_loss": _edge_loss(objects, lights),
            },
            "curation": {
                "bucket": "UNREVIEWED",
                "target": "NONE",
                "tags": [],
                "notes": "",
            },
        }
        levels.append(level)

    return levels
