from pathlib import Path
import json

from noxsum_lab.playtest import write_playtest_current


def test_write_playtest_current_writes_game_stages(tmp_path: Path) -> None:
    pack = {
        "game_stages": [
            {
                "id": "PT-001",
                "source_id": "NX-MINE-00001",
                "title": "BLIND TEST 01",
            },
            {
                "id": "PT-002",
                "source_id": "NX-MINE-00002",
                "title": "BLIND TEST 02",
            },
        ]
    }

    output = write_playtest_current(pack, tmp_path / "exports" / "playtest_current.json")

    assert output.exists()
    data = json.loads(output.read_text(encoding="utf-8"))
    assert [stage["id"] for stage in data] == ["PT-001", "PT-002"]
    assert data[0]["source_id"] == "NX-MINE-00001"
