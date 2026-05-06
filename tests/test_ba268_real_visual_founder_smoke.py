"""BA 26.8 — Real Visual Assets Founder Smoke Tests.

Tests:
1. visual_summary.json wird erzeugt
2. Provider ohne ENV blockt sauber, kein Crash
3. Fallback-Asset wird klar markiert
4. Priorität Video > Bild > Fallback
5. run_url_to_final_mp4.py wird nicht gebrochen
6. Bestehende BA 26.5/26.6/26.7 Tests bleiben grün (via pytest -q)

Keine echten Provider-Calls — Leonardo/Runway über Mocks.
"""

from __future__ import annotations

import importlib.util
import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Tuple
from unittest.mock import patch

import pytest

_ROOT = Path(__file__).resolve().parents[1]
_SCRIPT = _ROOT / "scripts" / "run_real_visual_founder_smoke.py"
_URL_TO_FINAL = _ROOT / "scripts" / "run_url_to_final_mp4.py"


@pytest.fixture(scope="module")
def ba268_mod():
    spec = importlib.util.spec_from_file_location("ba268_test", _SCRIPT)
    assert spec and spec.loader
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


@pytest.fixture(scope="module")
def ba265_mod():
    spec = importlib.util.spec_from_file_location("ba265_test_268", _URL_TO_FINAL)
    assert spec and spec.loader
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _ffmpeg_ok() -> bool:
    return shutil.which("ffmpeg") is not None


def _write_min_mp4(target: Path) -> None:
    subprocess.run(
        [
            "ffmpeg", "-y", "-f", "lavfi",
            "-i", "color=c=blue:s=320x240:r=25",
            "-t", "1", "-c:v", "libx264", "-pix_fmt", "yuv420p",
            str(target),
        ],
        check=True, capture_output=True, text=True,
    )


def _minimal_script(path: Path, *, n_chapters: int = 3) -> None:
    chapters = [
        {"title": f"Kapitel {i+1}", "content": f"Inhalt Absatz {i+1}. " * 8}
        for i in range(n_chapters)
    ]
    doc = {
        "title": "BA268 Testtitel",
        "hook": "Kurzer Hook für BA 26.8.",
        "chapters": chapters,
        "full_script": "",
        "sources": ["https://example.com/test268"],
        "warnings": [],
    }
    path.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")


def _fake_leonardo_ok(prompt: str, dest: Path) -> Tuple[bool, List[str]]:
    """Mock: erzeugt ein kleines echtes PNG für die Pipeline."""
    from PIL import Image
    img = Image.new("RGB", (320, 240), color=(50, 80, 120))
    dest.parent.mkdir(parents=True, exist_ok=True)
    img.save(dest, format="PNG")
    return True, ["mock_leonardo_used"]


def _fake_leonardo_fail(prompt: str, dest: Path) -> Tuple[bool, List[str]]:
    return False, ["mock_leonardo_api_unavailable"]


def _fake_runway_ok(
    *, image_path, prompt, run_id, out_root, duration_seconds=5, **kw
) -> Dict[str, Any]:
    """Mock: erzeugt eine minimale MP4 (wenn ffmpeg da) oder fake-Datei."""
    out_dir = Path(out_root) / f"runway_smoke_{run_id}"
    out_dir.mkdir(parents=True, exist_ok=True)
    clip = out_dir / "runway_clip.mp4"
    if _ffmpeg_ok():
        _write_min_mp4(clip)
    else:
        clip.write_bytes(b"\x00" * 256)
    return {
        "ok": True,
        "status": "completed",
        "output_video_path": str(clip),
        "warnings": ["mock_runway_used"],
        "blocking_reasons": [],
    }


def _fake_runway_fail(
    *, image_path, prompt, run_id, out_root, duration_seconds=5, **kw
) -> Dict[str, Any]:
    return {
        "ok": False,
        "status": "blocked",
        "output_video_path": "",
        "warnings": ["mock_runway_blocked"],
        "blocking_reasons": ["runway_api_key_missing"],
    }


# ---------------------------------------------------------------------------
# Test 1: visual_summary.json wird erzeugt
# ---------------------------------------------------------------------------

