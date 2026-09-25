import unittest

from noxsum_lab.import_grant import import_grant_stage


class ImportGrantTests(unittest.TestCase):
    def test_imports_basic_grant_stage(self) -> None:
        stage = {
            "id": "GR01",
            "title": "FIRST SHADOW",
            "posts": 1,
            "solution": ["C3"],
            "installed_lights": ["TOP", "LEFT", "RIGHT"],
            "observations": [
                {
                    "id": "A",
                    "active_lights": ["TOP", "LEFT", "RIGHT"],
                    "target": {"B3": 1, "D3": 1, "C4": 1},
                }
            ],
            "expected_states": 25,
        }

        level = import_grant_stage(
            stage,
            ref="feature/grant36-v0.5-board-shapes",
            path="data/grant36_v0_5.json",
        )

        self.assertEqual(level["schema_version"], "noxsum.level.v1")
        self.assertEqual(level["source"]["source_id"], "GR01")
        self.assertEqual(level["inventory"]["POST"], 1)
        self.assertEqual(
            level["solution"]["placements"],
            [
                {
                    "piece": "POST",
                    "cell": "C3",
                    "orientation": None,
                    "kind": "normal",
                }
            ],
        )
        self.assertEqual(level["metrics"]["expected_states"], 25)
        self.assertEqual(level["curation"]["bucket"], "UNREVIEWED")

    def test_preserves_typed_piece_board_fog_and_shutter(self) -> None:
        stage = {
            "id": "GRXX",
            "title": "MIXED",
            "posts": 3,
            "normal_posts": 1,
            "tall_posts": 1,
            "plate_posts": 1,
            "solution": ["A1", "B2", "C3"],
            "solution_post_types": {
                "A1": "normal",
                "B2": "tall",
                "C3": "plate_h",
            },
            "solution_lights": ["TOP", "LEFT"],
            "solution_shutter": 2,
            "movable_shutter": True,
            "rotatable_plate": True,
            "fog_cells": ["E5"],
            "boardShape": {
                "mask": [
                    "11111",
                    "11111",
                    "11111",
                    "11111",
                    "11110",
                ]
            },
            "observations": [],
            "expected_states": 123,
        }

        level = import_grant_stage(stage)

        self.assertEqual(
            level["inventory"],
            {"POST": 1, "TALL": 1, "PLATE": 1},
        )
        self.assertEqual(level["board"]["mask"][-1], "11110")
        self.assertEqual(level["mechanics"]["fog_cells"], ["E5"])
        self.assertEqual(level["solution"]["shutter"], 2)

        plate = level["solution"]["placements"][2]
        self.assertEqual(plate["piece"], "PLATE")
        self.assertEqual(plate["orientation"], "H")


if __name__ == "__main__":
    unittest.main()
