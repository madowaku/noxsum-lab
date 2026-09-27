from __future__ import annotations

import json
from pathlib import Path
import unittest

from noxsum_lab.gimmick_probe import solve_probe, validate_probe_pack

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "fixtures/gimmick_probe_v0_3.json"


def load_stages():
    data = json.loads(FIXTURE.read_text(encoding="utf-8"))
    return data["stages"]


class GimmickProbeTests(unittest.TestCase):
    def test_four_authored_gimmick_probes_are_unique(self) -> None:
        results = validate_probe_pack(load_stages())
        self.assertEqual(
            [result.stage_id for result in results],
            ["LAN-01", "LAN-02", "MIR-01", "MIR-02"],
        )
        self.assertEqual(
            [result.searched_states for result in results],
            [552, 552, 48, 46],
        )
        self.assertTrue(all(result.solution_count == 1 for result in results))

    def test_mir02_uses_zero_to_choose_orientation(self) -> None:
        stage = next(stage for stage in load_stages() if stage["id"] == "MIR-02")

        e5_only = solve_probe(stage, observed_cells=["E5"])
        self.assertEqual(e5_only.solution_count, 2)
        self.assertEqual(
            {state.mirror_orientation for state in e5_only.solutions},
            {"/", "\\"},
        )

        with_zero = solve_probe(stage, observed_cells=["E5", "A3"])
        self.assertEqual(with_zero.solution_count, 1)
        self.assertEqual(with_zero.solutions[0].mirror_orientation, "\\")
        self.assertEqual(
            with_zero.solutions[0].readable()["movable_sits"],
            ["E4"],
        )

    def test_lan02_needs_both_observations(self) -> None:
        stage = next(stage for stage in load_stages() if stage["id"] == "LAN-02")
        self.assertEqual(
            solve_probe(stage, observed_cells=["B3"]).solution_count,
            48,
        )
        self.assertEqual(
            solve_probe(stage, observed_cells=["D1"]).solution_count,
            5,
        )
        result = solve_probe(stage, observed_cells=["B3", "D1"])
        self.assertEqual(result.solution_count, 1)
        self.assertEqual(
            result.solutions[0].readable(),
            {
                "family": "LANTERN",
                "movable_sits": ["D2"],
                "lantern": "D3",
            },
        )


if __name__ == "__main__":
    unittest.main()