@pytest.mark.skipif(not _ffmpeg_ok(), reason="ffmpeg not available")
def test_visual_summary_created(ba268_mod, tmp_path):
    script_p = tmp_path / "script.json"
    _minimal_script(script_p, n_chapters=2)

    with patch.dict(os.environ, {"LEONARDO_API_KEY": "test_key_leo", "RUNWAY_API_KEY": "test_key_rw"}, clear=False):
        doc = ba268_mod.run_real_visual_founder_smoke(
            script_json_path=script_p,
            out_dir=tmp_path / "out",
            max_scenes=3,
            duration_seconds=30,
            use_leonardo=True,
            use_runway=True,
            max_runway_scenes=1,
            voice_mode="dummy",
            fit_video_to_voice=False,
            leonardo_beat_fn=_fake_leonardo_ok,
            runway_run_fn=_fake_runway_ok,
        )

    vs_path = tmp_path / "out" / "visual_summary.json"
    assert vs_path.is_file(), "visual_summary.json missing"
    vs = json.loads(vs_path.read_text(encoding="utf-8"))
    assert "used_leonardo_images_count" in vs
    assert "used_runway_videos_count" in vs
    assert "scenes" in vs
    assert vs["used_leonardo_images_count"] >= 1
    assert vs["used_runway_videos_count"] >= 1
    assert doc.get("ba268_visual") is not None


# ---------------------------------------------------------------------------
# Test 2: Provider ohne ENV blockt sauber
# ---------------------------------------------------------------------------

@pytest.mark.skipif(not _ffmpeg_ok(), reason="ffmpeg not available")
def test_missing_env_blocks_cleanly(ba268_mod, tmp_path):
    script_p = tmp_path / "script.json"
    _minimal_script(script_p, n_chapters=2)

    env_clean = {k: v for k, v in os.environ.items()
                 if k not in ("LEONARDO_API_KEY", "RUNWAY_API_KEY", "ELEVENLABS_API_KEY")}
    with patch.dict(os.environ, env_clean, clear=True):
        doc = ba268_mod.run_real_visual_founder_smoke(
            script_json_path=script_p,
            out_dir=tmp_path / "out_noenv",
            max_scenes=2,
            duration_seconds=20,
            use_leonardo=True,
            use_runway=True,
            voice_mode="dummy",
            fit_video_to_voice=False,
        )

    vs_path = tmp_path / "out_noenv" / "visual_summary.json"
    assert vs_path.is_file()
    vs = json.loads(vs_path.read_text(encoding="utf-8"))
    assert vs["used_leonardo_images_count"] == 0
    assert vs["used_runway_videos_count"] == 0
    assert any("missing_api_key" in b for b in vs.get("blocking_reasons") or [])
    assert doc.get("ok") is not None  # no crash


# ---------------------------------------------------------------------------
# Test 3: Fallback-Asset klar markiert
# ---------------------------------------------------------------------------

@pytest.mark.skipif(not _ffmpeg_ok(), reason="ffmpeg not available")
def test_fallback_marked(ba268_mod, tmp_path):
    script_p = tmp_path / "script.json"
    _minimal_script(script_p, n_chapters=2)

    fallback = tmp_path / "fallback.mp4"
    _write_min_mp4(fallback)

    env_clean = {k: v for k, v in os.environ.items()
                 if k not in ("LEONARDO_API_KEY", "RUNWAY_API_KEY")}
    with patch.dict(os.environ, env_clean, clear=True):
        doc = ba268_mod.run_real_visual_founder_smoke(
            script_json_path=script_p,
            out_dir=tmp_path / "out_fb",
            max_scenes=2,
            duration_seconds=20,
            use_leonardo=True,
            use_runway=True,
            voice_mode="dummy",
            fit_video_to_voice=False,
            fallback_clip=fallback,
        )

    vs_path = tmp_path / "out_fb" / "visual_summary.json"
    vs = json.loads(vs_path.read_text(encoding="utf-8"))
    sources = [s.get("source") for s in vs.get("scenes") or []]
    assert any("fallback" in (s or "") for s in sources), f"Expected fallback in sources: {sources}"
    assert any("fallback_existing_runway_clip_used" in w for w in doc.get("warnings") or [])


# ---------------------------------------------------------------------------
# Test 4: Priorität Video > Bild > Fallback
# ---------------------------------------------------------------------------

@pytest.mark.skipif(not _ffmpeg_ok(), reason="ffmpeg not available")
def test_priority_video_over_image_over_fallback(ba268_mod, tmp_path):
    script_p = tmp_path / "script.json"
    _minimal_script(script_p, n_chapters=3)

    fallback = tmp_path / "fallback.mp4"
    _write_min_mp4(fallback)

    call_count = {"leo": 0, "rw": 0}

    def leo_fn(prompt, dest):
        call_count["leo"] += 1
        return _fake_leonardo_ok(prompt, dest)

    def rw_fn(*, image_path, prompt, run_id, out_root, duration_seconds=5, **kw):
        call_count["rw"] += 1
        if call_count["rw"] <= 1:
            return _fake_runway_ok(
                image_path=image_path, prompt=prompt, run_id=run_id,
                out_root=out_root, duration_seconds=duration_seconds,
            )
        return _fake_runway_fail(
            image_path=image_path, prompt=prompt, run_id=run_id,
            out_root=out_root, duration_seconds=duration_seconds,
        )

    with patch.dict(os.environ, {"LEONARDO_API_KEY": "k", "RUNWAY_API_KEY": "k"}, clear=False):
        doc = ba268_mod.run_real_visual_founder_smoke(
            script_json_path=script_p,
            out_dir=tmp_path / "out_prio",
            max_scenes=4,
            duration_seconds=40,
            use_leonardo=True,
            use_runway=True,
            max_runway_scenes=2,
            voice_mode="dummy",
            fit_video_to_voice=False,
            fallback_clip=fallback,
            leonardo_beat_fn=leo_fn,
            runway_run_fn=rw_fn,
        )

    vs_path = tmp_path / "out_prio" / "visual_summary.json"
    vs = json.loads(vs_path.read_text(encoding="utf-8"))
    sources = [s.get("source") for s in vs.get("scenes") or []]
    assert "runway_live" in sources, f"Expected runway_live in {sources}"
    has_image_or_fallback = any(s in ("leonardo_image", "fallback_existing_clip") for s in sources)
    assert has_image_or_fallback, f"Expected non-runway sources too: {sources}"


