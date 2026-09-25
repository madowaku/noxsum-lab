from __future__ import annotations

from typing import Iterable

from .rules import BOARD_SIZE, CELL_COUNT, VECTORS

# D4 symmetries of the square. Each transform maps (x, y) -> (x', y').
SYMMETRIES = (
    "identity",
    "rot90",
    "rot180",
    "rot270",
    "mirror_x",
    "mirror_y",
    "diag",
    "anti_diag",
)

VECTOR_TO_LIGHT = {value: key for key, value in VECTORS.items()}


def transform_xy(x: int, y: int, symmetry: str) -> tuple[int, int]:
    n = BOARD_SIZE - 1
    if symmetry == "identity":
        return x, y
    if symmetry == "rot90":
        return n - y, x
    if symmetry == "rot180":
        return n - x, n - y
    if symmetry == "rot270":
        return y, n - x
    if symmetry == "mirror_x":
        return n - x, y
    if symmetry == "mirror_y":
        return x, n - y
    if symmetry == "diag":
        return y, x
    if symmetry == "anti_diag":
        return n - y, n - x
    raise ValueError(f"unknown symmetry: {symmetry}")


def transform_vector(dx: int, dy: int, symmetry: str) -> tuple[int, int]:
    # Transform a direction by transforming a centered point and subtracting
    # the transformed center. BOARD_SIZE is odd, so the center is integral.
    center = BOARD_SIZE // 2
    cx, cy = transform_xy(center, center, symmetry)
    px, py = transform_xy(center + dx, center + dy, symmetry)
    return px - cx, py - cy


def transform_index(index: int, symmetry: str) -> int:
    x, y = index % BOARD_SIZE, index // BOARD_SIZE
    tx, ty = transform_xy(x, y, symmetry)
    return ty * BOARD_SIZE + tx


def transform_values(values: Iterable[int], symmetry: str) -> tuple[int, ...]:
    source = tuple(int(value) for value in values)
    if len(source) != CELL_COUNT:
        raise ValueError(f"expected {CELL_COUNT} values, got {len(source)}")
    result = [0] * CELL_COUNT
    for index, value in enumerate(source):
        result[transform_index(index, symmetry)] = value
    return tuple(result)


def transform_light(light: str, symmetry: str) -> str:
    vector = VECTORS[light]
    transformed = transform_vector(*vector, symmetry)
    return VECTOR_TO_LIGHT[transformed]


def transform_lights(lights: Iterable[str], symmetry: str) -> tuple[str, ...]:
    order = {name: index for index, name in enumerate(("TOP", "LEFT", "RIGHT", "BOTTOM"))}
    transformed = {transform_light(light, symmetry) for light in lights}
    return tuple(sorted(transformed, key=order.__getitem__))


def mask_rows_to_values(mask: list[str] | None) -> tuple[int, ...]:
    if mask is None:
        return (1,) * CELL_COUNT
    if len(mask) != BOARD_SIZE:
        raise ValueError("mask must have five rows")
    return tuple(int(char) for row in mask for char in row)


def values_to_mask_rows(values: Iterable[int]) -> tuple[str, ...]:
    source = tuple(values)
    return tuple(
        "".join(str(int(source[y * BOARD_SIZE + x])) for x in range(BOARD_SIZE))
        for y in range(BOARD_SIZE)
    )


def canonical_puzzle_signature(
    *,
    target: Iterable[int],
    lights: Iterable[str],
    inventory: tuple[int, int, int],
    board_mask: list[str] | None = None,
) -> str:
    """Return a D4-invariant signature for a fixed-light puzzle.

    The transform includes both the target field and light directions. This
    means a 90-degree-rotated puzzle with correspondingly rotated lamps is
    treated as the same underlying puzzle.
    """

    target_tuple = tuple(int(value) for value in target)
    mask_values = mask_rows_to_values(board_mask)
    variants: list[str] = []
    for symmetry in SYMMETRIES:
        transformed_target = transform_values(target_tuple, symmetry)
        transformed_mask = transform_values(mask_values, symmetry)
        transformed_lights = transform_lights(lights, symmetry)
        variants.append(
            "|".join(
                (
                    f"inv={inventory[0]},{inventory[1]},{inventory[2]}",
                    "lights=" + ",".join(transformed_lights),
                    "mask=" + "".join(str(value) for value in transformed_mask),
                    "target=" + ",".join(str(value) for value in transformed_target),
                )
            )
        )
    return min(variants)
