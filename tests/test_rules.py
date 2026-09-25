import unittest

from noxsum_lab.rules import cell, legal_positions, shadow


class RulesTests(unittest.TestCase):
    def test_normal_post_matches_first_shadow(self) -> None:
        actual = shadow(((cell("C3"), "normal"),), ("TOP", "LEFT", "RIGHT"))
        nonzero = {
            index: value
            for index, value in enumerate(actual)
            if value
        }
        self.assertEqual(
            nonzero,
            {
                cell("B3"): 1,
                cell("D3"): 1,
                cell("C4"): 1,
            },
        )

    def test_tall_reaches_two_cells(self) -> None:
        actual = shadow(((cell("C3"), "tall"),), ("TOP",))
        self.assertEqual(actual[cell("C4")], 1)
        self.assertEqual(actual[cell("C5")], 1)

    def test_plate_axis(self) -> None:
        vertical = shadow(
            ((cell("C3"), "plate_v"),),
            ("TOP", "LEFT", "RIGHT", "BOTTOM"),
        )
        horizontal = shadow(
            ((cell("C3"), "plate_h"),),
            ("TOP", "LEFT", "RIGHT", "BOTTOM"),
        )
        self.assertEqual(vertical[cell("B3")], 1)
        self.assertEqual(vertical[cell("D3")], 1)
        self.assertEqual(vertical[cell("C2")], 0)
        self.assertEqual(vertical[cell("C4")], 0)
        self.assertEqual(horizontal[cell("C2")], 1)
        self.assertEqual(horizontal[cell("C4")], 1)
        self.assertEqual(horizontal[cell("B3")], 0)
        self.assertEqual(horizontal[cell("D3")], 0)

    def test_shutter_blocks_top_for_column(self) -> None:
        unblocked = shadow(((cell("C3"), "normal"),), ("TOP",), None)
        blocked = shadow(((cell("C3"), "normal"),), ("TOP",), 2)
        self.assertEqual(unblocked[cell("C4")], 1)
        self.assertEqual(blocked[cell("C4")], 0)

    def test_board_shape_only_limits_sockets(self) -> None:
        stage = {
            "boardShape": {
                "mask": [
                    "00100",
                    "00100",
                    "11111",
                    "00100",
                    "00100",
                ]
            }
        }
        self.assertEqual(len(legal_positions(stage)), 9)


if __name__ == "__main__":
    unittest.main()
