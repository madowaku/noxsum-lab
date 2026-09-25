from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .rules import (
    Objects,
    cell,
    code,
    light_states,
    object_states,
    readable_objects,
    shutter_states,
    state_matches,
)


@dataclass(frozen=True)
class SolutionState:
    objects: Objects
    lights: tuple[str, ...]
    shutter: int | None

    def as_dict(self) -> dict[str, Any]:
        return {
            "objects": readable_objects(self.objects),
            "lights": list(self.lights),
            "shutter": self.shutter,
        }


@dataclass(frozen=True)
class SolveResult:
    stage_id: str
    searched_states: int
    solution_count: int
    solutions: tuple[SolutionState, ...]

    @property
    def unique(self) -> bool:
        return self.solution_count == 1


def solve_stage(stage: dict[str, Any], *, keep_solutions: int = 4) -> SolveResult:
    searched = 0
    solution_count = 0
    kept: list[SolutionState] = []

    lights_options = light_states(stage)
    shutters = shutter_states(stage)

    for objects in object_states(stage):
        for lights in lights_options:
            for shutter in shutters:
                searched += 1
                if not state_matches(stage, objects, lights, shutter):
                    continue

                solution_count += 1
                if len(kept) < keep_solutions:
                    kept.append(SolutionState(objects, lights, shutter))

    return SolveResult(
        stage_id=str(stage.get("id", "<unknown>")),
        searched_states=searched,
        solution_count=solution_count,
        solutions=tuple(kept),
    )


def _expected_kind(stage: dict[str, Any], name: str) -> str:
    declared = stage.get("solution_post_types", {})
    if name in declared:
        return str(declared[name])
    if name in set(stage.get("solution_tall", [])):
        return "tall"
    if stage.get("tall"):
        return "tall"
    return "normal"


def expected_objects(stage: dict[str, Any]) -> set[tuple[int, str]]:
    return {
        (cell(name), _expected_kind(stage, name))
        for name in stage.get("solution", [])
    }


def assert_solution_metadata(stage: dict[str, Any], solution: SolutionState) -> None:
    actual = set(solution.objects)
    expected = expected_objects(stage)
    if actual != expected:
        readable_actual = [(code(index), kind) for index, kind in sorted(actual)]
        readable_expected = [(code(index), kind) for index, kind in sorted(expected)]
        raise AssertionError(
            f"{stage['id']}: solution objects differ; "
            f"actual={readable_actual}, expected={readable_expected}"
        )

    if stage.get("free_light_selection"):
        wanted = set(stage.get("solution_lights", []))
        if set(solution.lights) != wanted:
            raise AssertionError(
                f"{stage['id']}: lights={solution.lights}, expected={sorted(wanted)}"
            )

    if stage.get("movable_shutter"):
        wanted = int(stage["solution_shutter"])
        if solution.shutter != wanted:
            raise AssertionError(
                f"{stage['id']}: shutter={solution.shutter}, expected={wanted}"
            )


def validate_stage(stage: dict[str, Any]) -> SolveResult:
    result = solve_stage(stage)

    expected_states = int(stage.get("expected_states", result.searched_states))
    if result.searched_states != expected_states:
        raise AssertionError(
            f"{stage['id']}: searched {result.searched_states} states, "
            f"expected {expected_states}"
        )

    if result.solution_count != 1:
        raise AssertionError(
            f"{stage['id']}: expected unique solution, got {result.solution_count}; "
            f"examples={[item.as_dict() for item in result.solutions]}"
        )

    assert_solution_metadata(stage, result.solutions[0])
    return result


def validate_campaign(stages: list[dict[str, Any]]) -> list[SolveResult]:
    results: list[SolveResult] = []
    for stage in stages:
        results.append(validate_stage(stage))
    return results
