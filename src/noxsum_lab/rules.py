from __future__ import annotations

import itertools
from functools import lru_cache
from typing import Any, Iterable, Iterator

BOARD_SIZE = 5
CELL_COUNT = BOARD_SIZE * BOARD_SIZE

DIRECTIONS = ("TOP", "LEFT", "RIGHT", "BOTTOM")
VECTORS = {
    "TOP": (0, 1),
    "LEFT": (1, 0),
    "RIGHT": (-1, 0),
    "BOTTOM": (0, -1),
}

Object = tuple[int, str]
Objects = tuple[Object, ...]


def cell(code: str) -> int:
    code = str(code).upper()
    if len(code) < 2:
        raise ValueError(f"invalid cell code: {code!r}")
    x = ord(code[0]) - ord("A")
    y = int(code[1:]) - 1
    if not (0 <= x < BOARD_SIZE and 0 <= y < BOARD_SIZE):
        raise ValueError(f"cell outside 5x5 board: {code!r}")
    return y * BOARD_SIZE + x


def code(index: int) -> str:
    if not 0 <= index < CELL_COUNT:
        raise ValueError(f"cell index outside board: {index}")
    return chr(ord("A") + index % BOARD_SIZE) + str(index // BOARD_SIZE + 1)


def category(kind: str) -> str:
    if kind in ("plate_v", "plate_h"):
        return "plate"
    if kind in ("normal", "tall"):
        return kind
    raise ValueError(f"unknown post type: {kind}")


def legal_positions(stage: dict[str, Any]) -> tuple[int, ...]:
    board_shape = stage.get("boardShape")
    if board_shape is None:
        return tuple(range(CELL_COUNT))
    if not isinstance(board_shape, dict) or not isinstance(board_shape.get("mask"), list):
        raise ValueError("boardShape.mask must be a 5-row array")

    rows = board_shape["mask"]
    if len(rows) != BOARD_SIZE:
        raise ValueError("boardShape.mask must have exactly five rows")

    result: list[int] = []
    for row_index, row in enumerate(rows):
        if (
            not isinstance(row, str)
            or len(row) != BOARD_SIZE
            or any(char not in "01" for char in row)
        ):
            raise ValueError("boardShape.mask rows must be exactly five 0/1 characters")
        result.extend(
            row_index * BOARD_SIZE + column
            for column, char in enumerate(row)
            if char == "1"
        )
    return tuple(result)


def fixed_variants(stage: dict[str, Any]) -> list[Objects]:
    fixed_codes = stage.get("fixed_posts", [])
    if not fixed_codes:
        return [tuple()]

    choices: list[tuple[Object, ...]] = []
    declared = stage.get("fixed_post_types", {})
    for name in fixed_codes:
        kind = declared.get(name, "tall" if stage.get("tall") else "normal")
        if stage.get("rotatable_plate") and str(kind).startswith("plate_"):
            choices.append(((cell(name), "plate_v"), (cell(name), "plate_h")))
        else:
            choices.append(((cell(name), str(kind)),))

    return [tuple(items) for items in itertools.product(*choices)]


def requested_inventory(stage: dict[str, Any], fixed: Objects) -> dict[str, int]:
    wanted_total = int(stage["posts"])
    fixed_counts = {"normal": 0, "tall": 0, "plate": 0}
    for _, kind in fixed:
        fixed_counts[category(kind)] += 1

    if any(key in stage for key in ("normal_posts", "tall_posts", "plate_posts")):
        requested = {
            "normal": int(stage.get("normal_posts", 0)),
            "tall": int(stage.get("tall_posts", 0)),
            "plate": int(stage.get("plate_posts", 0)),
        }
    elif stage.get("tall"):
        requested = {"normal": 0, "tall": wanted_total, "plate": 0}
    else:
        # Fixed special objects still count toward the declared total.
        requested = dict(fixed_counts)
        requested["normal"] += wanted_total - len(fixed)

    return requested


def object_states(stage: dict[str, Any]) -> Iterator[Objects]:
    allowed = legal_positions(stage)
    allowed_set = set(allowed)

    for fixed in fixed_variants(stage):
        if any(index not in allowed_set for index, _ in fixed):
            continue
        if len({index for index, _ in fixed}) != len(fixed):
            continue

        used = {index for index, _ in fixed}
        requested = requested_inventory(stage, fixed)

        fixed_counts = {"normal": 0, "tall": 0, "plate": 0}
        for _, kind in fixed:
            fixed_counts[category(kind)] += 1

        remaining = {
            name: requested[name] - fixed_counts[name]
            for name in requested
        }
        if any(value < 0 for value in remaining.values()):
            continue

        available = [index for index in allowed if index not in used]
        normal_count = remaining["normal"]
        tall_count = remaining["tall"]
        plate_count = remaining["plate"]

        for normals in itertools.combinations(available, normal_count):
            normal_set = set(normals)
            after_normal = [index for index in available if index not in normal_set]
            for talls in itertools.combinations(after_normal, tall_count):
                tall_set = set(talls)
                after_tall = [index for index in after_normal if index not in tall_set]
                for plates in itertools.combinations(after_tall, plate_count):
                    base = list(fixed)
                    base.extend((index, "normal") for index in normals)
                    base.extend((index, "tall") for index in talls)

                    if plate_count == 0:
                        yield tuple(base)
                        continue

                    for orientations in itertools.product(
                        ("plate_v", "plate_h"), repeat=plate_count
                    ):
                        objects = list(base)
                        objects.extend(zip(plates, orientations))
                        yield tuple(objects)


def light_states(stage: dict[str, Any]) -> list[tuple[str, ...]]:
    if not stage.get("free_light_selection"):
        observations = stage.get("observations", [])
        if not observations:
            return [tuple(stage.get("installed_lights", ()))]
        return [tuple(observations[0].get("active_lights", ()))]

    installed = tuple(stage["installed_lights"])
    if "active_light_count" in stage:
        return list(itertools.combinations(installed, int(stage["active_light_count"])))

    return [
        combo
        for count in range(1, len(installed) + 1)
        for combo in itertools.combinations(installed, count)
    ]


def shutter_states(stage: dict[str, Any]) -> list[int | None]:
    if stage.get("movable_shutter"):
        return list(range(BOARD_SIZE))
    fixed = stage.get("fixed_shutters", [])
    return [int(fixed[0]) if fixed else None]


@lru_cache(maxsize=None)
def atomic_shadow(index: int, kind: str, lights: tuple[str, ...], shutter: int | None) -> tuple[int, ...]:
    result = [0] * CELL_COUNT
    x, y = index % BOARD_SIZE, index // BOARD_SIZE
    reach = 2 if kind == "tall" else 1

    for light in lights:
        if light not in VECTORS:
            raise ValueError(f"unknown light direction: {light}")

        # Current NOXSUM shutter blocks the TOP lamp for one board column.
        if light == "TOP" and shutter is not None and x == shutter:
            continue
        if kind == "plate_v" and light not in ("LEFT", "RIGHT"):
            continue
        if kind == "plate_h" and light not in ("TOP", "BOTTOM"):
            continue

        dx, dy = VECTORS[light]
        for distance in range(1, reach + 1):
            tx = x + dx * distance
            ty = y + dy * distance
            if 0 <= tx < BOARD_SIZE and 0 <= ty < BOARD_SIZE:
                result[ty * BOARD_SIZE + tx] += 1

    return tuple(result)


def shadow(objects: Iterable[Object], lights: Iterable[str], shutter: int | None = None) -> tuple[int, ...]:
    lights_tuple = tuple(lights)
    result = [0] * CELL_COUNT
    for index, kind in objects:
        atom = atomic_shadow(index, kind, lights_tuple, shutter)
        for i, value in enumerate(atom):
            result[i] += value
    return tuple(result)


def pack(values: Iterable[int]) -> int:
    """Pack 25 small shadow values into 4-bit lanes for fast comparisons."""
    result = 0
    for index, value in enumerate(values):
        value = int(value)
        if not 0 <= value <= 15:
            raise ValueError(f"shadow lane overflow at {index}: {value}")
        result |= value << (4 * index)
    return result


@lru_cache(maxsize=None)
def atomic_pack(index: int, kind: str, lights: tuple[str, ...], shutter: int | None) -> int:
    return pack(atomic_shadow(index, kind, lights, shutter))


def packed_shadow(objects: Objects, lights: Iterable[str], shutter: int | None = None) -> int:
    lights_tuple = tuple(lights)
    return sum(
        atomic_pack(index, kind, lights_tuple, shutter)
        for index, kind in objects
    )


def observation_projection(
    stage: dict[str, Any], observation: dict[str, Any]
) -> tuple[int, int]:
    fog = set(stage.get("fog_cells", []))
    values = [0] * CELL_COUNT
    mask = 0

    target = observation.get("target", {})
    for index in range(CELL_COUNT):
        name = code(index)
        if name in fog:
            continue
        values[index] = int(target.get(name, 0))
        mask |= 0xF << (4 * index)

    return pack(values), mask


def state_matches(
    stage: dict[str, Any],
    objects: Objects,
    selected_lights: tuple[str, ...],
    shutter: int | None,
) -> bool:
    for observation in stage.get("observations", []):
        if stage.get("free_light_selection") or stage.get("light_puzzle"):
            lights = selected_lights
        else:
            lights = tuple(observation.get("active_lights", ()))

        expected, mask = observation_projection(stage, observation)
        actual = packed_shadow(objects, lights, shutter)
        if (actual & mask) != (expected & mask):
            return False

    return True


def readable_objects(objects: Objects) -> list[dict[str, str]]:
    return [
        {"cell": code(index), "type": kind}
        for index, kind in sorted(objects)
    ]
