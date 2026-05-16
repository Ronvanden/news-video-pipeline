"""BA 10.6/10.7 — Founder Dashboard (HTML + optionale JSON-Config)."""

from __future__ import annotations

import os
import importlib.util
import re
import shlex
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import FileResponse, HTMLResponse
from pydantic import BaseModel, Field, field_validator, model_validator
from starlette.responses import JSONResponse
from starlette.concurrency import run_in_threadpool

from app.founder_dashboard.fresh_preview_artifact_access import (
    fresh_preview_artifact_media_type,
    resolve_fresh_preview_artifact_path,
)
from app.founder_dashboard.storyboard_render_artifact_access import (
    resolve_storyboard_render_artifact_path,
    storyboard_render_artifact_media_type,
)
from app.founder_dashboard.ba323_video_generate import (
    build_video_generate_operator_ui_ba3280,
    derive_video_generate_status,
    execute_dashboard_video_generate,
    build_provider_readiness,
    new_video_gen_run_id,
    runway_live_configured,
    scrub_video_generate_warnings_ba3280,
    video_generate_output_dir,
    write_open_me_video_result_report,
)
from app.production_connectors.production_bundle import build_production_bundle_v1
from app.founder_dashboard.html import get_founder_dashboard_html
from app.production_assembly.fresh_preview_snapshot import build_latest_fresh_preview_snapshot
from app.production_assembly.fresh_topic_preview_smoke import run_fresh_topic_preview_smoke
from app.founder_dashboard.final_render_dry_run import build_final_render_dry_run_for_local_preview
from app.founder_dashboard.local_preview_panel import (
    build_local_preview_panel_payload,
    default_local_preview_out_root,
    now_iso_utc,
    load_local_preview_human_approval,
    local_preview_file_media_type,
    local_preview_safe_resolve_run_dir,
    local_preview_safe_resolve_file,
    load_local_preview_saved_result,
    build_file_urls_for_run,
    build_status_cards_from_saved_result,
    build_approval_gate_from_run,
    validate_local_preview_run_id,
)
from app.utils import extract_video_id
from scripts.run_final_render import run_final_render_for_local_preview

router = APIRouter(tags=["founder-dashboard"])


@router.get("/founder/dashboard", response_class=HTMLResponse)
async def founder_dashboard_page() -> HTMLResponse:
    """Read-only Single-Page-UI; Story-Engine nur clientseitig per fetch."""
    return HTMLResponse(content=get_founder_dashboard_html())


def production_proof_summary_payload() -> dict:
    """Read-only Kanon: Founder Proof-of-Production / Manual-URL-Spine (keine Secrets)."""
    return {
        "summary_version": "production-proof-v1",
        "motto": "produce_one_real_asset_end_to_end",
        "canonical_spine": {
            "primary_http": {
                "method": "POST",
                "path": "/story-engine/prompt-plan",
                "required_for_full_plan": ["manual_source_url"],
                "optional": ["manual_url_rewrite_mode", "template_override", "allow_live_provider_execution"],
            },
            "pipeline_code": "app.prompt_engine.pipeline.build_production_prompt_plan",
            "includes_ba_layers_on_plan": [
                "BA 12 production assembly",
                "BA 13 publishing preparation",
                "BA 14 performance feedback",
                "BA 15 production acceleration",
                "BA 16 monetization scale",
                "BA 17.0 viral upgrade (advisory, pre-assembly)",
                "BA 18.0 scene expansion (multi-beat prompts, pre-assembly)",
                "BA 19.0/20.2 run_asset_runner.py (placeholder or Leonardo live + manifest)",
                "BA 19.1 build_timeline_manifest.py (timeline_manifest.json)",
                "BA 19.2 render_final_story_video.py (local MP4 via ffmpeg)",
                "BA 20.0 build_full_voiceover.py (narration + smoke MP3 + manifest)",
                "BA 20.1 build_full_voiceover.py (ElevenLabs / OpenAI TTS optional)",
            ],
        },
        "script_only_fast_path": {
            "note": "GenerateScriptResponse contract only — does not attach BA12–16 plan fields.",
            "endpoints": [
                {"method": "POST", "path": "/generate-script"},
                {"method": "POST", "path": "/youtube/generate-script"},
            ],
        },
        "cli_helpers": [
            {"script": "scripts/run_url_to_demo.py", "role": "Single-URL → condensed JSON (rewrite + hooks + demo hints)"},
            {"script": "scripts/build_first_demo_video.py", "role": "Local MP4 from image + audio paths"},
            {"script": "scripts/run_batch_url_demo.py", "role": "Batch URLs"},
            {"script": "scripts/run_watch_approval.py", "role": "Watch approval radar (local JSON)"},
            {"script": "scripts/build_timeline_manifest.py", "role": "BA 19.1 — asset_manifest → timeline_manifest.json"},
            {"script": "scripts/render_final_story_video.py", "role": "BA 19.2 — timeline + images + audio → MP4 (ffmpeg)"},
            {"script": "scripts/build_full_voiceover.py", "role": "BA 20.0/20.1 — narration + smoke or ElevenLabs/OpenAI TTS MP3"},
            {"script": "scripts/run_asset_runner.py", "role": "BA 19.0/20.2 — scene_asset_pack → PNGs + asset_manifest (placeholder or Leonardo live)"},
        ],
        "docs": [
            "PIPELINE_PLAN.md — Founder Production Mode / Proof of Production",
            "GOLD_PRODUCTION_STANDARD.md — Firestore production_jobs reference path",
        ],
    }