# ---------------------------------------------------------------------------
# Test 5: run_url_to_final_mp4 nicht gebrochen (BA 26.5 baseline)
# ---------------------------------------------------------------------------

@pytest.mark.skipif(not _ffmpeg_ok(), reason="ffmpeg not available")
def test_ba265_not_broken(ba265_mod, tmp_path):
    script_p = tmp_path / "in265.json"
    _minimal_script(script_p, n_chapters=2)
    out = tmp_path / "out265"
    doc = ba265_mod.run_ba265_url_to_final(
        url=None,
        script_json_path=script_p,
        out_dir=out,
        max_scenes=2,
        duration_seconds=20,
        motion_mode="basic",
    )
    assert doc.get("ok") is True, f"BA265 broken: {doc.get('blocking_reasons')}"
    assert (out / "run_summary.json").is_file()
    assert (out / "final_video.mp4").is_file()


# ---------------------------------------------------------------------------
# Test 6: script_json fehlt → sauberer Blocker
# ---------------------------------------------------------------------------

def test_missing_script_json(ba268_mod, tmp_path):
    doc = ba268_mod.run_real_visual_founder_smoke(
        script_json_path=tmp_path / "nonexistent.json",
        out_dir=tmp_path / "out_missing",
        max_scenes=2,
        duration_seconds=20,
        use_leonardo=False,
        use_runway=False,
        voice_mode="dummy",
        fit_video_to_voice=False,
    )
    assert doc.get("ok") is False
    assert "script_json_missing" in (doc.get("blocking_reasons") or [])


# ---------------------------------------------------------------------------
# Test 7: Leonardo-only (kein Runway) erzeugt visual_summary
# ---------------------------------------------------------------------------

@pytest.mark.skipif(not _ffmpeg_ok(), reason="ffmpeg not available")
def test_leonardo_only_no_runway(ba268_mod, tmp_path):
    script_p = tmp_path / "script.json"
    _minimal_script(script_p, n_chapters=2)

    with patch.dict(os.environ, {"LEONARDO_API_KEY": "test"}, clear=False):
        env_no_rw = {k: v for k, v in os.environ.items() if k != "RUNWAY_API_KEY"}
        with patch.dict(os.environ, env_no_rw, clear=True):
            doc = ba268_mod.run_real_visual_founder_smoke(
                script_json_path=script_p,
                out_dir=tmp_path / "out_leo",
                max_scenes=2,
                duration_seconds=20,
                use_leonardo=True,
                use_runway=True,
                voice_mode="dummy",
                fit_video_to_voice=False,
                leonardo_beat_fn=_fake_leonardo_ok,
            )

    vs = json.loads((tmp_path / "out_leo" / "visual_summary.json").read_text(encoding="utf-8"))
    assert vs["used_leonardo_images_count"] >= 1
    assert vs["used_runway_videos_count"] == 0
    assert any("runway" in b for b in vs.get("blocking_reasons") or [])


# ---------------------------------------------------------------------------
# Test 8: use_leonardo=False / use_runway=False → skipped flags
# ---------------------------------------------------------------------------

@pytest.mark.skipif(not _ffmpeg_ok(), reason="ffmpeg not available")
def test_flags_disable_providers(ba268_mod, tmp_path):
    script_p = tmp_path / "script.json"
    _minimal_script(script_p, n_chapters=2)

    doc = ba268_mod.run_real_visual_founder_smoke(
        script_json_path=script_p,
        out_dir=tmp_path / "out_skip",
        max_scenes=2,
        duration_seconds=20,
        use_leonardo=False,
        use_runway=False,
        voice_mode="dummy",
        fit_video_to_voice=False,
    )

    warns = doc.get("warnings") or []
    assert any("leonardo_skipped" in w for w in warns)
    assert any("runway_skipped" in w for w in warns)
