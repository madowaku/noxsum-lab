from __future__ import annotations

import itertools
from dataclasses import dataclass
from typing import Any, Iterable

BOARD_SIZE = 5
CELL_COUNT = 25
LIGHT_VECTORS = {
    "TOP": (0, 1),
    "LEFT": (1, 0),
    "RIGHT": (-1, 0),
    "BOTTOM": (0, -1),
}


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
        raise ValueError(f"cell outside 5x5 board: {index}")
    return chr(ord("A") + index % BOARD_SIZE) + str(index // BOARD_SIZE + 1)


def _xy(index: int) -> tuple[int, int]:
    return index % BOARD_SIZE, index // BOARD_SIZE


def lantern_shadow(lantern: int, sits: Iterable[int]) -> tuple[int, ...]:
    """v0.2 lantern concept model.

    The lantern emits four orthogonal rays. A SIT in the same row/column creates
    one shadow cell one step farther away from the lantern. SIT traces do not
    occlude each other and the lantern itself creates no recorded shadow.
    """
    lx, ly = _xy(lantern)
    result = [0] * CELL_COUNT

    for sit in sits:
        sx, sy = _xy(sit)
        if sx == lx and sy != ly:
            dy = 1 if sy > ly else -1
            tx, ty = sx, sy + dy
        elif sy == ly and sx != lx:
            dx = 1 if sx > lx else -1
            tx, ty = sx + dx, sy
        else:
            continue

        if 0 <= tx < BOARD_SIZE and 0 <= ty < BOARD_SIZE:
            result[ty * BOARD_SIZE + tx] += 1

    return tuple(result)


def _reflect(direction: tuple[int, int], orientation: str) -> tuple[int, int]:
    dx, dy = direction
    if orientation == "/":
        return -dy, -dx
    if orientation == "\\":
        return dy, dx
    raise ValueError(f"invalid mirror orientation: {orientation!r}")


def _edge_starts(light: str) -> list[tuple[int, int]]:
    if light == "TOP":
        return [(x, 0) for x in range(BOARD_SIZE)]
    if light == "BOTTOM":
        return [(x, BOARD_SIZE - 1) for x in range(BOARD_SIZE)]
    if light == "LEFT":
        return [(0, y) for y in range(BOARD_SIZE)]
    if light == "RIGHT":
        return [(BOARD_SIZE - 1, y) for y in range(BOARD_SIZE)]
    raise ValueError(f"invalid light: {light!r}")


def mirror_shadow(
    mirror: int,
    orientation: str,
    sits: Iterable[int],
    lights: Iterable[str],
) -> tuple[int, ...]:
    """Trace parallel board-edge beams through one fixed 90-degree mirror.

    A SIT creates one shadow cell immediately downstream for each beam path that
    reaches it. The beam continues after the SIT. The fixed mirror occupies its
    own cell and is not a legal SIT position.
    """
    sit_set = set(sits)
    result = [0] * CELL_COUNT

    for light in lights:
        for start_x, start_y in _edge_starts(light):
            dx, dy = LIGHT_VECTORS[light]
            x, y = start_x, start_y
            visited: set[tuple[int, int, int, int]] = set()

            while 0 <= x < BOARD_SIZE and 0 <= y < BOARD_SIZE:
                state = (x, y, dx, dy)
                if state in visited:
                    break
                visited.add(state)

                index = y * BOARD_SIZE + x
                if index == mirror:
                    dx, dy = _reflect((dx, dy), orientation)
                    x += dx
                    y += dy
                    continue

                if index in sit_set:
                    tx, ty = x + dx, y + dy
                    if 0 <= tx < BOARD_SIZE and 0 <= ty < BOARD_SIZE:
                        result[ty * BOARD_SIZE + tx] += 1

                x += dx
                y += dy

    return tuple(result)


def _matches(shadow: tuple[int, ...], observed: dict[str, int]) -> bool:
    return all(shadow[cell(name)] == int(value) for name, value in observed.items())


@dataclass(frozen=True)
class ProbeState:
    family: str
    movable_sits: tuple[int, ...]
    lantern: int | None = None
    mirror_orientation: str | None = None

    def readable(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "family": self.family,
            "movable_sits": [code(index) for index in self.movable_sits],
        }
        if self.lantern is not None:
            result["lantern"] = code(self.lantern)
        if self.mirror_orientation is not None:
            result["mirror_orientation"] = self.mirror_orientation
        return result


@dataclass(frozen=True)
class ProbeResult:
    stage_id: str
    searched_states: int
    solution_count: int
    solutions: tuple[ProbeState, ...]


def _lantern_worlds(stage: dict[str, Any]):
    fixed = tuple(cell(name) for name in stage.get("fixed_sits", []))
    if int(stage.get("lanterns", 1)) != 1:
        raise ValueError("v0.3 probe supports exactly one lantern")

    for lantern in range(CELL_COUNT):
        if lantern in fixed:
            continue
        available = [
            index
            for index in range(CELL_COUNT)
            if index not in fixed and index != lantern
        ]
        for movable in itertools.combinations(
            available, int(stage.get("movable_sits", 0))
        ):
            shadow = lantern_shadow(lantern, fixed + movable)
            state = ProbeState(
                family="LANTERN",
                lantern=lantern,
                movable_sits=tuple(movable),
            )
            yield state, shadow


def _mirror_worlds(stage: dict[str, Any]):
    mirror = cell(stage["fixed_mirror"])
    fixed = tuple(cell(name) for name in stage.get("fixed_sits", []))
    if mirror in fixed:
        raise ValueError("mirror cell cannot contain fixed SIT")

    available = [
        index for index in range(CELL_COUNT)
        if index != mirror and index not in fixed
    ]
    lights = tuple(stage.get("fixed_lights", ("TOP",)))

    for orientation in stage.get("mirror_orientations", ("/", "\\")):
        for movable in itertools.combinations(
            available, int(stage.get("movable_sits", 0))
        ):
            shadow = mirror_shadow(
                mirror,
                str(orientation),
                fixed + movable,
                lights,
            )
            state = ProbeState(
                family="ROTATABLE_MIRROR",
                mirror_orientation=str(orientation),
                movable_sits=tuple(movable),
            )
            yield state, shadow


def enumerate_worlds(stage: dict[str, Any]):
    family = str(stage["family"])
    if family == "LANTERN":
        yield from _lantern_worlds(stage)
        return
    if family == "ROTATABLE_MIRROR":
        yield from _mirror_worlds(stage)
        return
    raise ValueError(f"unsupported probe family: {family}")


def solve_probe(
    stage: dict[str, Any],
    *,
    observed_cells: Iterable[str] | None = None,
    keep_solutions: int = 8,
) -> ProbeResult:
    observed = dict(stage["observed"])
    if observed_cells is not None:
        wanted = {str(name) for name in observed_cells}
        observed = {
            name: value for name, value in observed.items()
            if name in wanted
        }

    searched = 0
    count = 0
    kept: list[ProbeState] = []
    for state, shadow in enumerate_worlds(stage):
        searched += 1
        if not _matches(shadow, observed):
            continue
        count += 1
        if len(kept) < keep_solutions:
            kept.append(state)

    return ProbeResult(
        stage_id=str(stage["id"]),
        searched_states=searched,
        solution_count=count,
        solutions=tuple(kept),
    )


def _assert_authored_solution(stage: dict[str, Any], state: ProbeState) -> None:
    wanted_sits = tuple(sorted(cell(name) for name in stage["solution"].get("movable_sits", [])))
    if tuple(sorted(state.movable_sits)) != wanted_sits:
        raise AssertionError(
            f"{stage['id']}: movable SITs {state.readable()['movable_sits']} "
            f"!= {stage['solution'].get('movable_sits', [])}"
        )

    if stage["family"] == "LANTERN":
        wanted = cell(stage["solution"]["lantern"])
        if state.lantern != wanted:
            raise AssertionError(
                f"{stage['id']}: lantern={code(state.lantern)} "
                f"!= {stage['solution']['lantern']}"
            )
    else:
        wanted = str(stage["solution"]["mirror_orientation"])
        if state.mirror_orientation != wanted:
            raise AssertionError(
                f"{stage['id']}: mirror={state.mirror_orientation!r} != {wanted!r}"
            )


def validate_probe(stage: dict[str, Any]) -> ProbeResult:
    result = solve_probe(stage)
    if result.searched_states != int(stage["expected_states"]):
        raise AssertionError(
            f"{stage['id']}: searched {result.searched_states}, "
            f"expected {stage['expected_states']}"
        )
    if result.solution_count != int(stage["expected_solutions"]):
        raise AssertionError(
            f"{stage['id']}: solutions={result.solution_count}, "
            f"expected {stage['expected_solutions']}"
        )
    if result.solution_count != 1:
        raise AssertionError(f"{stage['id']}: authored probe must be unique")
    _assert_authored_solution(stage, result.solutions[0])

    for counterfactual in stage.get("counterfactuals", []):
        reduced = solve_probe(
            stage,
            observed_cells=counterfactual["observed"],
            keep_solutions=0,
        )
        expected = int(counterfactual["expected_solutions"])
        if reduced.solution_count != expected:
            raise AssertionError(
                f"{stage['id']}: observed={counterfactual['observed']} "
                f"survivors={reduced.solution_count}, expected={expected}"
            )

    return result


def validate_probe_pack(stages: list[dict[str, Any]]) -> list[ProbeResult]:
    return [validate_probe(stage) for stage in stages]