@router.get("/founder/production-proof/summary")
async def founder_production_proof_summary() -> dict:
    """Kompakte Orientierung für Proof-of-Production (statisch, kein SaaS)."""
    return production_proof_summary_payload()


@router.get("/founder/dashboard/fresh-preview/snapshot")
async def founder_fresh_preview_snapshot() -> dict:
    """BA 30.3 — read-only Scan von ``output/fresh_topic_preview`` (keine Provider, keine Secrets)."""
    return await run_in_threadpool(build_latest_fresh_preview_snapshot, default_local_preview_out_root())


@router.get("/founder/dashboard/fresh-preview/file")
async def founder_fresh_preview_artifact_file(
    artifact_path: str = Query(..., alias="path", min_length=1, max_length=6000),
) -> FileResponse:
    """
    BA 30.9 — liefert eine Textdatei (.md / .json / .txt) aus den Fresh-Preview-Artefakt-Zonen.

    Read-only; maximal 1 MB; keine Symlinks; Path-Traversal außerhalb von ``output`` blockiert.
    """
    out_root = default_local_preview_out_root()

    def _resolve() -> tuple:
        return resolve_fresh_preview_artifact_path(out_root, artifact_path)

    resolved, reason = await run_in_threadpool(_resolve)
    if reason == "ok" and resolved is not None:
        return FileResponse(
            resolved,
            media_type=fresh_preview_artifact_media_type(resolved),
            filename=resolved.name,
        )
    if reason == "not_found":
        raise HTTPException(status_code=404, detail="not found")
    if reason == "too_large":
        raise HTTPException(status_code=413, detail="payload too large")
    raise HTTPException(status_code=403, detail="forbidden")


class FreshPreviewStartDryRunRequest(BaseModel):
    """BA 30.7 — nur Dry-Run (stoppt nach asset_manifest); kein Live-Asset-Runner."""

    topic: Optional[str] = None
    url: Optional[str] = None
    duration_target_seconds: int = Field(default=45, ge=5, le=900)
    provider: Optional[str] = Field(
        default="placeholder",
        description="Dashboard V1: wird ignoriert; intern immer placeholder",
    )
    max_scenes: int = Field(default=6, ge=1, le=40)

    model_config = {"extra": "forbid"}


_ALLOWED_VOICE_MODES_BA323 = frozenset(
    {"elevenlabs_or_safe_default", "none", "elevenlabs", "dummy", "openai", "existing"}
)
_ALLOWED_MOTION_MODES_BA323 = frozenset({"basic", "static"})
_THUMBNAIL_OVERLAY_PRESETS_BA3278 = frozenset(
    {"clean_bold", "impact_youtube", "urgent_mystery", "documentary_poster"}
)


