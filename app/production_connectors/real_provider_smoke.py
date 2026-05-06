"""BA 26.4 — Kontrollierter Real-Provider-Smoke (Runway/Veo), mit dry_run und Sicherheitsflags.

Keine Secrets im Code; API-Keys nur aus os.environ. Kein Fake-Erfolg bei fehlendem Key oder Block.
"""

from __future__ import annotations

import importlib.util
import json
import os
import re
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

from app.production_connectors.scene_pack_local_video import beat_duration_seconds, pick_local_video_from_beat
from app.visual_plan.visual_no_text import append_no_text_guard
from app.visual_plan.visual_policy_report import build_visual_policy_fields

RESULT_SCHEMA = "real_provider_smoke_v1"

ALLOWED_PROVIDERS = frozenset({"runway", "veo"})
ENV_API_KEY = {"runway": "RUNWAY_API_KEY", "veo": "GOOGLE_VEO_API_KEY"}

_RUN_ID_RE = re.compile(r"^[A-Za-z0-9_-]{1,80}$")


def _validate_run_id(run_id: str) -> bool:
    s = (run_id or "").strip()
    if not s or ".." in s or "/" in s or "\\" in s:
        return False
    return bool(_RUN_ID_RE.fullmatch(s))


def _load_runway_module() -> Any:
    p = Path(__file__).resolve().parents[2] / "scripts" / "runway_image_to_video_smoke.py"
    spec = importlib.util.spec_from_file_location("runway_image_to_video_smoke_ba264", p)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {p}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _sorted_beats(scene_expansion: Dict[str, Any]) -> List[Dict[str, Any]]:
    raw = scene_expansion.get("expanded_scene_assets") or []
    if not isinstance(raw, list) or not raw:
        return []
    return sorted(raw, key=lambda b: (int(b.get("chapter_index", 0)), int(b.get("beat_index", 0))))


