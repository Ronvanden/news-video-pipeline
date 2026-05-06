"""BA 21.7 — Local Preview Result Contract (stabile Top-Level-Keys für Dashboard/JSON)."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[1]
_SCRIPT = _ROOT / "scripts" / "run_local_preview_pipeline.py"


@pytest.fixture(scope="module")
def preview_mod():
    spec = importlib.util.spec_from_file_location("run_local_preview_pipeline", _SCRIPT)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _min_subtitle_manifest(tmp_path: Path, tag: str) -> Path:
    d = tmp_path / f"sub217_{tag}"
    d.mkdir(parents=True, exist_ok=True)
    srt = d / "cues.srt"
    srt.write_text(
        "1\n00:00:00,000 --> 00:00:02,000\nA.\n\n2\n00:00:02,100 --> 00:00:04,000\nB.\n",
        encoding="utf-8",
    )
    m = d / "subtitle_manifest.json"
    m.write_text(json.dumps({"subtitles_srt_path": str(srt)}), encoding="utf-8")
    return m


def test_apply_contract_on_minimal_dict(preview_mod):
    raw: dict = {"ok": False}
    out = preview_mod.apply_local_preview_result_contract(raw)
    assert out is raw
    assert out["result_contract"]["id"] == preview_mod.LOCAL_PREVIEW_RESULT_CONTRACT_ID
    assert out["result_contract"]["schema_version"] == preview_mod.LOCAL_PREVIEW_RESULT_SCHEMA_VERSION
    assert out["verdict"] in ("PASS", "WARNING", "FAIL")
    for k in ("build_subtitles", "render_clean", "burnin_preview"):
        assert k in out["steps"]
    for pk in preview_mod.LOCAL_PREVIEW_RESULT_PATH_KEYS:
        assert pk in out["paths"]
    assert isinstance(out["quality_checklist"], dict)
    assert isinstance(out["subtitle_quality_check"], dict)
    assert isinstance(out["sync_guard"], dict)
    assert isinstance(out["warning_classification"], dict)
    assert isinstance(out["founder_quality_decision"], dict)


def test_pipeline_result_includes_contract_after_finalize(preview_mod, tmp_path, monkeypatch):
    tl = tmp_path / "tl217.json"
    nar = tmp_path / "n217.txt"
    tl.write_text(json.dumps({"estimated_duration_seconds": 4.0}), encoding="utf-8")
    nar.write_text("body", encoding="utf-8")
    sub_m = _min_subtitle_manifest(tmp_path, "c217")
    aud_stub = tmp_path / "a217.wav"
    aud_stub.write_bytes(b"\0")

    def fake_build(*_a, **_k):
        return {
            "ok": True,
            "subtitle_manifest_path": str(sub_m),
            "audio_path": str(aud_stub),
            "warnings": [],
            "blocking_reasons": [],
        }

    def fake_render(*_a, **kw):
        ov = kw.get("output_video")
        if ov is not None:
            Path(ov).parent.mkdir(parents=True, exist_ok=True)
            Path(ov).write_bytes(b"cv")
        return {"video_created": True, "warnings": [], "blocking_reasons": []}

    def fake_burn(*_a, **_k):
        outp = tmp_path / "pv217.mp4"
        outp.write_bytes(b"pv")
        return {
            "ok": True,
            "skipped": False,
            "output_video_path": str(outp),
            "warnings": [],
            "blocking_reasons": [],
        }

    monkeypatch.setattr(preview_mod, "_probe_media_duration_seconds", lambda p, **kw: (4.0, None))

    meta = preview_mod.run_local_preview_pipeline(
        tl,
        nar,
        out_root=tmp_path,
        run_id="ba217rid",
        build_subtitle_pack_fn=fake_build,
        render_final_story_video_fn=fake_render,
        burn_in_subtitles_preview_fn=fake_burn,
    )
    assert meta["result_contract"]["id"] == "local_preview_result_v1"
    assert meta["result_contract"]["schema_version"] == 1
    assert meta["verdict"] == meta["founder_quality_decision"]["signals"]["verdict"]
    for pk in preview_mod.LOCAL_PREVIEW_RESULT_PATH_KEYS:
        assert pk in meta["paths"]
