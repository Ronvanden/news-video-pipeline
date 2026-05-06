"""BA 30.2 — Fresh topic / URL / script → preview smoke orchestration."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

from app.production_assembly.fresh_topic_preview_smoke import run_fresh_topic_preview_smoke


def test_fresh_topic_dry_run_produces_asset_manifest(tmp_path: Path):
    out = tmp_path / "output"
    fake_script = {
        "title": "T",
        "hook": "H",
        "chapters": [{"title": "K1", "content": "Erster Absatz mit genug Text für eine Szene."}],
        "full_script": "",
        "sources": [],
        "warnings": [],
    }
    with patch(
        "app.production_assembly.fresh_topic_preview_smoke._build_script_for_fresh_input",
        return_value=(fake_script, [], []),
    ):
        r = run_fresh_topic_preview_smoke(
            run_id="fresh_t1",
            output_root=out,
            topic="ignored_under_mock",
            duration_target_seconds=45,
            dry_run=True,
            max_scenes=4,
        )
    assert r.get("ok") is True
    assert r.get("asset_manifest_path")
    am = Path(r["asset_manifest_path"])
    assert am.is_file()
    doc = json.loads(am.read_text(encoding="utf-8"))
    assert isinstance(doc.get("assets"), list)
    assert len(doc["assets"]) >= 1


def test_fresh_no_input_blocks():
    import tempfile

    with tempfile.TemporaryDirectory() as td:
        r = run_fresh_topic_preview_smoke(
            run_id="x",
            output_root=Path(td),
            topic=None,
            url=None,
            script_json=None,
            dry_run=True,
        )
    assert r.get("blocking_reasons")


def test_fresh_full_run_uses_execute_preview_smoke(tmp_path: Path):
    out = tmp_path / "output"
    fake_script = {
        "title": "T2",
        "hook": "H2",
        "chapters": [{"title": "K", "content": "Inhalt für Szene eins. Noch etwas Text."}],
        "full_script": "",
        "sources": [],
        "warnings": [],
    }

    def fake_execute(**kwargs):
        return (
            {
                "ok": True,
                "run_id": kwargs.get("run_id"),
                "open_preview_smoke_report_path": str(out / "OPEN.md"),
            },
            0,
        )

    with patch(
        "app.production_assembly.fresh_topic_preview_smoke._build_script_for_fresh_input",
        return_value=(fake_script, [], []),
    ), patch(
        "app.production_assembly.preview_smoke_auto.execute_preview_smoke_auto",
        fake_execute,
    ):
        r = run_fresh_topic_preview_smoke(
            run_id="fresh_t2",
            output_root=out,
            topic="mocked",
            dry_run=False,
            max_scenes=3,
        )
    assert r.get("ok") is True
    assert r.get("preview_smoke_exit_code") == 0
    assert r.get("preview_smoke_summary", {}).get("ok") is True