def load_scene_asset_pack(path: Path) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    if not path.is_file():
        raise FileNotFoundError(f"scene_asset_pack not found: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    se = data.get("scene_expansion")
    if not isinstance(se, dict):
        raise ValueError("scene_asset_pack.json missing object 'scene_expansion'")
    beats = _sorted_beats(se)
    if not beats:
        raise ValueError("scene_expansion.expanded_scene_assets empty or missing")
    return data, beats


def _runway_dry_run_summary(*, prompt: str, duration: int, api_base: Optional[str]) -> Dict[str, Any]:
    rw = _load_runway_module()
    base = (api_base or rw.DEFAULT_API_BASE).rstrip("/")
    dur = rw._clamp_duration(int(duration))
    return {
        "method": "POST",
        "url": f"{base}/v1/image_to_video",
        "body_fields": {
            "promptImage": "<data_uri_omitted_dry_run>",
            "promptText": (prompt or " ").strip() or " ",
            "model": rw.DEFAULT_MODEL,
            "ratio": rw.DEFAULT_RATIO,
            "duration": dur,
        },
        "header_names": ["Content-Type", "Authorization", "X-Runway-Version", "Accept"],
    }


def _veo_dry_run_summary() -> Dict[str, Any]:
    return {
        "method": "TBD",
        "url": "TBD_google_veo_generate",
        "body_fields": {"note": "BA 26.4 dry-run placeholder; kein Veo-HTTP-Client in diesem Repo"},
        "header_names": ["TBD"],
    }


def _scene_image_path(assets_directory: Optional[Path], scene_index: int) -> Optional[Path]:
    if not assets_directory or not assets_directory.is_dir():
        return None
    p = assets_directory / f"scene_{scene_index:03d}.png"
    if p.is_file():
        return p
    return None


def _api_key_for(provider: str) -> str:
    env = ENV_API_KEY.get(provider, "")
    return (os.environ.get(env) or "").strip()


def run_real_provider_smoke(
    pack_path: Path,
    *,
    out_root: Path,
    run_id: str,
    selected_provider: str,
    dry_run: bool,
    real_provider_enabled: bool,
    max_real_scenes: int = 1,
    force_provider: bool = False,
    assets_directory: Optional[Path] = None,
    runway_api_base: Optional[str] = None,
    runway_run_fn: Optional[Callable[..., Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """
    Verarbeitet alle Beats des Packs; pro Szene strukturiertes Ergebnis.

    Echte Aufrufe nur wenn: nicht dry_run, real_provider_enabled, Key gesetzt,
    max_real_scenes nicht überschritten, und (kein lokales Video oder force_provider).
    """
    top_warnings: List[str] = []
    top_blocking: List[str] = []
    rid = (run_id or "").strip()
    prov = (selected_provider or "").strip().lower()

    if not _validate_run_id(rid):
        top_blocking.append("invalid_run_id")
        return {
            "schema_version": RESULT_SCHEMA,
            "ok": False,
            "run_id": rid,
            "selected_provider": prov,
            "dry_run": bool(dry_run),
            "real_provider_enabled": bool(real_provider_enabled),
            "max_real_scenes": max(0, int(max_real_scenes)),
            "force_provider": bool(force_provider),
            "scenes": [],
            "warnings": top_warnings,
            "blocking_reasons": top_blocking,
        }

    if prov not in ALLOWED_PROVIDERS:
        top_blocking.append("invalid_selected_provider")
        top_warnings.append(f"selected_provider_must_be_runway_or_veo:got={prov or 'empty'}")
        return {
            "schema_version": RESULT_SCHEMA,
            "ok": False,
            "run_id": rid,
            "selected_provider": prov,
            "dry_run": bool(dry_run),
            "real_provider_enabled": bool(real_provider_enabled),
            "max_real_scenes": max(0, int(max_real_scenes)),
            "force_provider": bool(force_provider),
            "scenes": [],
            "warnings": top_warnings,
            "blocking_reasons": top_blocking,
        }

    cap = max(0, int(max_real_scenes))
    real_attempts = 0

    pack_path = pack_path.resolve()
    _pack, beats = load_scene_asset_pack(pack_path)
    scenes_out: List[Dict[str, Any]] = []

    for i, b in enumerate(beats, start=1):
        ch = int(b.get("chapter_index", 0))
        bi = int(b.get("beat_index", 0))
        routed_v = str(b.get("routed_visual_provider") or "")
        routed_img = str(b.get("routed_image_provider") or "")
        vprompt_raw = str(b.get("visual_prompt_raw") or b.get("visual_prompt") or "")
        vprompt = append_no_text_guard(str(b.get("visual_prompt_effective") or b.get("visual_prompt") or ""))
        bdur = beat_duration_seconds(b) or 5

        sw: List[str] = []
        sb: List[str] = []
        row: Dict[str, Any] = {
            "scene_index": i,
            "chapter_index": ch,
            "beat_index": bi,
            "provider": prov,
            "dry_run": bool(dry_run),
            "real_call_attempted": False,
            "real_call_succeeded": False,
            "provider_job_id": None,
            "provider_status": None,
            "local_video_path": None,
            "remote_video_url": None,
            "dry_run_request_summary": None,
            "warnings": sw,
            "blocking_reasons": sb,
        }
        row.update(
            build_visual_policy_fields(
                visual_prompt_raw=vprompt_raw,
                visual_prompt_effective=vprompt,
                overlay_intent=(b.get("overlay_intent") or []) if isinstance(b.get("overlay_intent"), list) else [],
                text_sensitive=bool(b.get("text_sensitive")),
                visual_asset_kind=str(b.get("visual_asset_kind") or "motion_clip"),
                routed_visual_provider=(routed_v or prov),
                routed_image_provider=routed_img,
            )
        )

        # BA 26.5 — Dry-run transparency: if still routing says openai_images, surface it (no call here).
        if (routed_v or "").strip().lower() == "openai_images" or (routed_img or "").strip().lower() == "openai_images":
            row["provider_used"] = "openai_images"
            row["provider_status"] = "dry_run_ready" if dry_run else "not_executed_in_real_provider_smoke"
            row["prompt_used_effective"] = vprompt

        # BA 27.4/27.6 — Reference payload stubs visibility (no live upload)
        if isinstance(b.get("reference_provider_payloads"), dict) or b.get("reference_provider_payload_status") or b.get(
            "recommended_reference_provider_payload"
        ):
            row["reference_provider_payload_status"] = str(b.get("reference_provider_payload_status") or "")
            recp = b.get("recommended_reference_provider_payload")
            if isinstance(recp, dict):
                row["recommended_reference_provider_payload"] = {
                    "provider": recp.get("provider"),
                    "supported_mode": recp.get("supported_mode"),
                    "payload_format": recp.get("payload_format"),
                    "no_live_upload": bool(recp.get("no_live_upload") is True),
                    "status": recp.get("status"),
                }

        local_vid, lvw = pick_local_video_from_beat(b, pack_path)
        sw.extend(lvw)
        if local_vid is not None:
            row["local_video_path"] = str(local_vid.resolve())

        skip_provider = local_vid is not None and not force_provider
        if skip_provider:
            sw.append("local_clip_takes_precedence_skip_provider")
            scenes_out.append(row)
            continue

        if dry_run:
            if prov == "runway":
                row["dry_run_request_summary"] = _runway_dry_run_summary(
                    prompt=vprompt, duration=bdur, api_base=runway_api_base
                )
            else:
                row["dry_run_request_summary"] = _veo_dry_run_summary()
            scenes_out.append(row)
            continue

        if not real_provider_enabled:
            sb.append("real_provider_not_enabled")
            sw.append("set_real_provider_enabled_true_for_live_calls")
            scenes_out.append(row)
            continue

        if real_attempts >= cap:
            sb.append("max_real_scenes_reached")
            scenes_out.append(row)
            continue

        key = _api_key_for(prov)
        if not key:
            sb.append(f"{prov}_api_key_missing")
            envn = ENV_API_KEY.get(prov, "API_KEY")
            sw.append(f"missing_env:{envn}")
            scenes_out.append(row)
            continue

        if prov == "veo":
            sb.append("veo_provider_not_implemented")
            sw.append("veo_live_smoke_not_available_use_dry_run")
            scenes_out.append(row)
            continue

        img = _scene_image_path(assets_directory, i)
        if img is None:
            sb.append("runway_scene_image_missing")
            sw.append(f"expected_png:{assets_directory and (assets_directory / f'scene_{i:03d}.png')}")
            scenes_out.append(row)
            continue

        real_attempts += 1
        row["real_call_attempted"] = True

        rw_mod = _load_runway_module()
        run_fn = runway_run_fn or rw_mod.run_runway_image_to_video_smoke
        sub_rid = f"{rid}_sc{i:03d}"
        smoke_out = Path(out_root).resolve() / f"real_provider_smoke_{rid}"
        try:
            res = run_fn(
                image_path=img,
                prompt=vprompt,
                run_id=sub_rid,
                out_root=smoke_out,
                duration_seconds=bdur,
                api_base=runway_api_base,
            )
        except Exception as exc:
            sb.append("runway_call_exception")
            sw.append(f"runway_exception:{type(exc).__name__}")
            scenes_out.append(row)
            continue

        sw.extend([str(w) for w in (res.get("warnings") or []) if w])
        sb.extend([str(x) for x in (res.get("blocking_reasons") or []) if x])
        meta = res.get("metadata") if isinstance(res.get("metadata"), dict) else {}
        row["provider_job_id"] = meta.get("task_id") or meta.get("taskId")
        row["provider_status"] = res.get("status")
        if res.get("ok") and (res.get("output_video_path") or "").strip():
            row["real_call_succeeded"] = True
            row["local_video_path"] = str(Path(str(res["output_video_path"]).strip()).resolve())
        else:
            row["real_call_succeeded"] = False

        scenes_out.append(row)

    ok = not top_blocking and all(len(s.get("blocking_reasons") or []) == 0 for s in scenes_out)
    return {
        "schema_version": RESULT_SCHEMA,
        "ok": ok,
        "run_id": rid,
        "selected_provider": prov,
        "dry_run": bool(dry_run),
        "real_provider_enabled": bool(real_provider_enabled),
        "max_real_scenes": cap,
        "force_provider": bool(force_provider),
        "assets_directory": str(assets_directory.resolve()) if assets_directory else None,
        "scene_asset_pack": str(pack_path),
        "scenes": scenes_out,
        "warnings": top_warnings,
        "blocking_reasons": top_blocking,
    }
