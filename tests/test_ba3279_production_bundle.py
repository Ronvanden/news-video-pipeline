"""BA 32.79 — Production Bundle (local copy, no providers)."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.founder_dashboard.ba323_video_generate import build_open_me_video_result_html, execute_dashboard_video_generate
from app.main import app
from app.production_connectors.production_bundle import build_production_bundle_v1


def _write_min_files(
    root: Path,
    *,
    with_final: bool = True,
    with_thumb: bool = True,
    with_open_me: bool = True,
) -> dict:
    root.mkdir(parents=True, exist_ok=True)
    if with_final:
        (root / "final_video.mp4").write_bytes(b"fakevid")
    (root / "script.json").write_text("{}", encoding="utf-8")
    (root / "scene_asset_pack.json").write_text("{}", encoding="utf-8")
    (root / "asset_manifest.json").write_text("{}", encoding="utf-8")
    tp_dir = root / "thumbnail_pack"
    tp_dir.mkdir(exist_ok=True)
    (tp_dir / "thumbnail_batch_overlay_result.json").write_text("{}", encoding="utf-8")
    rec = tp_dir / "thumb_rec.png"
    if with_thumb:
        from PIL import Image

        Image.new("RGB", (64, 64), color=(1, 2, 3)).save(rec, format="PNG")
    om = root / "OPEN_ME_VIDEO_RESULT.html"
    if with_open_me:
        om.write_text("<html><body>x</body></html>", encoding="utf-8")
    tp = {
        "thumbnail_pack_status": "ready" if with_thumb else "missing_report",
        "thumbnail_pack_path": str(tp_dir.resolve()),
        "thumbnail_pack_result_path": str((tp_dir / "thumbnail_batch_overlay_result.json").resolve()),
        "thumbnail_recommended_path": str(rec.resolve()) if with_thumb else "",
        "thumbnail_variants": [],
        "thumbnail_generated_count": 1 if with_thumb else 0,
        "thumbnail_top_score": 50 if with_thumb else None,
        "thumbnail_recommended_score": 50 if with_thumb else None,
        "thumbnail_recommended_text_lines": [],
        "thumbnail_recommended_style_preset": "impact_youtube",
    }
    return {
        "final_video_path": str((root / "final_video.mp4").resolve()) if with_final else "",
        "script_path": str((root / "script.json").resolve()),
        "scene_asset_pack_path": str((root / "scene_asset_pack.json").resolve()),
        "asset_manifest_path": str((root / "asset_manifest.json").resolve()),
        "open_me_path": str(om.resolve()) if with_open_me else "",
        "thumbnail_pack": tp,
    }


def test_bundle_ready_all_core(tmp_path: Path) -> None:
    paths = _write_min_files(tmp_path, with_final=True, with_thumb=True, with_open_me=True)
    pb = build_production_bundle_v1(
        output_dir=tmp_path,
        run_id="rid79",
        final_video_path=paths["final_video_path"],
        script_path=paths["script_path"],
        scene_asset_pack_path=paths["scene_asset_pack_path"],
        asset_manifest_path=paths["asset_manifest_path"],
        open_me_path=paths["open_me_path"],
        thumbnail_pack=paths["thumbnail_pack"],
        warnings=[],
    )
    assert pb["production_bundle_version"] == "ba32_79_v1"
    assert pb["production_bundle_status"] == "ready"
    man = Path(pb["production_bundle_manifest_path"])
    assert man.is_file()
    data = json.loads(man.read_text(encoding="utf-8"))
    assert data["status"] == "ready"
    assert data["run_id"] == "rid79"
    assert (tmp_path / "production_bundle" / "final_video.mp4").is_file()
    assert (tmp_path / "production_bundle" / "recommended_thumbnail.png").is_file()
    assert "sk-" not in man.read_text(encoding="utf-8")


def test_bundle_partial_no_thumb(tmp_path: Path) -> None:
    paths = _write_min_files(tmp_path, with_final=True, with_thumb=False, with_open_me=True)
    pb = build_production_bundle_v1(
        output_dir=tmp_path,
        run_id="r",
        final_video_path=paths["final_video_path"],
        script_path=paths["script_path"],
        scene_asset_pack_path=paths["scene_asset_pack_path"],
        asset_manifest_path=paths["asset_manifest_path"],
        open_me_path=paths["open_me_path"],
        thumbnail_pack=paths["thumbnail_pack"],
        warnings=[],
    )
    assert pb["production_bundle_status"] == "partial"


def test_bundle_missing_no_final(tmp_path: Path) -> None:
    paths = _write_min_files(tmp_path, with_final=False, with_thumb=True, with_open_me=True)
    pb = build_production_bundle_v1(
        output_dir=tmp_path,
        run_id="r",
        final_video_path=paths["final_video_path"],
        script_path=paths["script_path"],
        scene_asset_pack_path=paths["scene_asset_pack_path"],
        asset_manifest_path=paths["asset_manifest_path"],
        open_me_path=paths["open_me_path"],
        thumbnail_pack=paths["thumbnail_pack"],
        warnings=[],
    )
    assert pb["production_bundle_status"] == "missing"


def test_open_me_contains_production_bundle_section(tmp_path: Path) -> None:
    paths = _write_min_files(tmp_path)
    pb = build_production_bundle_v1(
        output_dir=tmp_path,
        run_id="x",
        final_video_path=paths["final_video_path"],
        script_path=paths["script_path"],
        scene_asset_pack_path=paths["scene_asset_pack_path"],
        asset_manifest_path=paths["asset_manifest_path"],
        open_me_path=paths["open_me_path"],
        thumbnail_pack=paths["thumbnail_pack"],
        warnings=[],
    )
    html = build_open_me_video_result_html({"ok": True, "run_id": "x", "warnings": [], "blocking_reasons": [], "production_bundle": pb})
    assert "Production Bundle (BA 32.79)" in html


def test_execute_attaches_production_bundle(tmp_path: Path) -> None:
    class _M:
        def run_ba265_url_to_final(self, **kwargs):
            od = Path(kwargs["out_dir"]).resolve()
            od.mkdir(parents=True, exist_ok=True)
            fv = od / "final_video.mp4"
            fv.write_bytes(b"v")
            sp = od / "script.json"
            sp.write_text("{}", encoding="utf-8")
            pk = od / "scene_asset_pack.json"
            pk.write_text("{}", encoding="utf-8")
            mf = od / "asset_manifest.json"
            mf.write_text("{}", encoding="utf-8")
            return {
                "ok": True,
                "title": "T",
                "output_dir": str(od),
                "final_video_path": str(fv),
                "script_path": str(sp),
                "scene_asset_pack_path": str(pk),
                "asset_manifest_path": str(mf),
                "warnings": [],
                "blocking_reasons": [],
            }

    out = tmp_path / "vg79"
    with patch("app.founder_dashboard.ba323_video_generate._load_run_url_to_final_mod", lambda: _M()):
        res = execute_dashboard_video_generate(
            url="https://example.com/a",
            output_dir=out,
            run_id="run79",
            duration_target_seconds=600,
            max_scenes=1,
            max_live_assets=0,
            motion_clip_every_seconds=60,
            motion_clip_duration_seconds=10,
            max_motion_clips=0,
            allow_live_assets=False,
            allow_live_motion=False,
            voice_mode="none",
            motion_mode="basic",
        )
    assert "production_bundle" in res
    pb = res["production_bundle"]
    assert pb.get("production_bundle_version") == "ba32_79_v1"
    assert Path(pb["production_bundle_path"]).is_dir()


def test_route_finalize_bundle_with_open_me(tmp_path: Path, monkeypatch) -> None:
    """Route schreibt OPEN_ME und finalisiert Bundle mit open_me_path."""
    captured_run: dict = {}

    def _fake_execute(**kwargs):
        captured_run.update(kwargs)
        od = kwargs["output_dir"]
        od = Path(od)
        od.mkdir(parents=True, exist_ok=True)
        fv = od / "final_video.mp4"
        fv.write_bytes(b"x")
        sp = od / "script.json"
        sp.write_text("{}", encoding="utf-8")
        pk = od / "pack.json"
        pk.write_text("{}", encoding="utf-8")
        mf = od / "man.json"
        mf.write_text("{}", encoding="utf-8")
        return {
            "ok": True,
            "run_id": kwargs.get("run_id", "r"),
            "output_dir": str(od),
            "final_video_path": str(fv),
            "script_path": str(sp),
            "scene_asset_pack_path": str(pk),
            "asset_manifest_path": str(mf),
            "warnings": [],
            "blocking_reasons": [],
            "readiness_audit": {},
            "voice_artifact": {},
            "image_asset_audit": {},
            "thumbnail_pack": {"thumbnail_pack_status": "missing_report"},
        }

    monkeypatch.setattr(
        "app.routes.founder_dashboard.video_generate_output_dir",
        lambda out_root, run_id: tmp_path / "route79" / run_id,
    )
    monkeypatch.setattr(
        "app.routes.founder_dashboard.new_video_gen_run_id",
        lambda: "run_route79",
    )

    client = TestClient(app)
    with patch("app.routes.founder_dashboard.execute_dashboard_video_generate", side_effect=_fake_execute):
        r = client.post(
            "/founder/dashboard/video/generate",
            json={
                "url": "https://example.com/b",
                "confirm_provider_costs": False,
                "voice_mode": "none",
                "max_scenes": 1,
                "max_live_assets": 1,
                "max_motion_clips": 0,
            },
        )
    assert r.status_code == 200, r.text
    body = r.json()
    pb = body.get("production_bundle") or {}
    om = body.get("open_me_report_path") or ""
    assert om
    assert (Path(om).parent / "production_bundle" / "OPEN_ME_VIDEO_RESULT.html").is_file()
    assert pb.get("production_bundle_status") in ("ready", "partial", "missing")
