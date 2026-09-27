from __future__ import annotations

import json
from pathlib import Path

from noxsum_lab.gimmick_probe import solve_probe, validate_probe_pack

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "fixtures/gimmick_probe_v0_3.json"


def load_stages():
    data = json.loads(FIXTURE.read_text(encoding="utf-8"))
    return data["stages"]


def test_four_authored_gimmick_probes_are_unique():
    results = validate_probe_pack(load_stages())
    assert [result.stage_id for result in results] == [
        "LAN-01", "LAN-02", "MIR-01", "MIR-02"
    ]
    assert [result.searched_states for result in results] == [552, 552, 48, 46]
    assert all(result.solution_count == 1 for result in results)


def test_mir02_uses_zero_to_choose_orientation():
    stage = next(stage for stage in load_stages() if stage["id"] == "MIR-02")

    e5_only = solve_probe(stage, observed_cells=["E5"])
    assert e5_only.solution_count == 2
    assert {state.mirror_orientation for state in e5_only.solutions} == {"/", "\\"}

    with_zero = solve_probe(stage, observed_cells=["E5", "A3"])
    assert with_zero.solution_count == 1
    assert with_zero.solutions[0].mirror_orientation == "\\"
    assert with_zero.solutions[0].readable()["movable_sits"] == ["E4"]


def test_lan02_needs_both_observations():
    stage = next(stage for stage in load_stages() if stage["id"] == "LAN-02")
    assert solve_probe(stage, observed_cells=["B3"]).solution_count == 48
    assert solve_probe(stage, observed_cells=["D1"]).solution_count == 5
    result = solve_probe(stage, observed_cells=["B3", "D1"])
    assert result.solution_count == 1
    assert result.solutions[0].readable() == {
        "family": "LANTERN",
        "movable_sits": ["D2"],
        "lantern": "D3",
    }
