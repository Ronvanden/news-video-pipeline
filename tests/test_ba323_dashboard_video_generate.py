"""BA 32.3 — Founder Dashboard POST /founder/dashboard/video/generate."""

from __future__ import annotations

import os
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app
from app.founder_dashboard.ba323_video_generate import derive_video_generate_status
from app.founder_dashboard.ba323_video_generate import execute_dashboard_video_generate
from app.founder_dashboard.ba323_video_generate import resolve_voice_mode_dashboard
from app.founder_dashboard.ba323_video_generate import build_voice_artifact
from app.founder_dashboard.ba323_video_generate import build_asset_artifact
from app.founder_dashboard.ba323_video_generate import build_video_generate_operator_ui_ba3280
from app.founder_dashboard.ba323_video_generate import build_open_me_video_result_html
from app.founder_dashboard.ba323_video_generate import _qc_rows
from app.founder_dashboard.ba323_video_generate import derive_motion_readiness_fields


class Ba323VideoGenerateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app)

    def test_missing_url_body_422(self) -> None:
        r = self.client.post("/founder/dashboard/video/generate", json={})
        self.assertEqual(r.status_code, 422)

    def test_blank_url_422(self) -> None:
        r = self.client.post("/founder/dashboard/video/generate", json={"url": "   "})
        self.assertEqual(r.status_code, 422)

    def test_raw_text_allows_missing_url(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            out_root = Path(td).resolve()
            out_dir = (out_root / "video_generate" / "video_gen_10m_test_raw").resolve()
            out_dir.mkdir(parents=True, exist_ok=True)
            with patch("app.routes.founder_dashboard.default_local_preview_out_root", lambda: out_root):
                with patch("app.routes.founder_dashboard.execute_dashboard_video_generate") as mock_exec:
                    mock_exec.return_value = {
                        "ok": True,
                        "run_id": "video_gen_10m_test_raw",
                        "output_dir": str(out_dir),
                        "final_video_path": str(out_dir / "final_video.mp4"),
                        "script_path": str(out_dir / "script.json"),
                        "scene_asset_pack_path": str(out_dir / "scene_asset_pack.json"),
                        "asset_manifest_path": str(out_dir / "asset_manifest.json"),
                        "duration_target_seconds": 600,
                        "max_scenes": 24,
                        "max_live_assets": 24,
                        "motion_strategy": {},
                        "warnings": ["raw_text_input_used"],
                        "blocking_reasons": [],
                        "next_action": "Final Video prüfen",
                    }
                    r = self.client.post(
                        "/founder/dashboard/video/generate",
                        json={"raw_text": "Kurzer Text für Smoke.", "title": "Smoke"},
                    )
        self.assertEqual(r.status_code, 200, msg=r.text)

    def test_live_assets_without_cost_confirm_422(self) -> None:
        r = self.client.post(
            "/founder/dashboard/video/generate",
            json={
                "url": "https://example.com/article",
                "allow_live_assets": True,
                "confirm_provider_costs": False,
            },
        )
        self.assertEqual(r.status_code, 422)
        self.assertEqual(r.json().get("detail"), "confirm_provider_costs_required_when_live_flags")

    def test_live_motion_without_runway_422(self) -> None:
        with patch.dict(os.environ, {"RUNWAY_API_KEY": ""}, clear=False):
            r = self.client.post(
                "/founder/dashboard/video/generate",
                json={
                    "url": "https://example.com/article",
                    "allow_live_motion": True,
                    "confirm_provider_costs": True,
                },
            )
        self.assertEqual(r.status_code, 422)
        self.assertEqual(r.json().get("detail"), "live_motion_requires_runway_connector")

    @patch("app.routes.founder_dashboard.execute_dashboard_video_generate")
    def test_forwards_duration_and_scene_caps(self, mock_exec) -> None:
        with tempfile.TemporaryDirectory() as td:
            out_root = Path(td).resolve()
            out_dir = (out_root / "video_generate" / "video_gen_10m_test").resolve()
            out_dir.mkdir(parents=True, exist_ok=True)
        mock_exec.return_value = {
            "ok": True,
            "run_id": "video_gen_10m_test",
            "output_dir": str(out_dir),
            "final_video_path": str(out_dir / "final_video.mp4"),
            "script_path": str(out_dir / "script.json"),
            "scene_asset_pack_path": str(out_dir / "scene_asset_pack.json"),
            "asset_manifest_path": str(out_dir / "asset_manifest.json"),
            "duration_target_seconds": 600,
            "max_scenes": 24,
            "max_live_assets": 24,
            "motion_strategy": {},
            "warnings": [],
            "blocking_reasons": [],
            "next_action": "Final Video prüfen",
            # BA 32.49 — OPEN_ME Timing: Dauerfelder als X.XXs (JSON bleibt numerisch)
            "timing_audit": {
                "voice_duration_seconds": 28.93,
                "timeline_duration_seconds": 36.93,
                "final_video_duration_seconds": 36.93,
                "requested_duration_seconds": 600,
                "timing_gap_abs_seconds": 8.0,
                "timing_gap_status": "major_gap",
                "summary": "Smoke timing row",
            },
        }
        with patch("app.routes.founder_dashboard.default_local_preview_out_root", lambda: out_root):
            r = self.client.post(
                "/founder/dashboard/video/generate",
                json={"url": "https://example.com/a", "duration_target_seconds": 600, "max_scenes": 24},
            )
        self.assertEqual(r.status_code, 200, msg=r.text)
        mock_exec.assert_called_once()
        kw = mock_exec.call_args.kwargs
        self.assertEqual(kw["duration_target_seconds"], 600)
        self.assertEqual(kw["max_scenes"], 24)
        self.assertEqual(kw["max_live_assets"], 24)
        self.assertFalse(kw["enable_youtube_packaging"])
        data = r.json()
        self.assertTrue(data.get("open_me_report_path"), msg="open_me_report_path missing")
        self.assertIn("readiness_audit", data)
        ta = data.get("timing_audit") or {}
        self.assertEqual(ta.get("voice_duration_seconds"), 28.93)
        self.assertEqual(ta.get("requested_duration_seconds"), 600)
        p = Path(str(data["open_me_report_path"])).resolve()
        self.assertTrue(p.exists(), msg=f"report file missing: {p}")
        txt = p.read_text(encoding="utf-8")
        self.assertIn("Video Generate Ergebnis", txt)
        self.assertIn("video_gen_10m_test", txt)
        self.assertIn("Produktions-Check", txt)
        self.assertIn("Timing / Voice Fit", txt)
        self.assertIn("28.93s", txt)
        self.assertIn("600.00s", txt)
        self.assertIn("8.00s", txt)
        self.assertIn("Readiness Audit", txt)
        self.assertIn("Voice Artifact", txt)
        self.assertIn("Smoke Result", txt)
        self.assertIn("Asset Artifact", txt)

    @patch("app.routes.founder_dashboard.execute_dashboard_video_generate")
    def test_forwards_youtube_packaging_flag(self, mock_exec) -> None:
        with tempfile.TemporaryDirectory() as td:
            out_root = Path(td).resolve()
            out_dir = (out_root / "video_generate" / "video_gen_10m_packaging").resolve()
            out_dir.mkdir(parents=True, exist_ok=True)
            mock_exec.return_value = {
                "ok": True,
                "run_id": "video_gen_10m_packaging",
                "output_dir": str(out_dir),
                "final_video_path": str(out_dir / "final_video.mp4"),
                "script_path": str(out_dir / "script.json"),
                "scene_asset_pack_path": str(out_dir / "scene_asset_pack.json"),
                "asset_manifest_path": str(out_dir / "asset_manifest.json"),
                "duration_target_seconds": 600,
                "max_scenes": 24,
                "max_live_assets": 24,
                "motion_strategy": {},
                "youtube_packaging": {
                    "packaging_applied": True,
                    "manifest_path": str(out_dir / "youtube_packaging_manifest.json"),
                },
                "warnings": [],
                "blocking_reasons": [],
                "next_action": "Final Video prÃ¼fen",
            }
            with patch("app.routes.founder_dashboard.default_local_preview_out_root", lambda: out_root):
                r = self.client.post(
                    "/founder/dashboard/video/generate",
                    json={"url": "https://example.com/a", "enable_youtube_packaging": True},
                )
        self.assertEqual(r.status_code, 200, msg=r.text)
        self.assertTrue(mock_exec.call_args.kwargs["enable_youtube_packaging"])
        self.assertTrue((r.json().get("youtube_packaging") or {}).get("packaging_applied"))

    @patch("app.routes.founder_dashboard.execute_dashboard_video_generate")
    def test_response_includes_version(self, mock_exec) -> None:
        mock_exec.return_value = {
            "ok": False,
            "run_id": "x",
            "output_dir": "",
            "final_video_path": "",
            "script_path": "",
            "scene_asset_pack_path": "",
            "asset_manifest_path": None,
            "duration_target_seconds": 600,
            "max_scenes": 24,
            "max_live_assets": 24,
            "motion_strategy": {"live_motion_available": False},
            "warnings": [],
            "blocking_reasons": ["x"],
            "next_action": "Fehler prüfen",
        }
        r = self.client.post("/founder/dashboard/video/generate", json={"url": "https://example.com/b"})
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertEqual(data.get("video_generate_version"), "ba32_3_v1")

    def test_derive_video_generate_status_fallback_signals_match_dashboard(self) -> None:
        p_ok = {
            "ok": True,
            "blocking_reasons": [],
            "final_video_path": "/tmp/final_video.mp4",
            "warnings": ["no_assets_in_asset_dir_using_placeholder"],
        }
        self.assertEqual(derive_video_generate_status(p_ok), "fallback_preview")
        p_ok2 = {
            "ok": True,
            "blocking_reasons": [],
            "final_video_path": "/tmp/final_video.mp4",
            "warnings": ["ba323_voice_mode_fallback_dummy_no_elevenlabs_key"],
        }
        self.assertEqual(derive_video_generate_status(p_ok2), "fallback_preview")
        p_prod = {
            "ok": True,
            "blocking_reasons": [],
            "final_video_path": "/tmp/final_video.mp4",
            "warnings": ["some_unrelated_warning"],
        }
        self.assertEqual(derive_video_generate_status(p_prod), "production_ready")
        p_fail = {
            "ok": False,
            "blocking_reasons": ["x"],
            "warnings": [],
        }
        self.assertEqual(derive_video_generate_status(p_fail), "blocked")

    def test_derive_video_generate_status_blocks_ok_payload_without_final_video(self) -> None:
        payload = {
            "ok": True,
            "run_id": "video_gen_missing_final",
            "output_dir": "/tmp/video_gen_missing_final",
            "blocking_reasons": [],
            "warnings": [],
            "script_path": "/tmp/video_gen_missing_final/script.json",
            "scene_asset_pack_path": "/tmp/video_gen_missing_final/scene_asset_pack.json",
            "asset_manifest_path": "/tmp/video_gen_missing_final/asset_manifest.json",
            "final_video_path": "",
        }

        self.assertEqual(derive_video_generate_status(payload), "blocked")
        self.assertIn("final_video_path_missing", payload["blocking_reasons"])
        self.assertIn("final_video_path_missing_no_final_render", payload["warnings"])
        op = build_video_generate_operator_ui_ba3280("blocked", payload)
        self.assertEqual(op["headline"], "Kein final_video.mp4 erzeugt")

    def test_readiness_audit_live_assets_not_requested_sets_blocker(self) -> None:
        class _FakeMod:
            def run_ba265_url_to_final(self, **kwargs):
                out_dir = Path(str(kwargs.get("out_dir") or "")).resolve()
                gen_dir = out_dir / "generated_assets_x"
                gen_dir.mkdir(parents=True, exist_ok=True)
                (gen_dir / "scene_001.png").write_bytes(b"\x89PNG\r\n\x1a\n")
                mp = gen_dir / "asset_manifest.json"
                mp.write_text(
                    json.dumps(
                        {
                            "asset_count": 1,
                            "generation_mode": "placeholder",
                            "warnings": [],
                            "assets": [{"image_path": "scene_001.png", "generation_mode": "placeholder"}],
                        }
                    ),
                    encoding="utf-8",
                )
                return {
                    "ok": True,
                    "output_dir": str(out_dir),
                    "final_video_path": "",
                    "script_path": "x/script.json",
                    "scene_asset_pack_path": "x/scene_asset_pack.json",
                    "asset_manifest_path": str(mp),
                    "warnings": ["no_assets_in_asset_dir_using_placeholder"],
                    "blocking_reasons": [],
                }

        with patch("app.founder_dashboard.ba323_video_generate._load_run_url_to_final_mod", lambda: _FakeMod()):
            out = execute_dashboard_video_generate(
                url="https://example.com/a",
                output_dir=Path(tempfile.gettempdir()) / "vg_audit",
                run_id="x",
                duration_target_seconds=600,
                max_scenes=24,
                max_live_assets=24,
                motion_clip_every_seconds=60,
                motion_clip_duration_seconds=10,
                max_motion_clips=10,
                allow_live_assets=False,
                allow_live_motion=False,
                voice_mode="none",
                motion_mode="basic",
            )
        ra = out.get("readiness_audit") or {}
        self.assertFalse(ra.get("requested_live_assets"))
        self.assertIn("live_assets_not_requested", ra.get("provider_blockers") or [])
        self.assertTrue(ra.get("silent_render_expected"))
        self.assertEqual(ra.get("silent_render_reason"), "voice_mode_none")

    def test_readiness_audit_silent_render_not_expected_when_voice_dummy(self) -> None:
        class _FakeMod:
            def run_ba265_url_to_final(self, **kwargs):
                out_dir = Path(str(kwargs.get("out_dir") or "")).resolve()
                gen_dir = out_dir / "generated_assets_dum"
                gen_dir.mkdir(parents=True, exist_ok=True)
                (gen_dir / "scene_001.png").write_bytes(b"\x89PNG\r\n\x1a\n")
                mp = gen_dir / "asset_manifest.json"
                mp.write_text(
                    json.dumps(
                        {
                            "asset_count": 1,
                            "generation_mode": "placeholder",
                            "warnings": [],
                            "assets": [{"image_path": "scene_001.png", "generation_mode": "placeholder"}],
                        }
                    ),
                    encoding="utf-8",
                )
                return {
                    "ok": True,
                    "output_dir": str(out_dir),
                    "final_video_path": "",
                    "script_path": "x/script.json",
                    "scene_asset_pack_path": "x/scene_asset_pack.json",
                    "asset_manifest_path": str(mp),
                    "warnings": [],
                    "blocking_reasons": [],
                }

        with patch("app.founder_dashboard.ba323_video_generate._load_run_url_to_final_mod", lambda: _FakeMod()):
            out = execute_dashboard_video_generate(
                url="https://example.com/a",
                output_dir=Path(tempfile.gettempdir()) / "vg_silent_audit",
                run_id="xdum",
                duration_target_seconds=600,
                max_scenes=24,
                max_live_assets=24,
                motion_clip_every_seconds=60,
                motion_clip_duration_seconds=10,
                max_motion_clips=10,
                allow_live_assets=False,
                allow_live_motion=False,
                voice_mode="dummy",
                motion_mode="basic",
            )
        ra = out.get("readiness_audit") or {}
        self.assertFalse(ra.get("silent_render_expected"))
        self.assertIsNone(ra.get("silent_render_reason"))

    def test_readiness_audit_live_assets_requested_but_not_configured_sets_blockers(self) -> None:
        class _FakeMod:
            def run_ba265_url_to_final(self, **kwargs):
                out_dir = Path(str(kwargs.get("out_dir") or "")).resolve()
                gen_dir = out_dir / "generated_assets_x2"
                gen_dir.mkdir(parents=True, exist_ok=True)
                (gen_dir / "scene_001.png").write_bytes(b"\x89PNG\r\n\x1a\n")
                mp = gen_dir / "asset_manifest.json"
                mp.write_text(
                    json.dumps(
                        {
                            "asset_count": 1,
                            "generation_mode": "placeholder",
                            "warnings": ["leonardo_env_missing_fallback_placeholder"],
                            "assets": [{"image_path": "scene_001.png", "generation_mode": "placeholder"}],
                        }
                    ),
                    encoding="utf-8",
                )
                return {
                    "ok": True,
                    "output_dir": str(out_dir),
                    "final_video_path": "",
                    "script_path": "x/script.json",
                    "scene_asset_pack_path": "x/scene_asset_pack.json",
                    "asset_manifest_path": str(mp),
                    "warnings": [
                        "leonardo_env_missing_fallback_placeholder",
                        "no_assets_in_asset_dir_using_placeholder",
                    ],
                    "blocking_reasons": [],
                }

        with patch("app.founder_dashboard.ba323_video_generate._load_run_url_to_final_mod", lambda: _FakeMod()):
            out = execute_dashboard_video_generate(
                url="https://example.com/a",
                output_dir=Path(tempfile.gettempdir()) / "vg_audit2",
                run_id="x2",
                duration_target_seconds=600,
                max_scenes=24,
                max_live_assets=24,
                motion_clip_every_seconds=60,
                motion_clip_duration_seconds=10,
                max_motion_clips=10,
                allow_live_assets=True,
                allow_live_motion=False,
                voice_mode="none",
                motion_mode="basic",
            )
        ra = out.get("readiness_audit") or {}
        self.assertTrue(ra.get("requested_live_assets"))
        blockers = ra.get("provider_blockers") or []
        self.assertIn("live_asset_provider_not_configured", blockers)
        self.assertIn("no_real_asset_files", blockers)

    def test_resolve_voice_mode_dummy(self) -> None:
        vm, warns = resolve_voice_mode_dashboard("dummy")
        self.assertEqual(vm, "dummy")
        self.assertEqual(warns, [])

    def test_resolve_voice_mode_elevenlabs_missing_key_falls_back(self) -> None:
        with patch.dict(os.environ, {"ELEVENLABS_API_KEY": ""}, clear=False):
            vm, warns = resolve_voice_mode_dashboard("elevenlabs")
        self.assertEqual(vm, "dummy")
        self.assertTrue(any("ba323_voice_elevenlabs_requested_fallback_dummy" in w for w in warns))

    def test_resolve_voice_mode_openai_missing_key_falls_back(self) -> None:
        with patch.dict(os.environ, {"OPENAI_API_KEY": ""}, clear=False):
            vm, warns = resolve_voice_mode_dashboard("openai")
        self.assertEqual(vm, "dummy")
        self.assertTrue(any("ba323_voice_openai_requested_fallback_dummy" in w for w in warns))

    def test_build_voice_artifact_none_mode(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            out_dir = Path(td).resolve()
            va = build_voice_artifact(
                output_dir=out_dir,
                requested_voice_mode="none",
                effective_voice_mode="none",
            )
        self.assertFalse(va.get("voice_ready"))
        self.assertFalse(va.get("is_dummy"))
        self.assertIsNone(va.get("voice_file_path"))

    def test_build_voice_artifact_dummy_mode_with_missing_file_sets_warning(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            out_dir = Path(td).resolve()
            # simulate run_summary.json pointing to a file that does not exist
            (out_dir / "run_summary.json").write_text(
                '{"voice_file_path":"C:/nope/voiceover.mp3","voice_duration_seconds":8,"voice_warnings":["dummy_voice_used_not_real_tts"]}',
                encoding="utf-8",
            )
            va = build_voice_artifact(
                output_dir=out_dir,
                requested_voice_mode="dummy",
                effective_voice_mode="dummy",
            )
        self.assertTrue(va.get("is_dummy"))
        self.assertFalse(va.get("voice_ready"))
        self.assertIn("voice_file_missing", va.get("warnings") or [])

    def test_build_asset_artifact_counts_real_vs_placeholder(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            out_dir = Path(td).resolve()
            gen_dir = out_dir / "generated_assets_x"
            gen_dir.mkdir(parents=True, exist_ok=True)
            # create two files: one placeholder, one real
            (gen_dir / "scene_001.png").write_bytes(b"\x89PNG\r\n\x1a\n")
            (gen_dir / "scene_002.png").write_bytes(b"\x89PNG\r\n\x1a\n")
            man = {
                "asset_count": 2,
                "generation_mode": "leonardo_live",
                "warnings": ["leonardo_env_missing_fallback_placeholder"],
                "assets": [
                    {"image_path": "scene_001.png", "generation_mode": "placeholder"},
                    {"image_path": "scene_002.png", "generation_mode": "leonardo_live"},
                ],
            }
            mp = gen_dir / "asset_manifest.json"
            mp.write_text(json.dumps(man), encoding="utf-8")
            aa = build_asset_artifact(asset_manifest_path=str(mp))
        self.assertEqual(aa.get("asset_manifest_file_count"), 2)
        self.assertEqual(aa.get("placeholder_asset_count"), 1)
        self.assertEqual(aa.get("real_asset_file_count"), 1)
        self.assertEqual((aa.get("generation_modes") or {}).get("placeholder"), 1)
        self.assertEqual((aa.get("generation_modes") or {}).get("leonardo_live"), 1)
        gate = aa.get("asset_quality_gate") or {}
        self.assertEqual(gate.get("status"), "mixed_assets")
        self.assertFalse(gate.get("strict_ready"))
        self.assertTrue(gate.get("loose_ready"))

    def test_asset_quality_gate_placeholder_only(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            out_dir = Path(td).resolve()
            gen_dir = out_dir / "generated_assets_p"
            gen_dir.mkdir(parents=True, exist_ok=True)
            (gen_dir / "scene_001.png").write_bytes(b"\x89PNG\r\n\x1a\n")
            mp = gen_dir / "asset_manifest.json"
            mp.write_text(
                json.dumps(
                    {
                        "asset_count": 1,
                        "warnings": [],
                        "assets": [{"image_path": "scene_001.png", "generation_mode": "placeholder"}],
                    }
                ),
                encoding="utf-8",
            )
            aa = build_asset_artifact(asset_manifest_path=str(mp))
        gate = aa.get("asset_quality_gate") or {}
        self.assertEqual(gate.get("status"), "placeholder_only")
        self.assertFalse(gate.get("strict_ready"))
        self.assertFalse(gate.get("loose_ready"))

    def test_asset_quality_gate_production_ready(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            out_dir = Path(td).resolve()
            gen_dir = out_dir / "generated_assets_r"
            gen_dir.mkdir(parents=True, exist_ok=True)
            (gen_dir / "scene_001.png").write_bytes(b"\x89PNG\r\n\x1a\n")
            mp = gen_dir / "asset_manifest.json"
            mp.write_text(
                json.dumps(
                    {
                        "asset_count": 1,
                        "warnings": [],
                        "assets": [{"image_path": "scene_001.png", "generation_mode": "leonardo_live"}],
                    }
                ),
                encoding="utf-8",
            )
            aa = build_asset_artifact(asset_manifest_path=str(mp))
        gate = aa.get("asset_quality_gate") or {}
        self.assertEqual(gate.get("status"), "production_ready")
        self.assertTrue(gate.get("strict_ready"))
        self.assertTrue(gate.get("loose_ready"))

    @patch("app.routes.founder_dashboard.execute_dashboard_video_generate")
    def test_open_me_report_contains_fallback_status_when_warnings(self, mock_exec) -> None:
        with tempfile.TemporaryDirectory() as td:
            out_root = Path(td).resolve()
            out_dir = (out_root / "video_generate" / "video_gen_10m_fallback").resolve()
            out_dir.mkdir(parents=True, exist_ok=True)
            mock_exec.return_value = {
                "ok": True,
                "run_id": "video_gen_10m_fallback",
                "output_dir": str(out_dir),
                "final_video_path": str(out_dir / "final_video.mp4"),
                "script_path": str(out_dir / "script.json"),
                "scene_asset_pack_path": str(out_dir / "scene_asset_pack.json"),
                "asset_manifest_path": str(out_dir / "asset_manifest.json"),
                "duration_target_seconds": 600,
                "max_scenes": 24,
                "max_live_assets": 24,
                "motion_strategy": {"live_motion_available": False},
                "warnings": ["no_assets_in_asset_dir_using_placeholder", "ba323_voice_mode_fallback_dummy_no_elevenlabs_key"],
                "blocking_reasons": [],
                "next_action": "Final Video prüfen",
            }
            with patch("app.routes.founder_dashboard.default_local_preview_out_root", lambda: out_root):
                r = self.client.post("/founder/dashboard/video/generate", json={"url": "https://example.com/c"})
            self.assertEqual(r.status_code, 200, msg=r.text)
            data = r.json()
            p = Path(str(data.get("open_me_report_path") or "")).resolve()
            self.assertTrue(p.exists(), msg=f"report file missing: {p}")
            txt = p.read_text(encoding="utf-8")
            self.assertIn("fallback_preview", txt)
            self.assertIn("Platzhalter/Fallbacks", txt)
            self.assertIn("readiness_audit", data)
            self.assertIn("Readiness Audit", txt)
            self.assertIn("Voice Artifact", txt)
            self.assertIn("Smoke Result", txt)
            self.assertIn("Asset Artifact", txt)

    def test_qc_rows_asset_gate_ok_despite_render_placeholder_warnings(self) -> None:
        """BA 32.27 — Asset-Manifest-Qualität darf nicht durch cinematic/render-Warnungen überschrieben werden."""
        payload = {
            "ok": True,
            "script_path": "/tmp/script.json",
            "scene_asset_pack_path": "/tmp/pack.json",
            "asset_manifest_path": "/tmp/manifest.json",
            "final_video_path": "/tmp/final.mp4",
            "warnings": ["ba266_cinematic_placeholder_applied:1", "audio_missing_silent_render"],
            "motion_strategy": {"live_motion_available": False},
            "readiness_audit": {"asset_strict_ready": True, "render_used_placeholders": True},
            "asset_artifact": {
                "asset_quality_gate": {"status": "production_ready", "strict_ready": True},
            },
        }
        rows = {r[0]: r for r in _qc_rows(payload)}
        self.assertEqual(rows["Echte Assets verwendet"][1], "OK")
        self.assertEqual(rows["Render-Layer"][1], "Prüfen")
        self.assertIn("Placeholder/Cinematic-Fallback", rows["Render-Layer"][2])

    def test_derive_status_fallback_preview_unchanged_with_render_warnings(self) -> None:
        payload = {
            "ok": True,
            "blocking_reasons": [],
            "final_video_path": "/tmp/final_video.mp4",
            "warnings": ["ba266_cinematic_placeholder_applied:1"],
            "readiness_audit": {"asset_strict_ready": True},
            "asset_artifact": {
                "asset_quality_gate": {"status": "production_ready", "strict_ready": True},
            },
        }
        self.assertEqual(derive_video_generate_status(payload), "fallback_preview")

    def test_derive_status_production_ready_audio_silent_when_voice_none(self) -> None:
        """BA 32.31 — Silent Render mit voice_mode=none ist kein Fallback-Signal."""
        payload = {
            "ok": True,
            "blocking_reasons": [],
            "final_video_path": "/tmp/final_video.mp4",
            "warnings": ["audio_missing_silent_render"],
            "voice_artifact": {"effective_voice_mode": "none"},
            "readiness_audit": {"effective_voice_mode": "none"},
            "asset_artifact": {
                "asset_quality_gate": {"status": "production_ready", "strict_ready": True},
            },
        }
        self.assertEqual(derive_video_generate_status(payload), "production_ready")

    def test_derive_status_mixed_preview_when_long_target_duration_badly_missed(self) -> None:
        payload = {
            "ok": True,
            "blocking_reasons": [],
            "final_video_path": "/tmp/final_video.mp4",
            "warnings": ["target_duration_not_reached", "script_too_short_for_target_duration"],
            "voice_artifact": {
                "effective_voice_mode": "elevenlabs",
                "voice_ready": True,
                "is_dummy": False,
            },
            "readiness_audit": {
                "asset_strict_ready": True,
                "effective_voice_mode": "elevenlabs",
                "voice_file_ready": True,
            },
            "asset_artifact": {
                "asset_quality_gate": {"status": "production_ready", "strict_ready": True},
            },
            "duration_audit": {"target_duration_seconds": 600, "duration_ratio": 0.31},
        }
        self.assertEqual(derive_video_generate_status(payload), "mixed_preview")

    def test_derive_status_still_ready_for_short_smoke_duration_miss(self) -> None:
        payload = {
            "ok": True,
            "blocking_reasons": [],
            "final_video_path": "/tmp/final_video.mp4",
            "warnings": ["target_duration_not_reached"],
            "voice_artifact": {
                "effective_voice_mode": "elevenlabs",
                "voice_ready": True,
                "is_dummy": False,
            },
            "readiness_audit": {
                "asset_strict_ready": True,
                "effective_voice_mode": "elevenlabs",
                "voice_file_ready": True,
            },
            "asset_artifact": {
                "asset_quality_gate": {"status": "production_ready", "strict_ready": True},
            },
            "duration_audit": {"target_duration_seconds": 60, "duration_ratio": 0.6},
        }
        self.assertEqual(derive_video_generate_status(payload), "production_ready")

    def test_derive_status_fallback_audio_silent_when_voice_expected(self) -> None:
        payload = {
            "ok": True,
            "blocking_reasons": [],
            "final_video_path": "/tmp/final_video.mp4",
            "warnings": ["audio_missing_silent_render"],
            "voice_artifact": {"effective_voice_mode": "elevenlabs"},
            "asset_artifact": {
                "asset_quality_gate": {"status": "production_ready", "strict_ready": True},
            },
        }
        self.assertEqual(derive_video_generate_status(payload), "fallback_preview")

    def test_derive_status_fallback_audio_silent_when_voice_context_unknown(self) -> None:
        """Ohne Voice-Kontext bleibt audio_missing vorsichtshalber ein Fallback-Trigger."""
        payload = {
            "ok": True,
            "blocking_reasons": [],
            "final_video_path": "/tmp/final_video.mp4",
            "warnings": ["audio_missing_silent_render"],
            "asset_artifact": {
                "asset_quality_gate": {"status": "production_ready", "strict_ready": True},
            },
        }
        self.assertEqual(derive_video_generate_status(payload), "fallback_preview")

    def test_derive_status_respects_silent_render_expected_audit_field(self) -> None:
        """BA 32.32 — Audit-Feld geht vor Heuristik (z. B. minimalistische Payloads)."""
        payload = {
            "ok": True,
            "blocking_reasons": [],
            "final_video_path": "/tmp/final_video.mp4",
            "warnings": ["audio_missing_silent_render"],
            "readiness_audit": {"silent_render_expected": True},
            "asset_artifact": {
                "asset_quality_gate": {"status": "production_ready", "strict_ready": True},
            },
        }
        self.assertEqual(derive_video_generate_status(payload), "production_ready")
        payload_false = {
            **payload,
            "readiness_audit": {"silent_render_expected": False},
        }
        self.assertEqual(derive_video_generate_status(payload_false), "fallback_preview")

    def test_derive_status_fallback_when_voice_none_but_real_placeholder_warning(self) -> None:
        payload = {
            "ok": True,
            "blocking_reasons": [],
            "final_video_path": "/tmp/final_video.mp4",
            "warnings": ["audio_missing_silent_render", "ba266_cinematic_placeholder_applied:1"],
            "voice_artifact": {"effective_voice_mode": "none"},
            "asset_artifact": {
                "asset_quality_gate": {"status": "production_ready", "strict_ready": True},
            },
        }
        self.assertEqual(derive_video_generate_status(payload), "fallback_preview")

    def test_open_me_subline_asset_success_render_fallback(self) -> None:
        payload = {
            "ok": True,
            "run_id": "t1",
            "blocking_reasons": [],
            "warnings": ["ba266_cinematic_placeholder_applied:1"],
            "final_video_path": "/x/final.mp4",
            "asset_artifact": {
                "asset_quality_gate": {"status": "production_ready", "strict_ready": True},
            },
        }
        html_out = build_open_me_video_result_html(payload)
        self.assertIn("fallback_preview", html_out)
        self.assertIn("Asset-Erzeugung war erfolgreich", html_out)
        self.assertIn("Render-Layer", html_out)

    def _qc_voice_base(self) -> dict:
        return {
            "ok": True,
            "script_path": "/tmp/s.json",
            "scene_asset_pack_path": "/tmp/p.json",
            "asset_manifest_path": "/tmp/m.json",
            "final_video_path": "/tmp/f.mp4",
            "warnings": [],
            "motion_strategy": {"live_motion_available": False},
        }

    def test_qc_rows_voice_artifact_none(self) -> None:
        p = self._qc_voice_base()
        p["voice_artifact"] = {
            "effective_voice_mode": "none",
            "is_dummy": False,
            "voice_ready": False,
            "voice_file_path": None,
        }
        rows = {r[0]: r for r in _qc_rows(p)}
        self.assertEqual(rows["Echte Voice verwendet"], ("Echte Voice verwendet", "Nicht verfügbar", "Keine Voice ausgewählt."))

    def test_qc_rows_voice_artifact_dummy(self) -> None:
        p = self._qc_voice_base()
        p["voice_artifact"] = {
            "effective_voice_mode": "dummy",
            "is_dummy": True,
            "voice_ready": False,
            "voice_file_path": None,
        }
        rows = {r[0]: r for r in _qc_rows(p)}
        self.assertEqual(rows["Echte Voice verwendet"][1], "Prüfen")
        self.assertEqual(rows["Echte Voice verwendet"][2], "Dummy Voice verwendet.")

    def test_qc_rows_voice_artifact_real_ready(self) -> None:
        p = self._qc_voice_base()
        p["voice_artifact"] = {
            "effective_voice_mode": "elevenlabs",
            "is_dummy": False,
            "voice_ready": True,
            "voice_file_path": "/tmp/voice.mp3",
        }
        rows = {r[0]: r for r in _qc_rows(p)}
        self.assertEqual(rows["Echte Voice verwendet"], ("Echte Voice verwendet", "OK", "Echte Voice-Datei vorhanden."))

    def test_qc_rows_voice_artifact_path_but_not_ready(self) -> None:
        p = self._qc_voice_base()
        p["voice_artifact"] = {
            "effective_voice_mode": "elevenlabs",
            "is_dummy": False,
            "voice_ready": False,
            "voice_file_path": "/tmp/missing.mp3",
        }
        rows = {r[0]: r for r in _qc_rows(p)}
        self.assertEqual(rows["Echte Voice verwendet"], ("Echte Voice verwendet", "Prüfen", "Voice-Datei fehlt."))

    def test_qc_rows_voice_readiness_fallback_without_artifact(self) -> None:
        p = self._qc_voice_base()
        p["readiness_audit"] = {"effective_voice_mode": "none"}
        rows = {r[0]: r for r in _qc_rows(p)}
        self.assertEqual(rows["Echte Voice verwendet"][1], "Nicht verfügbar")
        self.assertIn("Keine Voice ausgewählt.", rows["Echte Voice verwendet"][2])

    def test_open_me_production_check_shows_voice_none(self) -> None:
        p = self._qc_voice_base()
        p["run_id"] = "r1"
        p["blocking_reasons"] = []
        p["voice_artifact"] = {
            "effective_voice_mode": "none",
            "is_dummy": False,
            "voice_ready": False,
            "voice_file_path": None,
        }
        html_out = build_open_me_video_result_html(p)
        self.assertIn("Keine Voice ausgewählt.", html_out)

    def test_open_me_silent_render_hint_when_voice_none_and_audio_warning(self) -> None:
        p = self._qc_voice_base()
        p["run_id"] = "r2"
        p["blocking_reasons"] = []
        p["warnings"] = ["audio_missing_silent_render"]
        p["voice_artifact"] = {
            "effective_voice_mode": "none",
            "is_dummy": False,
            "voice_ready": False,
            "voice_file_path": None,
        }
        p["readiness_audit"] = {
            "effective_voice_mode": "none",
            "silent_render_expected": True,
            "silent_render_reason": "voice_mode_none",
        }
        p["asset_artifact"] = {"asset_quality_gate": {"status": "production_ready", "strict_ready": True}}
        html_out = build_open_me_video_result_html(p)
        self.assertIn("Silent Render ist erwartet", html_out)
        self.assertIn("Smoke erfolgreich; Silent Render erwartet.", html_out)
        self.assertIn("production_ready", html_out)
        self.assertNotIn("fallback_preview", html_out)
        self.assertIn("silent_render_expected", html_out)

    def test_qc_rows_render_ok_when_voice_none_and_only_silent_audio_warning(self) -> None:
        p = self._qc_voice_base()
        p["warnings"] = ["audio_missing_silent_render"]
        p["readiness_audit"] = {"effective_voice_mode": "none", "render_used_placeholders": False}
        p["voice_artifact"] = {"effective_voice_mode": "none"}
        rows = {r[0]: r for r in _qc_rows(p)}
        self.assertEqual(rows["Render-Layer"][1], "OK")
        self.assertIn("keine Placeholder-Signale", rows["Render-Layer"][2])

    def test_derive_motion_readiness_rendered_without_live_checkbox_ba3264(self) -> None:
        d = derive_motion_readiness_fields(
            allow_live_motion=False,
            live_motion_available=True,
            max_motion_clips=1,
            motion_slot_plan={"enabled": True, "planned_count": 2, "slots": []},
            motion_clip_artifact={"rendered_count": 1, "planned_count": 2},
            generation_modes={},
        )
        self.assertTrue(d["motion_rendered"])
        self.assertTrue(d["motion_requested"])
        self.assertTrue(d["motion_ready"])

    def test_derive_motion_readiness_from_generation_modes_only_ba3264(self) -> None:
        d = derive_motion_readiness_fields(
            allow_live_motion=False,
            live_motion_available=False,
            max_motion_clips=0,
            motion_slot_plan=None,
            motion_clip_artifact={},
            generation_modes={"runway_video_live": 1},
        )
        self.assertTrue(d["motion_rendered"])
        self.assertTrue(d["motion_ready"])
        self.assertFalse(d["motion_requested"])

    def test_derive_motion_readiness_no_motion_ba3264(self) -> None:
        d = derive_motion_readiness_fields(
            allow_live_motion=False,
            live_motion_available=False,
            max_motion_clips=0,
            motion_slot_plan={"enabled": False, "planned_count": 0, "slots": []},
            motion_clip_artifact={},
            generation_modes={"gemini_image_live": 3},
        )
        self.assertFalse(d["motion_rendered"])
        self.assertFalse(d["motion_ready"])
        self.assertFalse(d["motion_requested"])

    def test_qc_rows_motion_bereit_ok_when_readiness_motion_ready_ba3264(self) -> None:
        p = self._qc_voice_base()
        p["readiness_audit"] = {"motion_ready": True, "effective_voice_mode": "elevenlabs"}
        p["voice_artifact"] = {"effective_voice_mode": "elevenlabs", "voice_ready": True, "is_dummy": False}
        rows = {r[0]: r for r in _qc_rows(p)}
        self.assertEqual(rows["Motion bereit (Audit)"][1], "OK")

    def test_motion_requested_no_clip_fallback_to_image_not_quality_blocker(self) -> None:
        payload = self._qc_voice_base()
        payload.update(
            {
                "ok": True,
                "blocking_reasons": [],
                "warnings": [
                    "runway_task_poll_timeout",
                    "runway_video_generation_failed:smoke_not_ok",
                    "motion_requested_but_no_clip_fallback_to_image",
                ],
                "final_video_path": "/tmp/final.mp4",
                "readiness_audit": {
                    "motion_requested": True,
                    "motion_ready": False,
                    "motion_rendered": False,
                    "asset_strict_ready": True,
                    "render_used_placeholders": False,
                    "effective_voice_mode": "elevenlabs",
                },
                "asset_artifact": {
                    "real_asset_file_count": 3,
                    "placeholder_asset_count": 0,
                    "asset_quality_gate": {"status": "production_ready", "strict_ready": True},
                },
                "voice_artifact": {
                    "effective_voice_mode": "elevenlabs",
                    "voice_ready": True,
                    "is_dummy": False,
                    "voice_file_path": "/tmp/voice.mp3",
                },
                "motion_strategy": {
                    "motion_requested": True,
                    "motion_rendered": False,
                    "runway_motion_rendered_count": 0,
                    "planned_motion_slot_count": 1,
                    "motion_fallback_to_image": True,
                },
            }
        )
        self.assertEqual(derive_video_generate_status(payload), "production_ready")
        rows = {r[0]: r for r in _qc_rows(payload)}
        self.assertEqual(rows["Render-Layer"][1], "OK")
        self.assertEqual(rows["Motion bereit (Audit)"][1], "OK")
        self.assertIn("Fallback auf Bild", rows["Motion bereit (Audit)"][2])

    def test_execute_video_generate_marks_optional_motion_no_clip_as_image_fallback(self) -> None:
        class _FakeMod:
            def run_ba265_url_to_final(self, **kwargs):
                out_dir = Path(str(kwargs.get("out_dir") or "")).resolve()
                gen_dir = out_dir / "generated_assets_x"
                gen_dir.mkdir(parents=True, exist_ok=True)
                (gen_dir / "scene_001.png").write_bytes(b"\x89PNG\r\n\x1a\n")
                voice = out_dir / "voice.mp3"
                voice.write_bytes(b"voice")
                (out_dir / "run_summary.json").write_text(
                    json.dumps({"voice_file_path": str(voice), "voice_duration_seconds": 10}),
                    encoding="utf-8",
                )
                mp = gen_dir / "asset_manifest.json"
                mp.write_text(
                    json.dumps(
                        {
                            "asset_count": 1,
                            "generation_mode": "openai_image_live",
                            "warnings": [],
                            "assets": [
                                {
                                    "scene_number": 1,
                                    "image_path": "scene_001.png",
                                    "generation_mode": "openai_image_live",
                                }
                            ],
                        }
                    ),
                    encoding="utf-8",
                )
                final = out_dir / "final_video.mp4"
                final.write_bytes(b"video")
                return {
                    "ok": True,
                    "output_dir": str(out_dir),
                    "final_video_path": str(final),
                    "script_path": str(out_dir / "script.json"),
                    "scene_asset_pack_path": str(out_dir / "scene_asset_pack.json"),
                    "asset_manifest_path": str(mp),
                    "warnings": ["runway_task_poll_timeout", "runway_video_generation_failed:smoke_not_ok"],
                    "blocking_reasons": [],
                    "motion_slot_plan": {"enabled": True, "planned_count": 1, "slots": [{"status": "failed"}]},
                    "motion_clip_artifact": {"planned_count": 1, "rendered_count": 0, "failed_count": 1, "video_clip_paths": []},
                }

        with tempfile.TemporaryDirectory() as td:
            with patch("app.founder_dashboard.ba323_video_generate._load_run_url_to_final_mod", lambda: _FakeMod()):
                with patch.dict(os.environ, {"ELEVENLABS_API_KEY": "test", "RUNWAY_API_KEY": "test"}, clear=False):
                    out = execute_dashboard_video_generate(
                        url="https://example.com/motion",
                        output_dir=Path(td),
                        run_id="motion_fallback",
                        duration_target_seconds=60,
                        max_scenes=1,
                        max_live_assets=1,
                        motion_clip_every_seconds=60,
                        motion_clip_duration_seconds=10,
                        max_motion_clips=1,
                        allow_live_assets=True,
                        allow_live_motion=True,
                        voice_mode="elevenlabs",
                        motion_mode="basic",
                    )
        self.assertTrue(out["ok"])
        self.assertIn("motion_requested_but_no_clip_fallback_to_image", out["warnings"])
        self.assertTrue((out["readiness_audit"] or {}).get("motion_fallback_to_image"))
        self.assertFalse((out["readiness_audit"] or {}).get("render_used_placeholders"))
        self.assertEqual(out.get("video_generate_run_status"), "production_ready")

    def test_open_me_readiness_shows_motion_requested_ba3264(self) -> None:
        p = self._qc_voice_base()
        p["run_id"] = "r_motion"
        p["readiness_audit"] = {
            "motion_ready": True,
            "motion_requested": True,
            "motion_rendered": True,
            "effective_voice_mode": "elevenlabs",
        }
        p["voice_artifact"] = {"effective_voice_mode": "elevenlabs", "voice_ready": True, "is_dummy": False}
        html_out = build_open_me_video_result_html(p)
        self.assertIn("motion_requested", html_out)
        self.assertIn("motion_rendered", html_out)


if __name__ == "__main__":
    unittest.main()
