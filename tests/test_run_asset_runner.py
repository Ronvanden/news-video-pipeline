"""BA 19.0 / BA 20.2 — run_asset_runner.py Placeholder + Leonardo live."""

from __future__ import annotations

import importlib.util
import json
from io import BytesIO
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError

import pytest
from PIL import Image

_ROOT = Path(__file__).resolve().parents[1]
_SCRIPT = _ROOT / "scripts" / "run_asset_runner.py"


@pytest.fixture(scope="module")
def asset_runner_mod():
    spec = importlib.util.spec_from_file_location("run_asset_runner", _SCRIPT)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _minimal_pack(tmp_path: Path) -> Path:
    pack = {
        "export_version": "18.2-v1",
        "scene_expansion": {
            "expanded_scene_assets": [
                {
                    "chapter_index": 0,
                    "beat_index": 0,
                    "visual_prompt": "Establishing wide shot of the city skyline at dusk.",
                    "camera_motion_hint": "slow push-in",
                    "duration_seconds": 10,
                    "asset_type": "establishing",
                    "continuity_note": "",
                    "safety_notes": [],
                },
                {
                    "chapter_index": 0,
                    "beat_index": 1,
                    "visual_prompt": "Detail: documents on a desk.",
                    "camera_motion_hint": "static",
                    "duration_seconds": 8,
                    "asset_type": "detail",
                    "continuity_note": "match prior",
                    "safety_notes": [],
                },
            ],
        },
    }
    p = tmp_path / "scene_asset_pack.json"
    p.write_text(json.dumps(pack), encoding="utf-8")
    return p


def _five_beat_pack(tmp_path: Path) -> Path:
    beats = []
    for j in range(5):
        beats.append(
            {
                "chapter_index": 0,
                "beat_index": j,
                "visual_prompt": f"Beat {j} establishing shot.",
                "camera_motion_hint": "static",
                "duration_seconds": 6,
                "asset_type": "establishing",
                "continuity_note": "",
                "safety_notes": [],
            }
        )
    p = tmp_path / "pack5.json"
    p.write_text(
        json.dumps({"export_version": "18.2-v1", "scene_expansion": {"expanded_scene_assets": beats}}),
        encoding="utf-8",
    )
    return p


def test_placeholder_png_cinematic_draft_look(asset_runner_mod, tmp_path):
    """BA 20.2b — Placeholder ist kein Flachgrau; 960×540; Gradient erkennbar."""
    pack = _minimal_pack(tmp_path)
    meta = asset_runner_mod.run_local_asset_runner(
        pack, tmp_path / "out", run_id="polish20b", mode="placeholder"
    )
    from PIL import Image

    p = Path(meta["output_dir"]) / "scene_001.png"
    im = Image.open(p).convert("RGB")
    assert im.size == (960, 540)
    top = im.getpixel((480, 8))
    bottom = im.getpixel((480, 531))
    assert top != bottom


def test_placeholder_creates_pngs_and_manifest(asset_runner_mod, tmp_path):
    pack = _minimal_pack(tmp_path)
    out_root = tmp_path / "out"
    meta = asset_runner_mod.run_local_asset_runner(
        pack,
        out_root,
        run_id="testrun19",
        mode="placeholder",
    )
    assert meta["ok"] is True
    assert meta["asset_count"] == 2
    out_dir = Path(meta["output_dir"])
    assert (out_dir / "scene_001.png").is_file()
    assert (out_dir / "scene_002.png").is_file()
    man = json.loads((out_dir / "asset_manifest.json").read_text(encoding="utf-8"))
    assert man["run_id"] == "testrun19"
    assert man["asset_count"] == 2
    assert man["generation_mode"] == "placeholder"
    assert len(man["assets"]) == 2
    assert man["assets"][0]["scene_number"] == 1
    assert man["assets"][0]["image_path"] == "scene_001.png"
    assert "visual_prompt" in man["assets"][0]
    # BA 26.4c: Operator-Transparenz (additiv)
    a0 = man["assets"][0]
    assert "visual_prompt_raw" in a0
    assert "visual_prompt_effective" in a0
    assert "visual_text_guard_applied" in a0
    assert "visual_policy_status" in a0
    assert "visual_policy_warnings" in a0
    assert "provider_routing_reason" in a0
    assert "[visual_no_text_guard_v26_4]" in str(a0.get("visual_prompt_effective") or "")
    assert man["assets"][0]["generation_mode"] == "placeholder"