class VideoGenerateRequest(BaseModel):
    """BA 32.3 — kontrollierter URL→MP4-Lauf (kein Fresh-Preview-Dry-Run)."""

    url: Optional[str] = Field(default=None)
    raw_text: Optional[str] = Field(default=None, description="BA 32.42 — optional: Raw-Text Input statt URL.")
    title: Optional[str] = Field(default=None, description="BA 32.42 — optional: Title override für Raw-Text Smokes.")
    script_text: Optional[Dict[str, Any]] = Field(
        default=None,
        description="BA 32.58 — finales Skript (GenerateScriptResponse-ähnlich); höchste Input-Priorität.",
    )
    source_youtube_url: Optional[str] = Field(
        default=None,
        description="BA 32.58 — YouTube-URL; Transkript als Quellenmaterial für ein neues Originalskript.",
    )
    youtube_url: Optional[str] = Field(
        default=None,
        description="BA 32.58 — Alias zu source_youtube_url (gleiche URL erlaubt, unterschiedliche nicht).",
    )
    rewrite_style: Optional[str] = Field(default=None, description="BA 32.58 — optionaler Stil-Hinweis fürs Rewrite.")
    video_template: Optional[str] = Field(default=None, description="BA 32.58 — optional; Default generic in der Pipeline.")
    target_language: str = Field(default="de", min_length=2, max_length=12, description="BA 32.58 — Zielsprache fürs Skript.")
    duration_target_seconds: int = Field(default=600, ge=60, le=1800)
    max_scenes: int = Field(default=24, ge=1, le=80)
    max_live_assets: int = Field(default=24, ge=0, le=80)
    motion_clip_every_seconds: int = Field(default=60, ge=15, le=600)
    motion_clip_duration_seconds: int = Field(default=10, ge=1, le=120)
    # BA 32.51: Default 0 — Video-Generate-Pfad (static + Voice) kann Timeline an Voice anpassen;
    # Wert > 0 signalisiert Motion-Clip-Kontext (kein automatisches Fit-to-Voice).
    max_motion_clips: int = Field(default=0, ge=0, le=30)
    allow_live_assets: bool = False
    allow_live_motion: bool = False
    confirm_provider_costs: bool = False
    voice_mode: str = Field(default="elevenlabs_or_safe_default")
    motion_mode: str = Field(default="basic")
    image_provider: Optional[str] = Field(
        default=None,
        description="BA 32.72 — optional; überschreibt IMAGE_PROVIDER bei Live-Assets (leonardo|openai_image|gemini_image|placeholder).",
    )
    openai_image_model: Optional[str] = Field(default=None, max_length=128)
    openai_image_size: Optional[str] = Field(default=None, max_length=64)
    openai_image_timeout_seconds: Optional[float] = Field(default=None, ge=15.0, le=600.0)
    # BA 32.72b — dev-only, transient overrides for local dashboard smokes.
    # Niemals in Result JSON / OPEN_ME / Warnings schreiben.
    dev_openai_api_key: Optional[str] = Field(default=None, max_length=512)
    dev_elevenlabs_api_key: Optional[str] = Field(default=None, max_length=512)
    dev_runway_api_key: Optional[str] = Field(default=None, max_length=512)
    dev_leonardo_api_key: Optional[str] = Field(default=None, max_length=512)
    # BA 32.78 — optional Thumbnail Pack (OpenAI Image Candidates + lokales Batch-Overlay)
    generate_thumbnail_pack: bool = False
    enable_youtube_packaging: bool = Field(
        default=False,
        description="Optionaler YouTube Packaging V1 Script-/Voice-Layer (Intro/CTA/Outro); default aus.",
    )
    thumbnail_candidate_count: int = Field(default=3, ge=1, le=3)
    thumbnail_max_outputs: int = Field(default=6, ge=1, le=6)
    thumbnail_model: Optional[str] = Field(default=None, max_length=128)
    thumbnail_size: Optional[str] = Field(default=None, max_length=64)
    thumbnail_style_presets: Optional[List[str]] = Field(default=None, max_length=8)
    thumbnail_title_override: Optional[str] = Field(default=None, max_length=500)
    thumbnail_summary_override: Optional[str] = Field(default=None, max_length=4000)

    model_config = {"extra": "forbid"}

    @field_validator("url")
    @classmethod
    def _strip_url(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        s = (v or "").strip()
        return s or None

    @field_validator("raw_text")
    @classmethod
    def _strip_raw_text(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        s = (v or "").strip()
        return s or None

    @field_validator("title")
    @classmethod
    def _strip_title(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        s = (v or "").strip()
        return s or None

    @field_validator("thumbnail_title_override", "thumbnail_summary_override")
    @classmethod
    def _strip_thumb_text_overrides(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        s = str(v).strip()
        return s or None

    @field_validator("thumbnail_model", "thumbnail_size")
    @classmethod
    def _strip_thumb_model_size(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        s = str(v).strip()
        return s or None

    @field_validator("thumbnail_style_presets", mode="before")
    @classmethod
    def _thumb_presets_before(cls, v: Union[None, str, List[Any]]) -> Optional[List[str]]:
        if v is None:
            return None
        if isinstance(v, str):
            parts = [x.strip() for x in v.split(",") if str(x).strip()]
            return parts or None
        if isinstance(v, list):
            return [str(x).strip() for x in v if str(x).strip()] or None
        raise ValueError("thumbnail_style_presets_invalid")

    @field_validator("thumbnail_style_presets")
    @classmethod
    def _thumb_presets_allowed(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        if not v:
            return None
        out = [x for x in v if x in _THUMBNAIL_OVERLAY_PRESETS_BA3278]
        return out or None

    @field_validator("source_youtube_url", "youtube_url", "rewrite_style", "video_template")
    @classmethod
    def _strip_optional_str(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        s = (v or "").strip()
        return s or None

    @field_validator("target_language")
    @classmethod
    def _strip_target_language(cls, v: str) -> str:
        return (v or "de").strip() or "de"

    @model_validator(mode="after")
    def _video_generate_input_required(self) -> "VideoGenerateRequest":
        # Mindestens eine Eingabe: URL, Raw-Text, YouTube-Source oder script_text.
        yt = (self.source_youtube_url or "").strip() or (self.youtube_url or "").strip()
        st = self.script_text
        has_script = False
        if isinstance(st, dict):
            has_script = bool(
                (st.get("full_script") or "").strip()
                or (st.get("title") or "").strip()
                or (st.get("hook") or "").strip()
                or (isinstance(st.get("chapters"), list) and len(st.get("chapters") or []) > 0)
            )
        if not ((self.url or "").strip() or (self.raw_text or "").strip() or yt or has_script):
            raise ValueError("video_generate_input_required")
        sy = (self.source_youtube_url or "").strip()
        yu = (self.youtube_url or "").strip()
        if sy and yu and sy != yu:
            raise ValueError("youtube_url_fields_conflict")
        return self

    @field_validator("voice_mode")
    @classmethod
    def _voice_mode_ok(cls, v: str) -> str:
        s = (v or "").strip()
        if s not in _ALLOWED_VOICE_MODES_BA323:
            raise ValueError("voice_mode_invalid")
        return s

    @field_validator("motion_mode")
    @classmethod
    def _motion_mode_ok(cls, v: str) -> str:
        s = (v or "").strip().lower()
        if s not in _ALLOWED_MOTION_MODES_BA323:
            raise ValueError("motion_mode_invalid")
        return s

    @field_validator("image_provider")
    @classmethod
    def _normalize_image_provider_req(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        s = str(v).strip().lower()
        if not s:
            return None
        if s in ("openai_image", "openai-image", "openai", "gpt_image", "gpt-image"):
            return "openai_image"
        if s in ("gemini_image", "gemini-image", "gemini", "nano_banana", "nano-banana", "google_image", "google-image"):
            return "gemini_image"
        if s in ("placeholder", "none", "off", "disabled"):
            return "placeholder"
        if s in ("leonardo", "leonardo_ai", "leonardo-ai"):
            return "leonardo"
        raise ValueError("image_provider_invalid")

    @field_validator("openai_image_model", "openai_image_size")
    @classmethod
    def _strip_openai_image_optional_str(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        s = str(v).strip()
        return s or None

    @field_validator(
        "dev_openai_api_key",
        "dev_elevenlabs_api_key",
        "dev_runway_api_key",
        "dev_leonardo_api_key",
    )
    @classmethod
    def _strip_dev_key_override(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        s = str(v).strip()
        return s or None


def _dev_key_overrides_allowed(req: Request) -> bool:
    """
    BA 32.72b — Dev-only: Erlaubt Key-Overrides nur lokal oder bei explizitem Flag.
    Niemals Key-Werte loggen.
    """
    flag = (os.environ.get("VP_ALLOW_DEV_PROVIDER_KEY_OVERRIDES") or "").strip().lower()
    if flag in ("1", "true", "yes", "on"):
        return True
    try:
        ch = (req.client.host or "").strip().lower() if req.client else ""
    except Exception:
        ch = ""
    host = (req.headers.get("host") or "").strip().lower()
    if ch in ("127.0.0.1", "::1"):
        return True
    if host.startswith("localhost") or host.startswith("127.0.0.1"):
        return True
    return False


def _ps_single_quote_body(s: str) -> str:
    """PowerShell single-quoted literal: escape ' as ''."""
    return (s or "").replace("'", "''")


def _canonical_youtube_url_from_dashboard_url(url: Optional[str]) -> Optional[str]:
    vid = extract_video_id((url or "").strip())
    if not vid:
        return None
    return f"https://www.youtube.com/watch?v={vid}"


def _build_fresh_preview_handoff_cli(
    *,
    dry_run_run_id: str,
    topic: Optional[str],
    url: Optional[str],
    duration_target_seconds: int,
    max_scenes: int,
) -> Dict[str, str]:
    """BA 30.8 — kopierbare CLI für vollen Preview-Smoke (ohne --dry-run, ohne --allow-live-assets)."""
    rid_full = f"{dry_run_run_id}_full"
    out_disp = "output"
    dur = int(duration_target_seconds)
    mxs = int(max_scenes)
    if topic is not None:
        arg_ps = f"  --topic '{_ps_single_quote_body(topic)}' `"
        arg_sh = f"--topic {shlex.quote(topic)}"
    else:
        arg_ps = f"  --url '{_ps_single_quote_body(url or '')}' `"
        arg_sh = f"--url {shlex.quote(url or '')}"
    handoff_cli_command = " ".join(
        [
            "python scripts/run_fresh_topic_preview_smoke.py",
            f"--run-id {shlex.quote(rid_full)}",
            f"--output-root {shlex.quote(out_disp)}",
            arg_sh,
            f"--duration-target-seconds {dur}",
            "--provider placeholder",
            f"--max-scenes {mxs}",
        ]
    )
    lines_ps = [
        "python scripts/run_fresh_topic_preview_smoke.py `",
        f"  --run-id {rid_full} `",
        f"  --output-root {out_disp} `",
        arg_ps,
        f"  --duration-target-seconds {dur} `",
        "  --provider placeholder `",
        f"  --max-scenes {mxs}",
    ]
    handoff_cli_command_powershell = "\n".join(lines_ps)
    handoff_note = (
        "Vollständiger Preview-Smoke lokal (ohne --dry-run): MP4/Open-Me gemäß BA 30.2. "
        "Im Repository-Root ausführen."
    )
    handoff_warning = (
        "Dieser Befehl startet einen längeren Lauf inkl. Preview-Pipeline und FFmpeg — nicht aus dem Dashboard. "
        "Für echte Live-Assets muss der Operator bewusst --allow-live-assets ergänzen und API-Keys bereitstellen."
    )
    return {
        "handoff_cli_command": handoff_cli_command,
        "handoff_cli_command_powershell": handoff_cli_command_powershell,
        "handoff_note": handoff_note,
        "handoff_warning": handoff_warning,
    }


@router.post("/founder/dashboard/fresh-preview/start-dry-run")
async def founder_fresh_preview_start_dry_run(req: FreshPreviewStartDryRunRequest) -> dict:
    """
    BA 30.7 — startet ``run_fresh_topic_preview_smoke`` mit ``dry_run=True`` und ``asset_runner_mode=placeholder``.

    Genau eines von ``topic`` oder ``url`` (nicht-leer nach Strip) ist erforderlich.
    """
    topic = (req.topic or "").strip() or None
    url = (req.url or "").strip() or None
    if not topic and not url:
        raise HTTPException(
            status_code=422,
            detail="fresh_preview_start_dry_run: topic oder url erforderlich",
        )
    if topic and url:
        raise HTTPException(
            status_code=422,
            detail="fresh_preview_start_dry_run: nur eines von topic oder url, nicht beides",
        )

    run_id = f"fresh_dash_{int(time.time() * 1000)}"
    out_root = default_local_preview_out_root()

    def _run() -> Dict[str, Any]:
        return run_fresh_topic_preview_smoke(
            run_id=run_id,
            output_root=out_root,
            topic=topic,
            url=url,
            duration_target_seconds=int(req.duration_target_seconds),
            provider="placeholder",
            dry_run=True,
            max_scenes=int(req.max_scenes),
            asset_runner_mode="placeholder",
        )

    result = await run_in_threadpool(_run)
    warnings = list(result.get("warnings") or [])
    blockers = list(result.get("blocking_reasons") or [])
    ok = bool(result.get("ok"))
    rid_actual = str(result.get("run_id") or run_id)
    payload: Dict[str, Any] = {
        "ok": ok,
        "run_id": rid_actual,
        "output_dir": str(result.get("fresh_work_dir") or ""),
        "snapshot_hint": "Refresh Fresh Preview Snapshot",
        "warnings": warnings,
        "blocking_reasons": blockers,
        "fresh_preview_start_dry_run_version": "ba30_8_v1",
    }
    if ok:
        payload.update(
            _build_fresh_preview_handoff_cli(
                dry_run_run_id=rid_actual,
                topic=topic,
                url=url,
                duration_target_seconds=int(req.duration_target_seconds),
                max_scenes=int(req.max_scenes),
            )
        )
    return payload


@router.post("/founder/dashboard/video/generate")
async def founder_dashboard_video_generate(req: VideoGenerateRequest, request: Request) -> dict:
    """
    BA 32.3 — URL → ``final_video.mp4`` via ``run_ba265_url_to_final`` unter ``output/video_generate/<run_id>/``.

    Keine Runway-Clip-Erzeugung in dieser Pipeline; Live-Motion nur mit konfiguriertem Connector + Warnhinweis.
    """
    if (req.allow_live_assets or req.allow_live_motion or req.generate_thumbnail_pack) and not req.confirm_provider_costs:
        raise HTTPException(
            status_code=422,
            detail="confirm_provider_costs_required_when_live_flags",
        )
    if req.allow_live_motion and not runway_live_configured():
        raise HTTPException(
            status_code=422,
            detail="live_motion_requires_runway_connector",
        )
    run_id = new_video_gen_run_id()
    out_dir = video_generate_output_dir(default_local_preview_out_root(), run_id)

    def _run() -> Dict[str, Any]:
        out_dir.mkdir(parents=True, exist_ok=True)
        yt_explicit = (req.source_youtube_url or "").strip() or (req.youtube_url or "").strip()
        yt_from_url = _canonical_youtube_url_from_dashboard_url(req.url) if not yt_explicit else None
        yt_effective = yt_explicit or yt_from_url or None
        url_effective = None if yt_from_url else req.url
        has_dev_keys = any(
            bool((x or "").strip())
            for x in (
                req.dev_openai_api_key,
                req.dev_elevenlabs_api_key,
                req.dev_runway_api_key,
                req.dev_leonardo_api_key,
            )
        )
        if has_dev_keys and not _dev_key_overrides_allowed(request):
            # dev-only: niemals Keys akzeptieren, wenn nicht explizit erlaubt/lokal
            raise HTTPException(status_code=403, detail="dev_key_overrides_not_allowed")
        return execute_dashboard_video_generate(
            url=url_effective,
            raw_text=req.raw_text,
            title=req.title,
            script_text=req.script_text,
            source_youtube_url=yt_effective,
            rewrite_style=req.rewrite_style,
            video_template=req.video_template,
            target_language=req.target_language,
            output_dir=out_dir,
            run_id=run_id,
            duration_target_seconds=int(req.duration_target_seconds),
            max_scenes=int(req.max_scenes),
            max_live_assets=int(req.max_live_assets),
            motion_clip_every_seconds=int(req.motion_clip_every_seconds),
            motion_clip_duration_seconds=int(req.motion_clip_duration_seconds),
            max_motion_clips=int(req.max_motion_clips),
            allow_live_assets=bool(req.allow_live_assets),
            allow_live_motion=bool(req.allow_live_motion),
            voice_mode=req.voice_mode,
            motion_mode=req.motion_mode,
            image_provider=req.image_provider,
            openai_image_model=req.openai_image_model,
            openai_image_size=req.openai_image_size,
            openai_image_timeout_seconds=req.openai_image_timeout_seconds,
            enable_youtube_packaging=bool(req.enable_youtube_packaging),
            dev_openai_api_key=req.dev_openai_api_key,
            dev_elevenlabs_api_key=req.dev_elevenlabs_api_key,
            dev_runway_api_key=req.dev_runway_api_key,
            dev_leonardo_api_key=req.dev_leonardo_api_key,
            generate_thumbnail_pack=bool(req.generate_thumbnail_pack),
            thumbnail_candidate_count=int(req.thumbnail_candidate_count),
            thumbnail_max_outputs=int(req.thumbnail_max_outputs),
            thumbnail_model=req.thumbnail_model,
            thumbnail_size=req.thumbnail_size,
            thumbnail_style_presets=req.thumbnail_style_presets,
            thumbnail_title_override=req.thumbnail_title_override,
            thumbnail_summary_override=req.thumbnail_summary_override,
        )

    payload = await run_in_threadpool(_run)
    payload["video_generate_version"] = "ba32_3_v1"
    # BA 32.4 — additive Debug-Felder: Route bleibt robust, auch wenn ältere/Mock-Payloads
    # (z.B. Tests) noch kein readiness_audit liefern.
    payload.setdefault("readiness_audit", {})
    payload.setdefault("voice_artifact", {})
    payload.setdefault("image_asset_audit", {})
    report_path, warn = await run_in_threadpool(
        write_open_me_video_result_report,
        output_dir=out_dir,
        payload=payload,
    )
    if report_path is not None:
        payload["open_me_report_path"] = str(report_path)
    if warn:
        try:
            payload.setdefault("warnings", [])
            if isinstance(payload["warnings"], list):
                payload["warnings"].append(warn)
        except Exception:
            pass

    def _finalize_production_bundle() -> None:
        """BA 32.79 — Bundle inkl. OPEN_ME nach erstem OPEN_ME-Schreiben."""
        pl = payload
        om = str(report_path) if report_path is not None else ""
        pb = build_production_bundle_v1(
            output_dir=out_dir,
            run_id=str(pl.get("run_id") or "").strip() or None,
            final_video_path=str(pl.get("final_video_path") or "") or None,
            script_path=str(pl.get("script_path") or "") or None,
            scene_asset_pack_path=str(pl.get("scene_asset_pack_path") or "") or None,
            asset_manifest_path=str(pl.get("asset_manifest_path") or "") or None,
            open_me_path=om or None,
            thumbnail_pack=pl.get("thumbnail_pack") if isinstance(pl.get("thumbnail_pack"), dict) else None,
            warnings=list(pl.get("warnings") or []) if isinstance(pl.get("warnings"), list) else [],
        )
        pl["production_bundle"] = pb
        ws = pl.setdefault("warnings", [])
        if isinstance(ws, list):
            for w in pb.get("warnings") or []:
                if w and w not in ws:
                    ws.append(w)

    await run_in_threadpool(_finalize_production_bundle)
    report_path2, warn2 = await run_in_threadpool(
        write_open_me_video_result_report,
        output_dir=out_dir,
        payload=payload,
    )
    if report_path2 is not None:
        payload["open_me_report_path"] = str(report_path2)
    if warn2:
        try:
            payload.setdefault("warnings", [])
            if isinstance(payload["warnings"], list):
                payload["warnings"].append(warn2)
        except Exception:
            pass
    # BA 32.80 — veraltete Bundle-Warnungen entfernen; Status/Operator für Dashboard-JSON
    try:
        scrub_video_generate_warnings_ba3280(payload)
        _st = derive_video_generate_status(payload)
        payload["video_generate_run_status"] = _st
        payload["video_generate_operator"] = build_video_generate_operator_ui_ba3280(_st, payload)
    except Exception:
        pass
    return payload


@router.get("/founder/dashboard/local-preview/panel")
async def founder_local_preview_panel() -> dict:
    """BA 22.0 — read-only Local-Preview-Übersicht (Artefakt-Flags, Pfade, CLI-/Doku-Aktionen)."""
    return build_local_preview_panel_payload()


@router.get("/founder/dashboard/local-preview/file/{run_id}/{filename}")
async def founder_local_preview_file(run_id: str, filename: str) -> FileResponse:
    """BA 22.2 — sichere Auslieferung nur aus ``output/local_preview_<run_id>/`` (Whitelist, kein Symlink)."""
    path = local_preview_safe_resolve_file(default_local_preview_out_root(), run_id, filename)
    if path is None:
        raise HTTPException(status_code=404, detail="not found")
    return FileResponse(
        path,
        media_type=local_preview_file_media_type(filename),
    )


@router.get("/founder/dashboard/storyboard-render/file/{run_id}/{artifact_path:path}")
async def founder_storyboard_render_artifact_file(run_id: str, artifact_path: str) -> FileResponse:
    """Read-only Storyboard local render artifacts under output/storyboard_runs/<run_id>/."""

    def _resolve() -> tuple:
        return resolve_storyboard_render_artifact_path(default_local_preview_out_root(), run_id, artifact_path)

    resolved, reason = await run_in_threadpool(_resolve)
    if reason == "ok" and resolved is not None:
        return FileResponse(
            resolved,
            media_type=storyboard_render_artifact_media_type(resolved),
            filename=resolved.name,
        )
    if reason == "not_found":
        raise HTTPException(status_code=404, detail="not found")
    if reason == "too_large":
        raise HTTPException(status_code=413, detail="payload too large")
    raise HTTPException(status_code=403, detail="forbidden")


_BA223_RUN_ID_RE = re.compile(r"^[A-Za-z0-9_-]{1,80}$")


def _validate_ba223_run_id(run_id: str) -> bool:
    s = (run_id or "").strip()
    if not s or ".." in s or "/" in s or "\\" in s:
        return False
    return bool(_BA223_RUN_ID_RE.fullmatch(s))


class LocalPreviewRunMiniFixtureRequest(BaseModel):
    run_id: str = Field(default="mini_e2e", min_length=1, max_length=80)
    force_burn: bool = False
    skip_preflight: bool = False

    model_config = {"extra": "forbid"}

class LocalPreviewApprovalNoteRequest(BaseModel):
    note: str = Field(default="", max_length=400)

    model_config = {"extra": "forbid"}


_lp_pipeline_mod: Optional[Any] = None


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _load_local_preview_pipeline_mod() -> Any:
    """Lädt `scripts/run_local_preview_pipeline.py` einmalig als Modul (kein subprocess)."""
    global _lp_pipeline_mod
    if _lp_pipeline_mod is not None:
        return _lp_pipeline_mod
    root = _repo_root()
    p = root / "scripts" / "run_local_preview_pipeline.py"
    spec = importlib.util.spec_from_file_location("run_local_preview_pipeline_ba223", p)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {p}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    _lp_pipeline_mod = mod
    return mod


def _ba223_fixture_paths() -> tuple[Path, Path]:
    root = _repo_root()
    d = root / "fixtures" / "local_preview_mini"
    return d / "mini_timeline_manifest.json", d / "mini_narration.txt"


def _ba223_preflight_check() -> Dict[str, Any]:
    return dict(_load_local_preview_pipeline_mod().check_local_ffmpeg_tools())


def _ba223_run_mini_fixture(*, out_root: Path, run_id: str, force_burn: bool) -> Dict[str, Any]:
    """Startet den festen Mini-Fixture-Run (ohne freie Pfade aus Request)."""
    timeline, narration = _ba223_fixture_paths()
    pl = _load_local_preview_pipeline_mod()
    return dict(
        pl.run_local_preview_pipeline(
            timeline,
            narration,
            out_root=out_root,
            run_id=run_id,
            motion_mode="static",
            subtitle_mode="simple",
            subtitle_style="typewriter",
            subtitle_source="narration",
            audio_path=None,
            force_burn=bool(force_burn),
        )
    )


@router.post("/founder/dashboard/local-preview/run-mini-fixture")
async def founder_local_preview_run_mini_fixture(req: LocalPreviewRunMiniFixtureRequest) -> dict:
    """
    BA 22.3 — Operator-Button: startet den festen Mini-Fixture-Preview-Lauf (lokal/dev),
    ohne freie Pfade, ohne Cloud/Provider-Calls.
    """
    run_id = (req.run_id or "").strip() or "mini_e2e"
    if not _validate_ba223_run_id(run_id):
        raise HTTPException(status_code=422, detail="invalid run_id")
    out_root = default_local_preview_out_root()

    if not req.skip_preflight:
        chk = await run_in_threadpool(_ba223_preflight_check)
        if not chk.get("ok"):
            return {
                "ok": False,
                "message": "Preflight fehlgeschlagen (ffmpeg/ffprobe).",
                "run_id": run_id,
                "preflight": chk,
                "warnings": list(chk.get("warnings") or []),
                "blocking_reasons": list(chk.get("missing_tools") or []),
            }

    try:
        result = await run_in_threadpool(_ba223_run_mini_fixture, out_root=out_root, run_id=run_id, force_burn=req.force_burn)
    except Exception as e:
        msg = str(getattr(e, "message", "") or str(e) or "unknown error")
        if len(msg) > 400:
            msg = msg[:397] + "..."
        return {
            "ok": False,
            "message": "Mini-Fixture Preview-Lauf fehlgeschlagen: " + msg,
            "run_id": run_id,
            "warnings": [],
            "blocking_reasons": ["exception"],
        }

    verdict = str(result.get("verdict") or "").strip().upper() or "UNKNOWN"
    compact = {
        "result_contract": result.get("result_contract"),
        "verdict": verdict,
        "warning_classification": result.get("warning_classification"),
        "founder_quality_decision": result.get("founder_quality_decision"),
        "quality_checklist": result.get("quality_checklist"),
        "subtitle_quality_check": result.get("subtitle_quality_check"),
        "sync_guard": result.get("sync_guard"),
        "warnings": result.get("warnings") or [],
        "blocking_reasons": result.get("blocking_reasons") or [],
        "paths": result.get("paths") or {},
    }
    panel = build_local_preview_panel_payload()
    return {
        "ok": True,
        "message": "Preview-Lauf abgeschlossen.",
        "run_id": run_id,
        "result": compact,
        "panel": panel,
        "warnings": list(result.get("warnings") or []),
        "blocking_reasons": list(result.get("blocking_reasons") or []),
    }


def _build_approval_gate_for_run_dir(run_dir: Path, run_id: str) -> Dict[str, Any]:
    saved = load_local_preview_saved_result(run_dir)
    scards = build_status_cards_from_saved_result(saved)
    urls = build_file_urls_for_run(run_dir, run_id)
    appr = load_local_preview_human_approval(run_dir)
    return build_approval_gate_from_run(run_id=run_id, status_cards=scards, file_urls=urls, approval_doc=appr)


@router.post("/founder/dashboard/local-preview/approve/{run_id}")
async def founder_local_preview_approve(run_id: str, req: LocalPreviewApprovalNoteRequest) -> dict:
    """BA 22.5 — schreibt `human_approval.json` (approved), nur unter output/local_preview_<run_id>/."""
    if not validate_local_preview_run_id(run_id):
        raise HTTPException(status_code=422, detail="invalid run_id")
    out_root = default_local_preview_out_root()
    run_dir = local_preview_safe_resolve_run_dir(out_root, run_id)
    if run_dir is None:
        raise HTTPException(status_code=404, detail="run not found")

    gate = await run_in_threadpool(_build_approval_gate_for_run_dir, run_dir, run_id)
    if not gate.get("actions", {}).get("approve_enabled"):
        return JSONResponse(
            status_code=409,
            content={
                "ok": False,
                "run_id": run_id,
                "approval_gate": gate,
                "message": gate.get("reason") or "not eligible",
            },
        )

    def _write():
        doc = {
            "schema_version": "local_preview_human_approval_v1",
            "run_id": run_id,
            "status": "approved",
            "approved_at": now_iso_utc(),
            "approved_by": "local_operator",
            "note": (req.note or "").strip(),
            "source": "dashboard",
        }
        (run_dir / "human_approval.json").write_text(
            __import__("json").dumps(doc, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    await run_in_threadpool(_write)
    gate2 = await run_in_threadpool(_build_approval_gate_for_run_dir, run_dir, run_id)
    return {"ok": True, "run_id": run_id, "approval_gate": gate2, "message": "approved"}


@router.post("/founder/dashboard/local-preview/revoke-approval/{run_id}")
async def founder_local_preview_revoke_approval(run_id: str, req: LocalPreviewApprovalNoteRequest) -> dict:
    """BA 22.5 — schreibt `human_approval.json` (revoked)."""
    if not validate_local_preview_run_id(run_id):
        raise HTTPException(status_code=422, detail="invalid run_id")
    out_root = default_local_preview_out_root()
    run_dir = local_preview_safe_resolve_run_dir(out_root, run_id)
    if run_dir is None:
        raise HTTPException(status_code=404, detail="run not found")

    gate = await run_in_threadpool(_build_approval_gate_for_run_dir, run_dir, run_id)
    if not gate.get("actions", {}).get("revoke_enabled"):
        return JSONResponse(
            status_code=409,
            content={"ok": False, "run_id": run_id, "approval_gate": gate, "message": "revoke not allowed"},
        )

    def _write():
        doc = {
            "schema_version": "local_preview_human_approval_v1",
            "run_id": run_id,
            "status": "revoked",
            "approved_at": now_iso_utc(),
            "approved_by": "local_operator",
            "note": (req.note or "").strip(),
            "source": "dashboard",
        }
        (run_dir / "human_approval.json").write_text(
            __import__("json").dumps(doc, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    await run_in_threadpool(_write)
    gate2 = await run_in_threadpool(_build_approval_gate_for_run_dir, run_dir, run_id)
    return {"ok": True, "run_id": run_id, "approval_gate": gate2, "message": "revoked"}


@router.post("/founder/dashboard/local-preview/final-render/dry-run/{run_id}")
async def founder_local_preview_final_render_dry_run(run_id: str) -> dict:
    """BA 24.2 — read-only Dry-Run: prüft Gates + baut Final-Render-Contract (keine Dateien)."""
    if not validate_local_preview_run_id(run_id):
        raise HTTPException(status_code=422, detail="invalid run_id")
    out_root = default_local_preview_out_root()
    res = await run_in_threadpool(build_final_render_dry_run_for_local_preview, run_id=run_id, out_root=out_root)
    if not res.get("ok"):
        # missing run dir -> 404; alles andere -> 400
        msg = str(res.get("message") or "dry-run failed")
        if "not found" in msg:
            raise HTTPException(status_code=404, detail=msg)
        raise HTTPException(status_code=400, detail=msg)
    return res


class LocalPreviewFinalRenderRunRequest(BaseModel):
    force: bool = False

    model_config = {"extra": "forbid"}


@router.post("/founder/dashboard/local-preview/final-render/run/{run_id}")
async def founder_local_preview_final_render_run(run_id: str, req: LocalPreviewFinalRenderRunRequest) -> dict:
    """BA 24.4 — startet lokalen Final Render (V1: copy preview)."""
    if not validate_local_preview_run_id(run_id):
        raise HTTPException(status_code=422, detail="invalid run_id")
    out_root = default_local_preview_out_root()
    res = await run_in_threadpool(
        run_final_render_for_local_preview,
        run_id=run_id,
        out_root=out_root,
        force=bool(req.force),
    )
    if not isinstance(res, dict):
        return {"ok": False, "run_id": run_id, "status": "failed", "message": "unexpected result"}
    # Consistent: not-ready -> 200 ok=false for UI
    return res


@router.get("/founder/dashboard/config")
async def founder_dashboard_config() -> dict:
    """Statische Meta-Infos für Ops/Integrationstests (keine Secrets)."""
    return {
        "dashboard_version": "10.8-v1",
        "auth": False,
        "provider_readiness": build_provider_readiness(),
        "local_preview_panel_relative": {"method": "GET", "path": "/founder/dashboard/local-preview/panel"},
        "fresh_preview_snapshot_relative": {"method": "GET", "path": "/founder/dashboard/fresh-preview/snapshot"},
        "fresh_preview_start_dry_run_relative": {
            "method": "POST",
            "path": "/founder/dashboard/fresh-preview/start-dry-run",
        },
        "video_generate_relative": {"method": "POST", "path": "/founder/dashboard/video/generate"},
        "fresh_preview_file_relative": {
            "method": "GET",
            "path": "/founder/dashboard/fresh-preview/file",
        },
        "local_preview_run_mini_fixture_relative": {
            "method": "POST",
            "path": "/founder/dashboard/local-preview/run-mini-fixture",
        },
        "local_preview_approve_relative": {
            "method": "POST",
            "path": "/founder/dashboard/local-preview/approve/{run_id}",
        },
        "local_preview_revoke_approval_relative": {
            "method": "POST",
            "path": "/founder/dashboard/local-preview/revoke-approval/{run_id}",
        },
        "local_preview_final_render_dry_run_relative": {
            "method": "POST",
            "path": "/founder/dashboard/local-preview/final-render/dry-run/{run_id}",
        },
        "local_preview_final_render_run_relative": {
            "method": "POST",
            "path": "/founder/dashboard/local-preview/final-render/run/{run_id}",
        },
        "local_preview_file_relative": {
            "method": "GET",
            "path": "/founder/dashboard/local-preview/file/{run_id}/{filename}",
        },
        "storyboard_render_file_relative": {
            "method": "GET",
            "path": "/founder/dashboard/storyboard-render/file/{run_id}/{artifact_path}",
        },
        "visual_plan_relative": {
            "presets": {"method": "GET", "path": "/visual-plan/presets"},
            "prompt_preview": {"method": "POST", "path": "/visual-plan/prompt-preview"},
        },
        "production_proof_summary_relative": {"method": "GET", "path": "/founder/production-proof/summary"},
        "story_engine_relative": {
            "export_package": {"method": "POST", "path": "/story-engine/export-package"},
            "export_package_preview": {"method": "POST", "path": "/story-engine/export-package/preview"},
            "provider_readiness": {"method": "POST", "path": "/story-engine/provider-readiness"},
            "provider_prompts_optimize": {"method": "POST", "path": "/story-engine/provider-prompts/optimize"},
            "thumbnail_ctr": {"method": "POST", "path": "/story-engine/thumbnail-ctr"},
            "export_formats": {"method": "GET", "path": "/story-engine/export-formats"},
            "template_selector": {"method": "GET", "path": "/story-engine/template-selector"},
        },
    }
