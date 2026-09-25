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
            ref="feature/grant20-v0.3",
            path="data/grant20_v0_3.json",
        )

        self.assertEqual(level["schema_version"], "noxsum.level.v1")
        self.assertEqual(level["source"]["source_id"], "GR01")
        self.assertEqual(level["inventory"]["POST"], 1)
        self.assertEqual(
            level["solution"]["placements"],
            [{"piece": "POST", "cell": "C3", "orientation": None}],
        )
        self.assertEqual(level["metrics"]["expected_states"], 25)
        self.assertEqual(level["curation"]["bucket"], "UNREVIEWED")


if __name__ == "__main__":
    unittest.main()