def test_openai_images_routed_uses_adapter_dry_run(asset_runner_mod, tmp_path, monkeypatch):
    # No key required for dry-run; ensure no accidental live calls.
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    pack = {
        "export_version": "18.2-v1",
        "scene_expansion": {
            "expanded_scene_assets": [
                {
                    "chapter_index": 0,
                    "beat_index": 0,
                    "visual_prompt": "Thumbnail base frame, clean negative space reserved for later editorial overlay.",
                    "visual_prompt_effective": "Thumbnail base frame, clean negative space reserved for later editorial overlay.\n\n[visual_no_text_guard_v26_4]\nNo readable text.",
                    "visual_prompt_raw": "Thumbnail base frame, clean negative space reserved for later editorial overlay.",
                    "overlay_intent": [],
                    "text_sensitive": False,
                    "visual_asset_kind": "thumbnail_base",
                    "routed_visual_provider": "openai_images",
                    "routed_image_provider": "",
                    "camera_motion_hint": "static",
                    "duration_seconds": 6,
                    "asset_type": "thumbnail_base",
                    "continuity_note": "",
                    "safety_notes": [],
                }
            ]
        },
    }
    p = tmp_path / "scene_asset_pack_openai.json"
    p.write_text(json.dumps(pack), encoding="utf-8")
    meta = asset_runner_mod.run_local_asset_runner(
        p,
        tmp_path / "out",
        run_id="oai_dry",
        mode="placeholder",
    )
    out_dir = Path(meta["output_dir"])
    man = json.loads((out_dir / "asset_manifest.json").read_text(encoding="utf-8"))
    a0 = man["assets"][0]
    assert a0.get("provider_used") == "openai_images"
    assert a0.get("provider_status") == "dry_run_ready"
    assert a0.get("generation_mode") == "openai_images_dry_run"
    assert "[visual_no_text_guard_v26_4]" in str(a0.get("prompt_used_effective") or "")
    assert (out_dir / "scene_001.png").is_file()


def test_missing_pack_raises_cleanly_via_runner(asset_runner_mod, tmp_path):
    with pytest.raises(FileNotFoundError):
        asset_runner_mod.run_local_asset_runner(
            tmp_path / "nope.json",
            tmp_path / "out",
            run_id="x",
            mode="placeholder",
        )


def test_empty_beats_raises(asset_runner_mod, tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text(json.dumps({"scene_expansion": {"expanded_scene_assets": []}}), encoding="utf-8")
    with pytest.raises(ValueError, match="empty"):
        asset_runner_mod.run_local_asset_runner(bad, tmp_path / "out", run_id="y", mode="placeholder")


def test_live_without_key_fallback_all_placeholders(asset_runner_mod, tmp_path, monkeypatch):
    monkeypatch.delenv("LEONARDO_API_KEY", raising=False)
    pack = _minimal_pack(tmp_path)
    meta = asset_runner_mod.run_local_asset_runner(
        pack,
        tmp_path / "out",
        run_id="liveskip",
        mode="live",
    )
    assert meta["ok"] is True
    assert meta["asset_count"] == 2
    out_dir = Path(meta["output_dir"])
    man = json.loads((out_dir / "asset_manifest.json").read_text(encoding="utf-8"))
    assert man["generation_mode"] == "leonardo_fallback_placeholder"
    assert "leonardo_env_missing_fallback_placeholder" in meta["warnings"]
    assert (out_dir / "scene_001.png").is_file()
    assert (out_dir / "scene_002.png").is_file()
    assert all(a["generation_mode"] == "leonardo_fallback_placeholder" for a in man["assets"])


def test_live_max_assets_limits_leonardo_attempts(asset_runner_mod, tmp_path, monkeypatch):
    monkeypatch.setenv("LEONARDO_API_KEY", "fake-key")

    def fake_beat(vp: str, dest: Path) -> tuple[bool, list[str]]:
        dest.write_bytes(b"\x89PNG\r\n\x1a\n")
        return True, []

    pack = _five_beat_pack(tmp_path)
    meta = asset_runner_mod.run_local_asset_runner(
        pack,
        tmp_path / "out",
        run_id="cap20",
        mode="live",
        max_assets_live=2,
        leonardo_beat_fn=fake_beat,
    )
    assert meta["ok"] is True
    man = json.loads((Path(meta["output_dir"]) / "asset_manifest.json").read_text(encoding="utf-8"))
    assert man["asset_count"] == 5
    assert man["assets"][0]["generation_mode"] == "leonardo_live"
    assert man["assets"][1]["generation_mode"] == "leonardo_live"
    assert man["assets"][2]["generation_mode"] == "placeholder"
    assert any("leonardo_live_max_assets_cap:2" in w for w in meta["warnings"])
    assert any("live_image_max_assets_cap:2" in w for w in meta["warnings"])
    assert any("live_image_provider:leonardo" in w for w in meta["warnings"])
    assert man["generation_mode"] == "leonardo_live"


def test_live_failed_beat_placeholder_continues(asset_runner_mod, tmp_path, monkeypatch):
    monkeypatch.setenv("LEONARDO_API_KEY", "fake-key")
    n = {"c": 0}

    def fake_beat(vp: str, dest: Path) -> tuple[bool, list[str]]:
        n["c"] += 1
        if n["c"] == 1:
            return False, ["mock_fail"]
        dest.write_bytes(b"\x89PNG\r\n\x1a\n")
        return True, []

    pack = _minimal_pack(tmp_path)
    meta = asset_runner_mod.run_local_asset_runner(
        pack,
        tmp_path / "out",
        run_id="failmix",
        mode="live",
        max_assets_live=10,
        leonardo_beat_fn=fake_beat,
    )
    assert meta["ok"] is True
    man = json.loads((Path(meta["output_dir"]) / "asset_manifest.json").read_text(encoding="utf-8"))
    assert man["assets"][0]["generation_mode"] == "leonardo_fallback_placeholder"
    assert man["assets"][1]["generation_mode"] == "leonardo_live"
    assert man["generation_mode"] == "leonardo_fallback_placeholder"
    assert any("leonardo_live_beat_failed_fallback_placeholder:1" in w for w in meta["warnings"])


def test_live_leonardo_beat_fn_ignores_ambient_openai_provider(asset_runner_mod, tmp_path, monkeypatch):
    monkeypatch.setenv("IMAGE_PROVIDER", "openai_image")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("LEONARDO_API_KEY", raising=False)
    calls = {"count": 0}

    def fake_beat(vp: str, dest: Path) -> tuple[bool, list[str]]:
        calls["count"] += 1
        dest.write_bytes(b"\x89PNG\r\n\x1a\n")
        return True, []

    pack = _minimal_pack(tmp_path)
    meta = asset_runner_mod.run_local_asset_runner(
        pack,
        tmp_path / "out",
        run_id="leofn_env_openai",
        mode="live",
        max_assets_live=2,
        leonardo_beat_fn=fake_beat,
    )
    man = json.loads((Path(meta["output_dir"]) / "asset_manifest.json").read_text(encoding="utf-8"))
    assert calls["count"] == 2
    assert meta["effective_image_provider"] == "leonardo"
    assert man["generation_mode"] == "leonardo_live"
    assert all(a["generation_mode"] == "leonardo_live" for a in man["assets"])
    assert "openai_image_key_missing_fallback_placeholder" not in meta["warnings"]


def test_chunk_helpers_generation_id_nested(asset_runner_mod):
    gid = asset_runner_mod._generation_id_from_dict(
        {"sdGenerationJob": {"generationId": "abc-123", "status": "PENDING"}}
    )
    assert gid == "abc-123"


def test_download_leonardo_image_url_success_png(asset_runner_mod, tmp_path):
    buf = BytesIO()
    Image.new("RGB", (4, 4), color="red").save(buf, format="PNG")
    png = buf.getvalue()

    class Resp:
        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        headers = {"Content-Type": "image/png"}

        def read(self):
            return png

        def getcode(self):
            return 200

    dest = tmp_path / "scene_dl.png"
    with patch.object(asset_runner_mod, "urlopen", return_value=Resp()):
        ok, warns = asset_runner_mod._download_leonardo_image_url(
            "https://cdn.example.test/path/img.png?token=NEVER_LEAK",
            dest,
            10.0,
        )
    assert ok is True
    assert dest.is_file()
    assert dest.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"
    blob = " ".join(warns)
    assert "NEVER_LEAK" not in blob
    assert "token=" not in blob


def test_download_leonardo_image_url_jpeg_converted_to_png(asset_runner_mod, tmp_path):
    buf = BytesIO()
    Image.new("RGB", (16, 16), color=(40, 50, 60)).save(buf, format="JPEG", quality=90)
    jpeg = buf.getvalue()

    class Resp:
        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        headers = {"Content-Type": "image/jpeg"}

        def read(self):
            return jpeg

        def getcode(self):
            return 200

    dest = tmp_path / "scene_dl.png"
    with patch.object(asset_runner_mod, "urlopen", return_value=Resp()):
        ok, warns = asset_runner_mod._download_leonardo_image_url(
            "https://cdn.leonardo.ai/user-static/image.jpg?signature=TOPSECRETVALUE",
            dest,
            10.0,
        )
    assert ok is True
    assert dest.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"
    joined = " ".join(warns)
    assert "TOPSECRETVALUE" not in joined
    assert "signature=" not in joined


def test_download_leonardo_image_url_http_error_no_secret_in_warning(asset_runner_mod, tmp_path):
    err = HTTPError(
        "https://cdn.test/x?apiKey=SECRET123",
        403,
        "Forbidden",
        {"Content-Type": "application/json"},
        BytesIO(b"{}"),
    )
    dest = tmp_path / "f.png"
    with patch.object(asset_runner_mod, "urlopen", side_effect=err):
        ok, warns = asset_runner_mod._download_leonardo_image_url(
            "https://cdn.test/x?apiKey=SECRET123",
            dest,
            5.0,
        )
    assert ok is False
    text = " ".join(warns)
    assert "SECRET123" not in text
    assert "apiKey=" not in text
    assert "status=403" in text or "403" in text
    assert "cdn.test" in text
