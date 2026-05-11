"""BA 32.3 — Founder Dashboard: URL → ``run_ba265_url_to_final`` (ohne Shell-Subprocess)."""

from __future__ import annotations

import importlib.util
import html
import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

from app.production_connectors.production_bundle import build_production_bundle_v1
from app.production_connectors.thumbnail_candidates import run_thumbnail_candidates_v1
from app.production_connectors.thumbnail_batch_overlay import run_thumbnail_batch_overlay_v1
from app.production_connectors.thumbnail_pack_export import load_thumbnail_pack_v1

_REPO_ROOT = Path(__file__).resolve().parents[2]

_FALLBACK_SIGNALS = (
    "placeholder",
    "fallback",
    "dummy",
    "no_assets",
    "no_existing_video_asset",
    "cinematic_placeholder",
    "audio_missing_silent_render",
    "voice_mode_fallback",
    "no_elevenlabs_key",
)

# Render-/Audio-Schicht (nicht Asset-Manifest): dürfen Gesamt-fallback_preview triggern,
# sollen aber den Asset-Quality-Produktions-Check nicht überschreiben.
_RENDER_LAYER_PLACEHOLDER_SIGNALS = (
    "ba266_cinematic_placeholder_applied",
    "audio_missing_silent_render",
)

# Nur wenn Voice erwartet wurde (nicht ``none``), zählt fehlendes Audio als Render-/Fallback-Signal.
_RENDER_LAYER_AUDIO_SILENT_SIGNAL = "audio_missing_silent_render"


def _effective_voice_mode_for_fallback(payload: Dict[str, Any]) -> Optional[str]:
    """
    Effektiver Voice-Modus für Status-/Render-Signale (Priorität wie Dashboard-QC):
    voice_artifact → readiness_audit → Top-Level Keys.
    ``None`` wenn nicht ermittelbar.
    """
    va = payload.get("voice_artifact")
    if isinstance(va, dict):
        eff = str(va.get("effective_voice_mode") or "").strip().lower()
        if eff:
            return eff
    ra = payload.get("readiness_audit")
    if isinstance(ra, dict):
        eff = str(ra.get("effective_voice_mode") or "").strip().lower()
        if eff:
            return eff
    for key in ("effective_voice_mode", "requested_voice_mode"):
        raw = payload.get(key)
        if isinstance(raw, str) and raw.strip():
            return raw.strip().lower()
    return None


def _audio_silent_render_is_expected_fallback(payload: Dict[str, Any]) -> bool:
    """
    BA 32.31 / 32.32 — ``audio_missing_silent_render`` ist erwartbar bei bewusst keiner Voice.

    Bevorzugt ``readiness_audit.silent_render_expected`` (explizites Audit-Feld), sonst Heuristik
    über effektiven Voice-Modus bzw. ``requested_voice_mode == "none"`` wenn effektiv unbekannt.
    """
    ra = payload.get("readiness_audit")
    if isinstance(ra, dict) and "silent_render_expected" in ra:
        v = ra.get("silent_render_expected")
        if isinstance(v, bool):
            return v
    eff = _effective_voice_mode_for_fallback(payload)
    if eff == "none":
        return True
    if eff is not None:
        return False
    req = None
    if isinstance(ra, dict):
        r = ra.get("requested_voice_mode")
        if isinstance(r, str) and r.strip():
            req = r.strip().lower()
    if req is None:
        r2 = payload.get("requested_voice_mode")
        if isinstance(r2, str) and r2.strip():
            req = r2.strip().lower()
    return req == "none"


def _silent_render_audit_fields(
    *,
    effective_voice_mode: str,
    requested_voice_mode: str,
) -> Tuple[bool, Optional[str]]:
    """BA 32.32 — additives Audit: Silent Render explizit kennzeichnen."""
    eff_raw = (effective_voice_mode or "").strip()
    eff = eff_raw.lower() if eff_raw else ""
    req = (requested_voice_mode or "").strip().lower() or "none"
    if eff == "none" or (not eff_raw and req == "none"):
        return True, "voice_mode_none"
    return False, None


def _warn_triggers_fallback_preview(payload: Dict[str, Any], joined_lower: str) -> bool:
    """True, wenn eine der Fallback-Teilstrings in ``joined_lower`` liegt (Voice-Kontext für Silent Render)."""
    for sig in _FALLBACK_SIGNALS:
        if sig not in joined_lower:
            continue
        if sig == _RENDER_LAYER_AUDIO_SILENT_SIGNAL and _audio_silent_render_is_expected_fallback(payload):
            continue
        return True
    return False


def _bundle_open_me_resolved_ba3280(payload: Dict[str, Any]) -> bool:
    pb = payload.get("production_bundle") if isinstance(payload.get("production_bundle"), dict) else {}
    if str(pb.get("production_bundle_status") or "").strip().lower() != "ready":
        return False
    bf = pb.get("bundled_files") if isinstance(pb.get("bundled_files"), list) else []
    for item in bf:
        if not isinstance(item, dict):
            continue
        if str(item.get("label") or "") == "OPEN_ME_VIDEO_RESULT" and bool(item.get("exists")):
            return True
    return False


def scrub_video_generate_warnings_ba3280(payload: Dict[str, Any]) -> None:
    """
    BA 32.80 — Entfernt veraltete Bundle-Warnungen, sobald das finale Production-Bundle OPEN_ME enthält.
    Mutiert ``payload["warnings"]`` best-effort.
    """
    if not _bundle_open_me_resolved_ba3280(payload):
        return
    ws = payload.get("warnings")
    if not isinstance(ws, list):
        return
    payload["warnings"] = [w for w in ws if str(w) != "production_bundle_open_me_source_missing"]


def _filter_warnings_for_fallback_join_ba3280(payload: Dict[str, Any]) -> List[str]:
    """Warnungen, die für Substring-Fallback-Erkennung herangezogen werden (BA 32.80)."""
    ra = payload.get("readiness_audit") if isinstance(payload.get("readiness_audit"), dict) else {}
    va = payload.get("voice_artifact") if isinstance(payload.get("voice_artifact"), dict) else {}
    motion_requested = bool(ra.get("motion_requested"))
    allow_live = bool(ra.get("allow_live_motion_requested"))
    out: List[str] = []
    for w in payload.get("warnings") or []:
        s = str(w or "").strip()
        if not s:
            continue
        if s == "production_bundle_open_me_source_missing" and _bundle_open_me_resolved_ba3280(payload):
            continue
        if s == "elevenlabs_voice_id_default_fallback":
            if bool(va.get("voice_ready")) and not bool(va.get("is_dummy")):
                continue
        if s == "motion_requested_but_no_clip_fallback_to_image":
            if _motion_fallback_to_image_ok_ba3280(payload):
                continue
        if not motion_requested and not allow_live:
            low = s.lower()
            if "live_motion_not_available" in low or "live_motion_disabled_or_connector_missing" in low:
                continue
            if s == "runway_key_missing_motion_skipped":
                continue
        out.append(s)
    return out


def _warn_joined_lower_ba3280(payload: Dict[str, Any]) -> str:
    try:
        return " ".join(str(x or "") for x in _filter_warnings_for_fallback_join_ba3280(payload)).lower()
    except Exception:
        return ""


def _asset_strict_ready_ba3280(payload: Dict[str, Any]) -> bool:
    ra = payload.get("readiness_audit") if isinstance(payload.get("readiness_audit"), dict) else {}
    aa = payload.get("asset_artifact") if isinstance(payload.get("asset_artifact"), dict) else {}
    gate = aa.get("asset_quality_gate") if isinstance(aa.get("asset_quality_gate"), dict) else {}
    return bool(ra.get("asset_strict_ready")) or bool(gate.get("strict_ready"))


def _motion_fallback_to_image_ok_ba3280(payload: Dict[str, Any], joined_lower: Optional[str] = None) -> bool:
    """Motion is optional when the final render safely used image assets instead of a missing clip."""
    ra = payload.get("readiness_audit") if isinstance(payload.get("readiness_audit"), dict) else {}
    if bool(ra.get("motion_ready")) or not bool(ra.get("motion_requested")):
        return False
    if bool(ra.get("motion_fallback_to_image")):
        return True
    if not bool(str(payload.get("final_video_path") or "").strip()):
        return False
    joined = joined_lower if joined_lower is not None else _warn_joined_lower(payload)
    if _render_layer_placeholder_hit_from_payload(payload, joined):
        return False
    if not _asset_strict_ready_ba3280(payload):
        return False
    if _voice_dummy_productive_penalty_ba3280(payload):
        return False
    return _voice_escape_ok_ba3280(payload)


def _motion_penalty_ba3280(payload: Dict[str, Any]) -> bool:
    ra = payload.get("readiness_audit") if isinstance(payload.get("readiness_audit"), dict) else {}
    if not bool(ra.get("motion_requested")):
        return False
    if _motion_fallback_to_image_ok_ba3280(payload):
        return False
    return not bool(ra.get("motion_ready"))


def _voice_dummy_productive_penalty_ba3280(payload: Dict[str, Any]) -> bool:
    va = payload.get("voice_artifact") if isinstance(payload.get("voice_artifact"), dict) else {}
    ra = payload.get("readiness_audit") if isinstance(payload.get("readiness_audit"), dict) else {}
    if not bool(va.get("is_dummy")):
        return False
    req = str(va.get("requested_voice_mode") or ra.get("requested_voice_mode") or "").strip().lower()
    if req in ("dummy", "none", ""):
        return False
    return True


def _voice_escape_ok_ba3280(payload: Dict[str, Any]) -> bool:
    va = payload.get("voice_artifact") if isinstance(payload.get("voice_artifact"), dict) else {}
    ra = payload.get("readiness_audit") if isinstance(payload.get("readiness_audit"), dict) else {}
    eff = str(va.get("effective_voice_mode") or ra.get("effective_voice_mode") or "").strip().lower()
    if eff == "none":
        return True
    if not eff:
        if str(ra.get("requested_voice_mode") or "").strip().lower() == "none":
            return True
    if bool(va.get("is_dummy")):
        req = str(va.get("requested_voice_mode") or ra.get("requested_voice_mode") or "").strip().lower()
        return req == "dummy"
    if bool(va.get("voice_ready")):
        return True
    return bool(ra.get("voice_file_ready"))


def _thumb_bundle_ready_ba3280(payload: Dict[str, Any]) -> Tuple[bool, bool]:
    tp = payload.get("thumbnail_pack") if isinstance(payload.get("thumbnail_pack"), dict) else {}
    pb = payload.get("production_bundle") if isinstance(payload.get("production_bundle"), dict) else {}
    thumb_ok = str(tp.get("thumbnail_pack_status") or "").strip().lower() == "ready"
    bundle_ok = str(pb.get("production_bundle_status") or "").strip().lower() == "ready"
    return thumb_ok, bundle_ok


def _ba3280_manifest_counts_aligned(payload: Dict[str, Any]) -> bool:
    aa = payload.get("asset_artifact") if isinstance(payload.get("asset_artifact"), dict) else {}
    try:
        real_c = int(aa.get("real_asset_file_count") or -1)
        file_c = int(aa.get("asset_manifest_file_count") or -2)
    except (TypeError, ValueError):
        return False
    return real_c > 0 and real_c == file_c


def _ba3280_operator_green_escape(payload: Dict[str, Any]) -> Optional[str]:
    """
    BA 32.80b — Voller Operatoren-Green-Pfad trotz harmloser Warnungen (Motion optional, Modell-Hinweis, …).

    Erfordert: strict_ready, Manifest-Zähler aligned, finales Video, kein Render-Placeholder,
    Voice ok (none oder echte Datei), Motion **nicht** angefordert.
    """
    if not bool(payload.get("ok")):
        return None
    br = payload.get("blocking_reasons") or []
    if isinstance(br, list) and len(br) > 0:
        return None
    ra = payload.get("readiness_audit") if isinstance(payload.get("readiness_audit"), dict) else {}
    if bool(ra.get("motion_requested")) and not _motion_fallback_to_image_ok_ba3280(payload):
        return None
    aa = payload.get("asset_artifact") if isinstance(payload.get("asset_artifact"), dict) else {}
    gate = aa.get("asset_quality_gate") if isinstance(aa.get("asset_quality_gate"), dict) else {}
    strict = bool(ra.get("asset_strict_ready")) or bool(gate.get("strict_ready"))
    if not strict or not _ba3280_manifest_counts_aligned(payload):
        return None
    if not bool(str(payload.get("final_video_path") or "").strip()):
        return None
    joined_eval = _warn_joined_lower_ba3280(payload)
    if _render_layer_placeholder_hit_from_payload(payload, joined_eval):
        return None
    if not _voice_escape_ok_ba3280(payload):
        return None
    thumb_ok, bundle_ok = _thumb_bundle_ready_ba3280(payload)
    if thumb_ok and bundle_ok:
        return "gold_mini_ready"
    return "production_ready"


def _ba3280_should_suppress_warn_fallback_preview(payload: Dict[str, Any], joined_eval: str) -> bool:
    """
    Strikte Produktionsoberfläche (Manifest + finales Video + sauberer Render/Voice/Motion-Pflicht):
    Substring-Fallback-Warnungen gelten dann nicht als Preview-Fallback-Grund.
    """
    if not _warn_triggers_fallback_preview(payload, joined_eval):
        return False
    ra = payload.get("readiness_audit") if isinstance(payload.get("readiness_audit"), dict) else {}
    aa = payload.get("asset_artifact") if isinstance(payload.get("asset_artifact"), dict) else {}
    gate = aa.get("asset_quality_gate") if isinstance(aa.get("asset_quality_gate"), dict) else {}
    strict = bool(ra.get("asset_strict_ready")) or bool(gate.get("strict_ready"))
    has_final = bool(str(payload.get("final_video_path") or "").strip())
    render_bad = _render_layer_placeholder_hit_from_payload(payload, joined_eval)
    if not (strict and has_final and not render_bad):
        return False
    if _motion_penalty_ba3280(payload) or _voice_dummy_productive_penalty_ba3280(payload):
        return False
    return _voice_escape_ok_ba3280(payload)


def _render_layer_placeholder_hit_from_payload(payload: Dict[str, Any], joined_lower: str) -> bool:
    """Render-Layer nutzt Placeholder/Cinematic oder (nur bei erwarteter Voice) fehlendes Audio."""
    ra = payload.get("readiness_audit") if isinstance(payload.get("readiness_audit"), dict) else {}
    if "render_used_placeholders" in ra:
        flag = bool(ra.get("render_used_placeholders"))
        if flag and _RENDER_LAYER_AUDIO_SILENT_SIGNAL in joined_lower and _voice_escape_ok_ba3280(payload):
            if "ba266_cinematic_placeholder_applied" not in joined_lower:
                return False
        return flag
    if "ba266_cinematic_placeholder_applied" in joined_lower:
        return True
    if _RENDER_LAYER_AUDIO_SILENT_SIGNAL in joined_lower and not _audio_silent_render_is_expected_fallback(payload):
        # Veraltete / redundante Silent-Warnung bei nachgewiesener Voice ignorieren (BA 32.80b).
        if _voice_escape_ok_ba3280(payload):
            return False
        return True
    return False


def build_provider_readiness() -> Dict[str, Any]:
    """
    Presence-only Provider-Readiness. Keine Calls, keine Secrets, keine .env-Reads.
    Rückgabe ist stabil/additiv für Dashboard-Anzeigen.
    """
    def _present(name: str) -> bool:
        return bool((os.environ.get(name) or "").strip())

    live_assets_ok = _present("LEONARDO_API_KEY")
    eleven_ok = _present("ELEVENLABS_API_KEY")
    openai_ok = _present("OPENAI_API_KEY")
    gemini_ok = _present("GEMINI_API_KEY") or _present("GOOGLE_API_KEY")
    runway_ok = _present("RUNWAY_API_KEY")

    return {
        "live_assets": {
            "configured": bool(live_assets_ok),
            "label": "Leonardo / Asset Provider",
            "status": "ready" if live_assets_ok else "missing",
        },
        "voice_elevenlabs": {
            "configured": bool(eleven_ok),
            "label": "ElevenLabs Voice",
            "status": "ready" if eleven_ok else "missing",
        },
        "voice_openai": {
            "configured": bool(openai_ok),
            "label": "OpenAI TTS",
            "status": "ready" if openai_ok else "missing",
        },
        "motion_runway": {
            "configured": bool(runway_ok),
            "label": "Runway Motion",
            "status": "ready" if runway_ok else "optional_missing",
        },
        "image_openai": {
            "configured": bool(openai_ok),
            "label": "OpenAI Image",
            "status": "ready" if openai_ok else "missing",
            "hint": (
                "IMAGE_PROVIDER=openai_image: OPENAI_IMAGE_MODEL=gpt-image-2 für Live-Smokes bevorzugen "
                "(nach Organization Verification). Bei 403 Verification und Modellzugriff prüfen, Smoke mit gpt-image-2 "
                "wiederholen; gpt-image-1 nur zur Diagnose/Einengung. Kein automatischer Modellwechsel im Code."
            ),
        },
        "image_gemini": {
            "configured": bool(gemini_ok),
            "label": "Gemini / Nano Banana Image",
            "status": "ready" if gemini_ok else "missing",
        },
    }


def build_voice_artifact(
    *,
    output_dir: Path,
    requested_voice_mode: str,
    effective_voice_mode: str,
) -> Dict[str, Any]:
    """
    Best-effort Voice-Artefakt-Info aus run_summary.json (falls vorhanden).
    Keine Provider-Calls; robust bei fehlenden Dateien.
    """
    req = (requested_voice_mode or "").strip().lower() or "none"
    eff = (effective_voice_mode or "").strip().lower() or "none"

    warns: List[str] = []
    voice_file_path: Optional[str] = None
    duration_seconds: Optional[float] = None
    is_dummy = eff == "dummy"

    summary_path = Path(output_dir).resolve() / "run_summary.json"
    if summary_path.is_file():
        try:
            data = json.loads(summary_path.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                vfp = data.get("voice_file_path")
                if isinstance(vfp, str) and vfp.strip():
                    voice_file_path = vfp.strip()
                vdur = data.get("voice_duration_seconds")
                if isinstance(vdur, (int, float)) and float(vdur) > 0:
                    duration_seconds = float(vdur)
                vw = data.get("voice_warnings") or []
                if isinstance(vw, list) and any(str(x) == "dummy_voice_used_not_real_tts" for x in vw):
                    is_dummy = True
                if isinstance(vw, list):
                    for x in vw:
                        s = str(x or "").strip()
                        if s and s not in warns:
                            warns.append(s)
                vblk = data.get("voice_blocking_reasons") or []
                if isinstance(vblk, list):
                    for x in vblk:
                        s = str(x or "").strip()
                        if not s:
                            continue
                        code = f"voice_summary_blocking:{s}"
                        if code not in warns:
                            warns.append(code)
        except Exception as exc:
            warns.append(f"voice_summary_unreadable:{type(exc).__name__}")

    if eff == "none":
        voice_ready = False
        is_dummy = False
        voice_file_path = None
        duration_seconds = None
    else:
        if voice_file_path:
            p = Path(voice_file_path)
            if not p.is_file():
                voice_ready = False
                warns.append("voice_file_missing")
            else:
                voice_ready = True
        else:
            voice_ready = False
            if eff != "dummy":
                warns.append("voice_file_path_missing")

    return {
        "requested_voice_mode": req,
        "effective_voice_mode": eff,
        "voice_ready": bool(voice_ready),
        "voice_file_path": voice_file_path,
        "duration_seconds": duration_seconds,
        "is_dummy": bool(is_dummy),
        "warnings": warns,
    }


def build_asset_artifact(*, asset_manifest_path: Optional[str]) -> Dict[str, Any]:
    """
    Best-effort Diagnostik aus asset_manifest.json.
    Keine Provider-Calls; robust bei fehlenden Dateien/Keys.

    Zähl-Vertrag (datei- und Placeholder-Signal-orientiert, **kein** strenger Provider-Vertrag):

    - Pro Asset-Eintrag (dict): ``image_path`` oder ``video_path`` relativ zum Manifest-Verzeichnis;
      nur wenn die referenzierte Datei **existiert**, fließt der Eintrag in ``asset_manifest_file_count``
      und in genau eine der Zähler-Spalten ``real_asset_file_count`` / ``placeholder_asset_count``.
    - **Real asset:** Datei existiert und der erkannte Modus-String enthält **nicht** die Teilzeichenkette
      ``placeholder`` (Case-folding über ``.lower()``).
    - **Placeholder/Fallback:** Modus-String enthält ``placeholder`` — erkannt best-effort aus
      ``generation_mode`` → ``mode`` → ``provider_used`` → ``source_type`` (erster nicht-leerer Wert).
    - **Ohne** eines dieser Felder, aber **mit** existierender Datei: wird wie ein echtes Asset gezählt
      (leerer Modus impliziert kein Placeholder-Signal).
    - ``generation_modes``: Histogramm nur für Einträge mit nicht-leerem erkanntem Modus-String;
      leerer Modus erscheint dort nicht, kann aber trotzdem als real/placeholder über Datei + Signal zählen.
    - **asset_quality_gate** leitet Status aus diesen Zählern ab, nicht aus externen Provider-APIs.
    - ``strict_ready``: ``real_asset_file_count > 0`` und ``placeholder_asset_count == 0``
      (mindestens eine echte Datei, kein Placeholder-Eintrag laut obiger Heuristik).
    - ``loose_ready``: ``real_asset_file_count > 0`` (echte Assets erlaubt, Placeholder können dabei sein).
    """
    out: Dict[str, Any] = {
        "asset_manifest_path": asset_manifest_path,
        "asset_manifest_file_count": None,
        "real_asset_file_count": None,
        "placeholder_asset_count": None,
        "generation_modes": {},
        "asset_quality_gate": {
            "status": "unknown",
            "real_assets_present": False,
            "placeholders_present": False,
            "strict_ready": False,
            "loose_ready": False,
            "summary": "unbekannt",
        },
        "asset_provider_warning_codes": [],
        "warnings": [],
    }
    if not asset_manifest_path or not str(asset_manifest_path).strip():
        out["warnings"].append("asset_manifest_path_missing")
        return out
    mp = Path(str(asset_manifest_path)).resolve()
    if not mp.is_file():
        out["warnings"].append("asset_manifest_file_missing")
        return out
    try:
        man = json.loads(mp.read_text(encoding="utf-8"))
    except Exception as exc:
        out["warnings"].append(f"asset_manifest_unreadable:{type(exc).__name__}")
        return out
    if not isinstance(man, dict):
        out["warnings"].append("asset_manifest_not_object")
        return out
    assets = man.get("assets") or []
    if not isinstance(assets, list):
        assets = []
    gen_dir = mp.parent

    placeholder_count = 0
    real_count = 0
    file_count = 0
    modes: Dict[str, int] = {}
    for a in assets:
        if not isinstance(a, dict):
            continue
        # generation_mode is canonical in run_asset_runner; keep best-effort fallbacks.
        gmode = str(
            a.get("generation_mode")
            or a.get("mode")
            or a.get("provider_used")
            or a.get("source_type")
            or ""
        ).strip().lower()
        if gmode:
            modes[gmode] = int(modes.get(gmode, 0)) + 1
        is_placeholder = "placeholder" in gmode
        img = str(a.get("image_path") or "").strip()
        vid = str(a.get("video_path") or "").strip()
        chosen = img or vid
        if chosen:
            try:
                if (gen_dir / chosen).is_file():
                    file_count += 1
                    if is_placeholder:
                        placeholder_count += 1
                    else:
                        real_count += 1
            except Exception:
                pass
        else:
            if is_placeholder:
                placeholder_count += 1

    out["asset_manifest_file_count"] = int(file_count)
    out["real_asset_file_count"] = int(real_count)
    out["placeholder_asset_count"] = int(placeholder_count)
    out["generation_modes"] = modes

    # Asset Quality Gate (strict vs loose)
    real_present = int(real_count) > 0
    placeholders_present = int(placeholder_count) > 0
    loose_ready = real_present
    strict_ready = real_present and not placeholders_present
    if file_count == 0:
        status = "missing_assets"
        summary = "Keine Asset-Dateien im Manifest gefunden."
    elif (not real_present) and placeholders_present:
        status = "placeholder_only"
        summary = "Nur Placeholder-Assets im Manifest."
    elif real_present and placeholders_present:
        status = "mixed_assets"
        summary = "Echte Assets vorhanden, aber noch Placeholder im Manifest."
    elif strict_ready:
        status = "production_ready"
        summary = "Asset Manifest enthält echte Assets ohne Placeholder."
    else:
        status = "unknown"
        summary = "Asset-Qualität unklar."
    out["asset_quality_gate"] = {
        "status": status,
        "real_assets_present": bool(real_present),
        "placeholders_present": bool(placeholders_present),
        "strict_ready": bool(strict_ready),
        "loose_ready": bool(loose_ready),
        "summary": summary,
    }

    w = man.get("warnings") or []
    if isinstance(w, list):
        # Keep only codes (no URLs/PII expected here, but keep tight anyway)
        codes = []
        for x in w:
            s = str(x or "").strip()
            if not s:
                continue
            if (
                s.startswith("leonardo_")
                or s.startswith("openai_images_")
                or s.startswith("openai_image_")
                or s.startswith("gemini_image_")
                or s.startswith("live_image_")
            ):
                codes.append(s)
        out["asset_provider_warning_codes"] = codes
    return out


def _warn_joined_lower(payload: Dict[str, Any]) -> str:
    w = payload.get("warnings") or []
    try:
        return " ".join(str(x or "") for x in w).lower()
    except Exception:
        return ""


def derive_video_generate_status(payload: Dict[str, Any]) -> str:
    """
    BA 32.80 — normalisierter Gesamtstatus:

    ``blocked`` | ``fallback_preview`` | ``mixed_preview`` | ``gold_mini_ready`` | ``production_ready``
    """
    ok = bool(payload.get("ok"))
    blockers = payload.get("blocking_reasons") or []
    if (not ok) or (isinstance(blockers, list) and len(blockers) > 0):
        return "blocked"

    green_escape = _ba3280_operator_green_escape(payload)
    if green_escape:
        return green_escape

    joined_eval = _warn_joined_lower_ba3280(payload)
    render_bad = _render_layer_placeholder_hit_from_payload(payload, joined_eval)
    motion_penalty = _motion_penalty_ba3280(payload)
    voice_dummy_penalty = _voice_dummy_productive_penalty_ba3280(payload)
    if render_bad:
        return "fallback_preview"
    if voice_dummy_penalty:
        return "mixed_preview"
    if motion_penalty:
        return "mixed_preview"

    warn_fb = _warn_triggers_fallback_preview(payload, joined_eval)
    if warn_fb and _ba3280_should_suppress_warn_fallback_preview(payload, joined_eval):
        warn_fb = False
    if warn_fb:
        return "fallback_preview"

    aa = payload.get("asset_artifact") if isinstance(payload.get("asset_artifact"), dict) else {}
    gate = aa.get("asset_quality_gate") if isinstance(aa.get("asset_quality_gate"), dict) else {}
    ra_top = payload.get("readiness_audit") if isinstance(payload.get("readiness_audit"), dict) else {}
    strict = bool(ra_top.get("asset_strict_ready")) or bool(gate.get("strict_ready"))
    gst = str(gate.get("status") or "").strip()
    if gst == "mixed_assets" and not strict:
        return "mixed_preview"

    has_final = bool(str(payload.get("final_video_path") or "").strip())
    thumb_ok, bundle_ok = _thumb_bundle_ready_ba3280(payload)
    if (
        strict
        and has_final
        and not render_bad
        and not motion_penalty
        and not voice_dummy_penalty
        and _voice_escape_ok_ba3280(payload)
        and thumb_ok
        and bundle_ok
    ):
        return "gold_mini_ready"
    return "production_ready"


def build_video_generate_operator_ui_ba3280(status: str, payload: Dict[str, Any]) -> Dict[str, str]:
    """Kurztexte für Dashboard/JSON (de). ``status`` = Ergebnis von ``derive_video_generate_status``."""
    ra = payload.get("readiness_audit") if isinstance(payload.get("readiness_audit"), dict) else {}
    motion_req = bool(ra.get("motion_requested"))
    motion_ok = bool(ra.get("motion_ready"))
    if status == "blocked":
        return {
            "headline": "Video-Generierung fehlgeschlagen",
            "subline": "Blocker prüfen, Parameter anpassen und erneut starten.",
            "smoke_line": "Smoke fehlgeschlagen oder blockiert.",
            "badge": "Failed",
            "badge_class": "bad",
        }
    if status == "fallback_preview":
        return {
            "headline": "Fallback-Preview erstellt",
            "subline": "Der Lauf ist technisch abgeschlossen, nutzt aber noch Platzhalter- oder Fallback-Signale.",
            "smoke_line": "Smoke lief, aber Fallbacks wurden genutzt",
            "badge": "Fallback / Preview",
            "badge_class": "warn",
        }
    if status == "mixed_preview":
        sub_m = (
            "Motion wurde angefordert, ist aber nicht bereit (kein Runway-Render / kein Live-Motion-Match)."
            if motion_req and not motion_ok
            else "Es gibt noch Qualitätseinschränkungen (z. B. Voice-Fallback oder teilweise Assets)."
        )
        return {
            "headline": "Lauf mit Qualitätseinschränkungen",
            "subline": sub_m,
            "smoke_line": "Smoke abgeschlossen mit Einschränkungen — Details in Warnungen prüfen.",
            "badge": "Teilweise",
            "badge_class": "warn",
        }
    if status == "gold_mini_ready":
        sub_g = (
            "Echte Assets, Voice/Render und Thumbnail-Bundle wurden erzeugt. "
            "Motion-Clips waren nicht angefordert oder optional nicht verfügbar."
            if not motion_req
            else "Echte Assets, Voice/Render, Thumbnail-Bundle und Motion-Pflicht wurden erfüllt."
        )
        return {
            "headline": "Gold-Mini-Run erstellt",
            "subline": sub_g,
            "smoke_line": "Smoke erfolgreich; Produktionspaket (strict_ready) inkl. Bundle.",
            "badge": "Gold Mini",
            "badge_class": "ok",
        }
    # production_ready
    sub_ready = (
        "Motion wurde übersprungen; der finale Render nutzt saubere Bild-Assets als Fallback."
        if motion_req and not motion_ok and _motion_fallback_to_image_ok_ba3280(payload)
        else "Finales Ergebnis prüfen und Preview öffnen."
    )
    return {
        "headline": "Video-Generierung abgeschlossen",
        "subline": sub_ready,
        "smoke_line": "Real Production Smoke erfolgreich prüfen",
        "badge": "Ready",
        "badge_class": "ok",
    }


def _qc_rows(payload: Dict[str, Any]) -> List[Tuple[str, str, str]]:
    joined = _warn_joined_lower_ba3280(payload)
    warnings = payload.get("warnings") or []
    _ = warnings  # for readability: payload may omit warnings
    has_script = bool(str(payload.get("script_path") or "").strip())
    has_pack = bool(str(payload.get("scene_asset_pack_path") or "").strip())
    has_manifest = bool(str(payload.get("asset_manifest_path") or "").strip())
    has_final_video = bool(str(payload.get("final_video_path") or "").strip())
    has_voice_fallback = any(sig in joined for sig in ("dummy", "voice_mode_fallback", "no_elevenlabs_key"))
    ms = payload.get("motion_strategy") or {}
    live_motion_av = ms.get("live_motion_available", None)
    ra = payload.get("readiness_audit") if isinstance(payload.get("readiness_audit"), dict) else {}
    aa = payload.get("asset_artifact") if isinstance(payload.get("asset_artifact"), dict) else {}
    gate = aa.get("asset_quality_gate") if isinstance(aa.get("asset_quality_gate"), dict) else {}
    asset_strict = bool(ra.get("asset_strict_ready"))
    if not asset_strict:
        asset_strict = bool(gate.get("strict_ready"))
    g_status = str(gate.get("status") or "").strip() if gate else ""

    def _render_layer_hit() -> bool:
        return _render_layer_placeholder_hit_from_payload(payload, joined)

    def _asset_generation_qc() -> Tuple[str, str, str]:
        if asset_strict:
            return (
                "Echte Assets verwendet",
                "OK",
                "Asset Quality Gate strict_ready (Manifest) — unabhängig von Render-Warnungen",
            )
        if not aa or not g_status:
            return ("Echte Assets verwendet", "Prüfen", "kein vollständiges asset_artifact / Gate")
        if g_status in ("mixed_assets", "placeholder_only", "missing_assets", "unknown"):
            return ("Echte Assets verwendet", "Prüfen", f"Asset-Gate: {g_status}")
        if g_status == "production_ready":
            return ("Echte Assets verwendet", "OK", "asset_quality_gate production_ready")
        return ("Echte Assets verwendet", "Prüfen", "Asset-Gate unklar")

    def _render_layer_qc() -> Tuple[str, str, str]:
        if not has_final_video:
            return ("Render-Layer", "Nicht verfügbar", "final_video_path fehlt — keine Renderdaten")
        if _render_layer_hit():
            return ("Render-Layer", "Prüfen", "Render-Layer nutzt noch Placeholder/Cinematic-Fallback.")
        return ("Render-Layer", "OK", "Render-Layer nutzt keine Placeholder-Signale.")

    def _voice_warning_fallback() -> Tuple[str, str, str]:
        return (
            "Echte Voice verwendet",
            "Prüfen" if has_voice_fallback else "OK",
            "Dummy/Fallback-Signal in warnings" if has_voice_fallback else "keine Voice-Fallback-Signale erkannt",
        )

    def _voice_qc() -> Tuple[str, str, str]:
        """Gleiche Priorität wie Dashboard: voice_artifact → readiness_audit → Warning-Signale."""
        va = payload.get("voice_artifact") if isinstance(payload.get("voice_artifact"), dict) else None
        if va:
            eff = str(va.get("effective_voice_mode") or "").strip().lower() or "none"
            if eff == "none":
                return ("Echte Voice verwendet", "Nicht verfügbar", "Keine Voice ausgewählt.")
            if bool(va.get("is_dummy")):
                return ("Echte Voice verwendet", "Prüfen", "Dummy Voice verwendet.")
            if bool(va.get("voice_ready")) and not bool(va.get("is_dummy")):
                return ("Echte Voice verwendet", "OK", "Echte Voice-Datei vorhanden.")
            if str(va.get("voice_file_path") or "").strip():
                return ("Echte Voice verwendet", "Prüfen", "Voice-Datei fehlt.")
            return _voice_warning_fallback()
        eff_r = str(ra.get("effective_voice_mode") or "").strip().lower()
        if eff_r == "none":
            return ("Echte Voice verwendet", "Nicht verfügbar", "Keine Voice ausgewählt.")
        if bool(ra.get("voice_is_dummy")):
            return ("Echte Voice verwendet", "Prüfen", "Dummy Voice verwendet.")
        if bool(ra.get("voice_file_ready")) and not bool(ra.get("voice_is_dummy")):
            return ("Echte Voice verwendet", "OK", "Echte Voice-Datei vorhanden.")
        if bool(ra.get("voice_file_path_present")):
            return ("Echte Voice verwendet", "Prüfen", "Voice-Datei fehlt.")
        return _voice_warning_fallback()

    def _ok_or_na(flag: bool, present_label: str, missing_label: str) -> Tuple[str, str]:
        return ("OK", present_label) if flag else ("Nicht verfügbar", missing_label)

    rows: List[Tuple[str, str, str]] = []
    st, det = _ok_or_na(has_script, "script_path vorhanden", "script_path fehlt")
    rows.append(("Script erstellt", st, det))
    st, det = _ok_or_na(has_pack, "scene_asset_pack_path vorhanden", "scene_asset_pack_path fehlt")
    rows.append(("Scene Asset Pack erstellt", st, det))
    st, det = _ok_or_na(has_manifest, "asset_manifest_path vorhanden", "asset_manifest_path fehlt")
    rows.append(("Asset Manifest vorhanden", st, det))
    st, det = _ok_or_na(has_final_video, "final_video_path vorhanden", "final_video_path fehlt")
    rows.append(("Final Video Pfad vorhanden", st, det))
    rows.append(_asset_generation_qc())
    rows.append(_render_layer_qc())
    rows.append(_voice_qc())
    if isinstance(live_motion_av, bool):
        rows.append(
            (
                "Live Motion verfügbar",
                "OK" if live_motion_av else "Prüfen",
                "live_motion_available=true" if live_motion_av else "live_motion_available=false",
            )
        )
    else:
        rows.append(("Live Motion verfügbar", "Nicht verfügbar", "motion_strategy.live_motion_available fehlt"))
    if bool(ra.get("motion_ready")):
        rows.append(
            (
                "Motion bereit (Audit)",
                "OK",
                "motion_ready: Runway-Clip gerendert oder Live-Motion-Connector angefragt und verfügbar.",
            )
        )
    elif bool(ra.get("motion_requested")) and _motion_fallback_to_image_ok_ba3280(payload, joined):
        rows.append(
            (
                "Motion bereit (Audit)",
                "OK",
                "Motion übersprungen / Fallback auf Bild: kein Clip-Pfad, finaler Render nutzt Image-only.",
            )
        )
    elif bool(ra.get("motion_requested")):
        rows.append(
            (
                "Motion bereit (Audit)",
                "Prüfen",
                "Motion-Slots geplant/angefordert, aber kein Runway-Render und kein Live-Motion-Match.",
            )
        )
    return rows


def _build_open_me_thumbnail_pack_section(payload: Dict[str, Any], esc: Callable[[Any], str]) -> str:
    """BA 32.77 — HTML fragment for OPEN_ME (no secrets)."""
    tp = payload.get("thumbnail_pack") if isinstance(payload.get("thumbnail_pack"), dict) else {}
    status = str(tp.get("thumbnail_pack_status") or "missing_report")
    pack_path = str(tp.get("thumbnail_pack_path") or "")
    res_path = str(tp.get("thumbnail_pack_result_path") or "")
    rec_path = str(tp.get("thumbnail_recommended_path") or "")
    rec_score = tp.get("thumbnail_recommended_score")
    rec_style = str(tp.get("thumbnail_recommended_style_preset") or "")
    rec_lines = tp.get("thumbnail_recommended_text_lines")
    if not isinstance(rec_lines, list):
        rec_lines = []
    rec_lines_s = " / ".join(str(x) for x in rec_lines if str(x or "").strip())
    nvar = tp.get("thumbnail_generated_count")
    try:
        nvar_i = int(nvar) if nvar is not None else 0
    except (TypeError, ValueError):
        nvar_i = 0
    top_sc = tp.get("thumbnail_top_score")

    rows = [
        "<table>",
        f"<tr><td class='k'>Status</td><td class='v'><code>{esc(status)}</code></td><td class='b'></td></tr>",
        f"<tr><td class='k'>Pack-Ordner</td><td class='v'><code>{esc(pack_path) if pack_path else '—'}</code></td><td class='b'></td></tr>",
        f"<tr><td class='k'>Batch-Report (JSON)</td><td class='v'><code>{esc(res_path) if res_path else '—'}</code></td><td class='b'></td></tr>",
        f"<tr><td class='k'>Varianten</td><td class='v'><code>{esc(nvar_i)}</code></td><td class='b'></td></tr>",
        f"<tr><td class='k'>Top-Score</td><td class='v'><code>{esc(top_sc) if top_sc is not None else '—'}</code></td><td class='b'></td></tr>",
        "</table>",
        "<p class=\"muted\" style=\"margin:8px 0 0;font-size:11px\">"
        "Empfehlung ist heuristisch (BA 32.76), kein CTR-Modell und keine automatische finale Auswahl."
        "</p>",
    ]

    if rec_path or rec_score is not None or rec_style or rec_lines_s:
        rows.append("<h3 style=\"font-size:13px;margin:14px 0 6px\">Empfohlene Variante</h3><table>")
        rows.append(
            f"<tr><td class='k'>Score</td><td class='v'><code>{esc(rec_score) if rec_score is not None else '—'}</code></td><td class='b'></td></tr>"
        )
        rows.append(
            f"<tr><td class='k'>Style-Preset</td><td class='v'><code>{esc(rec_style) if rec_style else '—'}</code></td><td class='b'></td></tr>"
        )
        rows.append(
            f"<tr><td class='k'>Textzeilen</td><td class='v'><code>{esc(rec_lines_s) if rec_lines_s else '—'}</code></td><td class='b'></td></tr>"
        )
        rows.append(
            f"<tr><td class='k'>Pfad</td><td class='v'><code>{esc(rec_path) if rec_path else '—'}</code></td><td class='b'></td></tr>"
        )
        rows.append("</table>")
        if rec_path:
            try:
                rp = Path(rec_path)
                if rp.is_file():
                    uri = rp.as_uri()
                    rows.append(
                        "<p style=\"margin:10px 0 0\">"
                        f"<img src=\"{esc(uri)}\" alt=\"Empfohlenes Thumbnail\" "
                        "style=\"max-width:100%;max-height:240px;border-radius:8px;border:1px solid var(--border)\" />"
                        "</p>"
                    )
            except Exception:
                pass

    variants = tp.get("thumbnail_variants")
    if isinstance(variants, list) and variants:
        rows.append("<h3 style=\"font-size:13px;margin:14px 0 6px\">Alle Varianten</h3>")
        rows.append("<table>")
        rows.append(
            "<tr><td class='k'><strong>output_id</strong></td>"
            "<td class='k'><strong>score</strong></td>"
            "<td class='k'><strong>style_preset</strong></td>"
            "<td class='k'><strong>text_lines</strong></td>"
            "<td class='k'><strong>output_path</strong></td></tr>"
        )
        for v in variants:
            if not isinstance(v, dict):
                continue
            oid = str(v.get("output_id") or "")
            sc = v.get("score")
            st = str(v.get("style_preset") or "")
            tls = v.get("text_lines")
            if not isinstance(tls, list):
                tls = []
            tl_join = " / ".join(str(x) for x in tls if str(x or "").strip())
            op = str(v.get("output_path") or "")
            rows.append(
                f"<tr><td class='v'><code>{esc(oid)}</code></td>"
                f"<td class='v'><code>{esc(sc)}</code></td>"
                f"<td class='v'><code>{esc(st)}</code></td>"
                f"<td class='v'><code>{esc(tl_join) if tl_join else '—'}</code></td>"
                f"<td class='v'><code>{esc(op) if op else '—'}</code></td></tr>"
            )
        rows.append("</table>")

    return "\n".join(rows)


def _build_open_me_production_bundle_section(payload: Dict[str, Any], esc: Callable[[Any], str]) -> str:
    """BA 32.79 — Production Bundle fragment for OPEN_ME."""
    pb = payload.get("production_bundle") if isinstance(payload.get("production_bundle"), dict) else {}
    st = str(pb.get("production_bundle_status") or "missing")
    bpath = str(pb.get("production_bundle_path") or "")
    mpath = str(pb.get("production_bundle_manifest_path") or "")
    fv_b = str(pb.get("final_video_bundle_path") or "")
    rt_b = str(pb.get("recommended_thumbnail_bundle_path") or "")
    rows = [
        "<table>",
        f"<tr><td class='k'>Status</td><td class='v'><code>{esc(st)}</code></td><td class='b'></td></tr>",
        f"<tr><td class='k'>Bundle-Ordner</td><td class='v'><code>{esc(bpath) if bpath else '—'}</code></td><td class='b'></td></tr>",
        f"<tr><td class='k'>Manifest (JSON)</td><td class='v'><code>{esc(mpath) if mpath else '—'}</code></td><td class='b'></td></tr>",
        f"<tr><td class='k'>Final Video (Bundle)</td><td class='v'><code>{esc(fv_b) if fv_b else '—'}</code></td><td class='b'></td></tr>",
        f"<tr><td class='k'>Recommended Thumbnail (Bundle)</td><td class='v'><code>{esc(rt_b) if rt_b else '—'}</code></td><td class='b'></td></tr>",
        "</table>",
    ]
    bf = pb.get("bundled_files")
    if isinstance(bf, list) and bf:
        rows.append("<h3 style=\"font-size:13px;margin:14px 0 6px\">Gebündelte Dateien</h3><table>")
        rows.append(
            "<tr><td class='k'><strong>label</strong></td>"
            "<td class='k'><strong>exists</strong></td>"
            "<td class='k'><strong>bytes</strong></td>"
            "<td class='k'><strong>bundle_path</strong></td></tr>"
        )
        for item in bf:
            if not isinstance(item, dict):
                continue
            rows.append(
                f"<tr><td class='v'><code>{esc(item.get('label'))}</code></td>"
                f"<td class='v'><code>{esc(item.get('exists'))}</code></td>"
                f"<td class='v'><code>{esc(item.get('bytes_written'))}</code></td>"
                f"<td class='v'><code>{esc(item.get('bundle_path'))}</code></td></tr>"
            )
        rows.append("</table>")
    return "\n".join(rows)


def build_open_me_video_result_html(payload: Dict[str, Any]) -> str:
    status = derive_video_generate_status(payload)
    run_id = str(payload.get("run_id") or "")
    ok = bool(payload.get("ok"))
    blockers = payload.get("blocking_reasons") or []
    warnings = payload.get("warnings") or []

    jn_all = _warn_joined_lower(payload)
    silent_render_note = (
        _audio_silent_render_is_expected_fallback(payload)
        and _RENDER_LAYER_AUDIO_SILENT_SIGNAL in jn_all
    )

    if status == "blocked":
        expl = "Der Lauf konnte nicht vollständig erzeugt werden."
    elif status == "fallback_preview":
        aa_fb = payload.get("asset_artifact") if isinstance(payload.get("asset_artifact"), dict) else {}
        gate_fb = aa_fb.get("asset_quality_gate") if isinstance(aa_fb.get("asset_quality_gate"), dict) else {}
        if bool(gate_fb.get("strict_ready")) or str(gate_fb.get("status") or "") == "production_ready":
            expl = (
                "Asset-Erzeugung war erfolgreich; Fallback stammt aus Render/Audio/Motion-Schicht."
            )
        else:
            expl = "Der Lauf ist technisch abgeschlossen, nutzt aber Platzhalter/Fallbacks."
        jn_fb = jn_all
        va_fb = payload.get("voice_artifact") if isinstance(payload.get("voice_artifact"), dict) else {}
        ra_fb = payload.get("readiness_audit") if isinstance(payload.get("readiness_audit"), dict) else {}
        eff_fb = str(va_fb.get("effective_voice_mode") or ra_fb.get("effective_voice_mode") or "").strip().lower()
        if (
            eff_fb == "none"
            and "audio_missing_silent_render" in jn_fb
            and (
                bool(gate_fb.get("strict_ready"))
                or str(gate_fb.get("status") or "") == "production_ready"
            )
        ):
            expl = expl + " Keine Voice ausgewählt; Silent Render ist erwartet."
    elif status == "gold_mini_ready":
        expl = (
            "Striktes Produktionspaket: echte Assets, Render, Voice (oder bewusst keine), "
            "Thumbnail-Pack und Production-Bundle sind bereit."
        )
    elif status == "mixed_preview":
        expl = (
            "Der Lauf ist abgeschlossen, weist aber noch Qualitätseinschränkungen auf "
            "(z. B. Motion, Voice oder gemischte Assets)."
        )
    else:
        expl = "Der Lauf ist abgeschlossen und sollte geprüft werden."
        if silent_render_note:
            expl = expl + " Keine Voice ausgewählt; Silent Render ist erwartet."

    def esc(x: Any) -> str:
        return html.escape(str(x if x is not None else ""))

    def li(items: Any) -> str:
        if not isinstance(items, list) or not items:
            return "<li><em>—</em></li>"
        return "\n".join(f"<li>{esc(x)}</li>" for x in items)

    artifacts = [
        ("Final Video", payload.get("final_video_path") or ""),
        ("Output-Ordner", payload.get("output_dir") or ""),
        ("Script", payload.get("script_path") or ""),
        ("Scene Asset Pack", payload.get("scene_asset_pack_path") or ""),
        ("Asset Manifest", payload.get("asset_manifest_path") or ""),
    ]
    art_rows = "\n".join(
        f"<tr><td class='k'>{esc(k)}</td><td class='v'><code>{esc(v) if str(v).strip() else '—'}</code></td></tr>"
        for k, v in artifacts
    )

    qc_rows = "\n".join(
        f"<tr><td class='k'>{esc(lbl)}</td><td class='v'>{esc(detail)}</td><td class='b'>{esc(st)}</td></tr>"
        for (lbl, st, detail) in _qc_rows(payload)
    )

    va = payload.get("voice_artifact") or {}
    va_rows = ""
    if isinstance(va, dict) and va:
        def _va_row(k: str, v: Any) -> str:
            return f"<tr><td class='k'>{esc(k)}</td><td class='v'><code>{esc(v)}</code></td><td class='b'></td></tr>"
        keys_va = [
            "requested_voice_mode",
            "effective_voice_mode",
            "voice_ready",
            "is_dummy",
            "voice_file_path",
            "duration_seconds",
            "warnings",
        ]
        va_rows = "\n".join(_va_row(k, va.get(k)) for k in keys_va if k in va)

    aa = payload.get("asset_artifact") or {}
    aa_rows = ""
    if isinstance(aa, dict) and aa:
        def _aa_row(k: str, v: Any) -> str:
            return f"<tr><td class='k'>{esc(k)}</td><td class='v'><code>{esc(v)}</code></td><td class='b'></td></tr>"
        keys_aa = [
            "asset_manifest_file_count",
            "real_asset_file_count",
            "placeholder_asset_count",
            "generation_modes",
            "asset_quality_gate",
            "asset_provider_warning_codes",
            "warnings",
        ]
        aa_rows = "\n".join(_aa_row(k, aa.get(k)) for k in keys_aa if k in aa)

    ia = payload.get("image_asset_audit") or {}
    ia_rows = ""
    if isinstance(ia, dict) and ia:

        def _ia_row(k: str, v: Any) -> str:
            disp = json.dumps(v, ensure_ascii=False) if isinstance(v, (dict, list)) else v
            return f"<tr><td class='k'>{esc(k)}</td><td class='v'><code>{esc(disp)}</code></td><td class='b'></td></tr>"

        keys_ia = [
            "requested_image_provider",
            "effective_image_provider",
            "requested_openai_image_model",
            "requested_openai_image_size",
            "requested_openai_image_timeout_seconds",
            "openai_image_runner_options",
            "real_asset_file_count",
            "asset_manifest_file_count",
            "asset_manifest_path",
        ]
        ia_rows = "\n".join(_ia_row(k, ia.get(k)) for k in keys_ia)

    ra = payload.get("readiness_audit") or {}
    ra_rows = ""
    if isinstance(ra, dict) and ra:
        def _ra_row(k: str, v: Any) -> str:
            return f"<tr><td class='k'>{esc(k)}</td><td class='v'><code>{esc(v)}</code></td><td class='b'></td></tr>"
        keys = [
            "requested_live_assets",
            "requested_voice_mode",
            "script_ready",
            "scene_asset_pack_ready",
            "asset_manifest_ready",
            "real_assets_ready",
            "asset_quality_status",
            "asset_strict_ready",
            "asset_loose_ready",
            "voice_ready",
            "voice_provider_ready",
            "voice_provider_blocker",
            "voice_file_path_present",
            "voice_file_ready",
            "voice_is_dummy",
            "motion_ready",
            "motion_requested",
            "motion_rendered",
            "render_used_placeholders",
            "provider_blockers",
            "effective_voice_mode",
            "asset_runner_mode",
            "live_motion_available",
            "allow_live_motion_requested",
            "silent_render_expected",
            "silent_render_reason",
        ]
        ra_rows = "\n".join(_ra_row(k, ra.get(k)) for k in keys if k in ra)

    ta = payload.get("timing_audit") or {}
    ta_rows = ""
    if isinstance(ta, dict) and ta:
        def _ta_fmt_gap_seconds(v: Any) -> Any:
            try:
                f = float(v)
            except (TypeError, ValueError):
                return v
            return f"{f:.2f}s"

        _ta_seconds_display_keys = {
            "voice_duration_seconds",
            "timeline_duration_seconds",
            "final_video_duration_seconds",
            "requested_duration_seconds",
            "timeline_minus_voice_seconds",
            "final_video_minus_voice_seconds",
            "voice_minus_timeline_seconds",
            "timing_gap_abs_seconds",
        }

        def _ta_row(k: str, v: Any) -> str:
            if k in _ta_seconds_display_keys:
                v = _ta_fmt_gap_seconds(v)
            return f"<tr><td class='k'>{esc(k)}</td><td class='v'><code>{esc(v)}</code></td><td class='b'></td></tr>"
        keys_ta = [
            "voice_duration_seconds",
            "timeline_duration_seconds",
            "final_video_duration_seconds",
            "requested_duration_seconds",
            "timeline_minus_voice_seconds",
            "final_video_minus_voice_seconds",
            "voice_minus_timeline_seconds",
            "timing_gap_abs_seconds",
            "timing_gap_status",
            "audio_shorter_than_timeline",
            "audio_longer_than_timeline",
            "padding_or_continue_applied",
            "fit_strategy",
            "summary",
        ]
        ta_rows = "\n".join(_ta_row(k, ta.get(k)) for k in keys_ta if k in ta)

    msp = payload.get("motion_slot_plan")
    ms_rows = ""
    if isinstance(msp, dict) and msp:
        nslots = len(msp.get("slots") or []) if isinstance(msp.get("slots"), list) else 0
        ms_rows = "\n".join(
            [
                f"<tr><td class='k'>enabled</td><td class='v'><code>{esc(msp.get('enabled'))}</code></td><td class='b'></td></tr>",
                f"<tr><td class='k'>planned_count</td><td class='v'><code>{esc(msp.get('planned_count'))}</code></td><td class='b'></td></tr>",
                f"<tr><td class='k'>motion_clip_every_seconds</td><td class='v'><code>{esc(msp.get('motion_clip_every_seconds'))}</code></td><td class='b'></td></tr>",
                f"<tr><td class='k'>motion_clip_duration_seconds</td><td class='v'><code>{esc(msp.get('motion_clip_duration_seconds'))}</code></td><td class='b'></td></tr>",
                f"<tr><td class='k'>max_motion_clips</td><td class='v'><code>{esc(msp.get('max_motion_clips'))}</code></td><td class='b'></td></tr>",
                f"<tr><td class='k'>slots (count)</td><td class='v'><code>{esc(nslots)}</code></td><td class='b'></td></tr>",
            ]
        )
        slots = msp.get("slots")
        if isinstance(slots, list) and slots:
            preview = json.dumps(slots[:16], ensure_ascii=False, indent=2)
            ms_rows += f"<tr><td class='k'>slots (preview)</td><td class='v' colspan='2'><pre style=\"margin:0;white-space:pre-wrap;font-size:11px\">{esc(preview)}</pre></td></tr>"
    else:
        ms_rows = "<tr><td class='k'>motion_slot_plan</td><td class='v'><em>—</em></td><td class='b'></td></tr>"

    mac = payload.get("motion_clip_artifact")
    ma_rows = ""
    if isinstance(mac, dict) and mac:
        ma_rows = "\n".join(
            [
                f"<tr><td class='k'>rendered_count</td><td class='v'><code>{esc(mac.get('rendered_count'))}</code></td><td class='b'></td></tr>",
                f"<tr><td class='k'>failed_count</td><td class='v'><code>{esc(mac.get('failed_count'))}</code></td><td class='b'></td></tr>",
                f"<tr><td class='k'>skipped_count</td><td class='v'><code>{esc(mac.get('skipped_count'))}</code></td><td class='b'></td></tr>",
                f"<tr><td class='k'>video_clip_paths</td><td class='v'><code>{esc(mac.get('video_clip_paths'))}</code></td><td class='b'></td></tr>",
            ]
        )
    else:
        ma_rows = "<tr><td class='k'>motion_clip_artifact</td><td class='v'><em>—</em></td><td class='b'></td></tr>"

    tp_section = _build_open_me_thumbnail_pack_section(payload, esc)
    pb_section = _build_open_me_production_bundle_section(payload, esc)

    if status == "gold_mini_ready":
        badge, badge_cls = "Gold Mini", "ok"
    elif status == "production_ready":
        badge, badge_cls = "Ready", "ok"
    elif status == "mixed_preview":
        badge, badge_cls = "Teilweise", "warn"
    elif status == "fallback_preview":
        badge, badge_cls = "Fallback / Preview", "warn"
    else:
        badge, badge_cls = "Failed", "bad"
    if status == "production_ready":
        smoke_text = (
            "Smoke erfolgreich; Silent Render erwartet."
            if silent_render_note
            else "Real Production Smoke erfolgreich prüfen"
        )
    elif status == "gold_mini_ready":
        smoke_text = "Smoke erfolgreich; Produktionspaket (strict_ready + Bundle)."
    elif status == "mixed_preview":
        smoke_text = "Smoke abgeschlossen mit Einschränkungen — Details in Warnungen prüfen."
    elif status == "fallback_preview":
        smoke_text = "Smoke lief, aber Fallbacks wurden genutzt"
    else:
        smoke_text = "Smoke fehlgeschlagen"
    if (
        status == "fallback_preview"
        and "Silent Render ist erwartet" in expl
    ):
        smoke_text = smoke_text + " Keine Voice ausgewählt; Silent Render ist erwartet."

    return f"""<!doctype html>
<html lang="de">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Video Generate Ergebnis</title>
  <style>
    :root {{ --bg:#0b1220; --fg:#e5e7eb; --muted:#9aa4b2; --card:#101a2e; --border:rgba(148,163,184,.25); --ok:#22c55e; --warn:#f59e0b; --bad:#ef4444; }}
    body {{ margin:0; padding:24px; background:var(--bg); color:var(--fg); font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif; }}
    .card {{ background:var(--card); border:1px solid var(--border); border-radius:14px; padding:16px 18px; max-width:980px; margin:0 auto; }}
    h1 {{ margin:0 0 8px; font-size:18px; }}
    .sub {{ margin:0 0 10px; color:var(--muted); font-size:13px; line-height:1.45; }}
    .row {{ display:flex; flex-wrap:wrap; gap:10px 14px; align-items:center; justify-content:space-between; }}
    .pill {{ padding:4px 10px; border-radius:999px; font-size:12px; font-weight:700; letter-spacing:.06em; border:1px solid var(--border); }}
    .pill.ok {{ border-color:rgba(34,197,94,.4); color:#bbf7d0; background:rgba(34,197,94,.12); }}
    .pill.warn {{ border-color:rgba(245,158,11,.5); color:#fde68a; background:rgba(245,158,11,.10); }}
    .pill.bad {{ border-color:rgba(239,68,68,.5); color:#fecaca; background:rgba(239,68,68,.12); }}
    code {{ color:#e5e7eb; font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace; font-size:12px; }}
    h2 {{ margin:16px 0 8px; font-size:14px; }}
    table {{ width:100%; border-collapse:collapse; }}
    td {{ padding:8px 6px; border-top:1px solid var(--border); vertical-align:top; }}
    td.k {{ width:220px; color:var(--muted); font-size:12px; }}
    td.v {{ font-size:12px; }}
    td.b {{ width:140px; text-align:right; font-weight:700; font-size:12px; }}
    ul {{ margin:6px 0 0; padding-left:18px; color:var(--fg); }}
    .muted {{ color:var(--muted); font-size:12px; }}
  </style>
</head>
<body>
  <div class="card">
    <div class="row">
      <div>
        <h1>Video Generate Ergebnis</h1>
        <p class="sub">{esc(expl)}</p>
      </div>
      <span class="pill {badge_cls}">{esc(badge)}</span>
    </div>

    <h2>Run</h2>
    <table>
      <tr><td class="k">run_id</td><td class="v"><code>{esc(run_id) if run_id else "—"}</code></td><td class="b">{esc("OK" if ok else "BLOCKED")}</td></tr>
      <tr><td class="k">status</td><td class="v"><code>{esc(status)}</code></td><td class="b"></td></tr>
    </table>

    <h2>Smoke Result</h2>
    <table>
      <tr><td class="k">smoke</td><td class="v">{esc(smoke_text)}</td><td class="b"></td></tr>
    </table>

    <h2>Artefakte / Pfade</h2>
    <table>
      {art_rows}
    </table>

    <h2>Asset Artifact</h2>
    <table>
      {aa_rows if aa_rows else "<tr><td class='k'>asset_artifact</td><td class='v'><em>—</em></td><td class='b'></td></tr>"}
    </table>

    <h2>Image Asset Audit (BA 32.72)</h2>
    <table>
      {ia_rows if ia_rows else "<tr><td class='k'>image_asset_audit</td><td class='v'><em>—</em></td><td class='b'></td></tr>"}
    </table>

    <h2>Produktions-Check</h2>
    <table>
      {qc_rows}
    </table>

    <h2>Voice Artifact</h2>
    <table>
      {va_rows if va_rows else "<tr><td class='k'>voice_artifact</td><td class='v'><em>—</em></td><td class='b'></td></tr>"}
    </table>

    <h2>Readiness Audit (Debug)</h2>
    <table>
      {ra_rows if ra_rows else "<tr><td class='k'>readiness_audit</td><td class='v'><em>—</em></td><td class='b'></td></tr>"}
    </table>

    <h2>Timing / Voice Fit</h2>
    <table>
      {ta_rows if ta_rows else "<tr><td class='k'>timing_audit</td><td class='v'><em>—</em></td><td class='b'></td></tr>"}
    </table>

    <h2>Motion Slot Plan (BA 32.62)</h2>
    <table>
      {ms_rows}
    </table>

    <h2>Motion Clip Artifact (BA 32.63)</h2>
    <table>
      {ma_rows}
    </table>

    <h2>Thumbnail Pack (BA 32.77)</h2>
    {tp_section}

    <h2>Production Bundle (BA 32.79)</h2>
    {pb_section}

    <h2>Warnings</h2>
    <ul>{li(warnings)}</ul>

    <h2>Blocking Reasons</h2>
    <ul>{li(blockers)}</ul>

    <p class="muted" style="margin-top:14px">Hinweis: Dieser Bericht ist lokal generiert (keine externen Assets).</p>
  </div>
</body>
</html>"""


def write_open_me_video_result_report(
    *,
    output_dir: Path,
    payload: Dict[str, Any],
) -> Tuple[Optional[Path], Optional[str]]:
    """Returns (path, warning_code). Never raises."""
    try:
        out = Path(output_dir).resolve()
        out.mkdir(parents=True, exist_ok=True)
        p = out / "OPEN_ME_VIDEO_RESULT.html"
        p.write_text(build_open_me_video_result_html(payload), encoding="utf-8")
        return p, None
    except Exception as e:
        reason = (str(e) or e.__class__.__name__).strip().replace("\n", " ")[:140]
        return None, f"open_me_video_result_report_failed:{reason}"


def _load_run_url_to_final_mod():
    p = _REPO_ROOT / "scripts" / "run_url_to_final_mp4.py"
    name = "run_url_to_final_mp4_ba323"
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, p)
    assert spec and spec.loader
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


def runway_live_configured() -> bool:
    """Nur Präsenzsignal — niemals Key-Werte loggen oder zurückgeben."""
    return bool((os.environ.get("RUNWAY_API_KEY") or "").strip())


def resolve_voice_mode_dashboard(requested: str) -> Tuple[str, List[str]]:
    """Mappt Dashboard-Strings auf ``run_ba265_url_to_final``-Voice-Modi."""
    warns: List[str] = []
    r = (requested or "").strip().lower()
    if r in ("elevenlabs_or_safe_default", ""):
        if (os.environ.get("ELEVENLABS_API_KEY") or "").strip():
            return "elevenlabs", warns
        warns.append("ba323_voice_mode_fallback_dummy_no_elevenlabs_key")
        return "dummy", warns
    allowed = frozenset({"none", "elevenlabs", "dummy", "openai", "existing"})
    if r not in allowed:
        warns.append("ba323_voice_mode_unknown_fallback_dummy")
        return "dummy", warns
    if r == "elevenlabs" and not (os.environ.get("ELEVENLABS_API_KEY") or "").strip():
        warns.append("ba323_voice_elevenlabs_requested_fallback_dummy")
        return "dummy", warns
    if r == "openai" and not (os.environ.get("OPENAI_API_KEY") or "").strip():
        warns.append("ba323_voice_openai_requested_fallback_dummy")
        return "dummy", warns
    return r, warns


def new_video_gen_run_id() -> str:
    return f"video_gen_10m_{int(time.time() * 1000)}"


def derive_motion_readiness_fields(
    *,
    allow_live_motion: bool,
    live_motion_available: bool,
    max_motion_clips: int,
    motion_slot_plan: Optional[Dict[str, Any]],
    motion_clip_artifact: Optional[Dict[str, Any]],
    generation_modes: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    BA 32.64 — Motion-Readiness aus Manifest/Slot-Artefakt, unabhängig von der
    reinen „Runway-Checkbox“ (``allow_live_motion`` = Connector-Anfrage).
    """
    msp = motion_slot_plan if isinstance(motion_slot_plan, dict) else {}
    mac = motion_clip_artifact if isinstance(motion_clip_artifact, dict) else {}
    gm = generation_modes if isinstance(generation_modes, dict) else {}

    def _i(x: Any, default: int = 0) -> int:
        try:
            return int(x)
        except (TypeError, ValueError):
            return default

    planned_slots = _i(msp.get("planned_count"))
    planned_art = _i(mac.get("planned_count"))
    rendered = _i(mac.get("rendered_count"))
    runway_live = _i(gm.get("runway_video_live"))

    motion_requested = (
        int(max_motion_clips) > 0
        or bool(msp.get("enabled"))
        or planned_slots > 0
        or planned_art > 0
    )
    motion_rendered = rendered > 0 or runway_live > 0
    motion_ready = motion_rendered or (bool(live_motion_available) and bool(allow_live_motion))

    return {
        "motion_requested": bool(motion_requested),
        "motion_rendered": bool(motion_rendered),
        "motion_ready": bool(motion_ready),
    }


def video_generate_output_dir(out_root: Path, run_id: str) -> Path:
    base = Path(out_root).resolve()
    return (base / "video_generate" / str(run_id).strip()).resolve()


def _ordered_thumbnail_candidate_paths(candidate_paths: Any) -> List[str]:
    cpaths = candidate_paths if isinstance(candidate_paths, dict) else {}
    order = ["thumb_a", "thumb_b", "thumb_c"]
    out: List[str] = []
    seen: set[str] = set()
    for k in order:
        p = str(cpaths.get(k) or "").strip()
        if p and Path(p).is_file() and p not in seen:
            out.append(p)
            seen.add(p)
    for k in sorted(cpaths.keys(), key=lambda x: str(x)):
        p = str(cpaths.get(k) or "").strip()
        if p and Path(p).is_file() and p not in seen:
            out.append(p)
            seen.add(p)
    return out


def _derive_thumbnail_title_summary_for_pack(
    *,
    title: Optional[str],
    raw_text: Optional[str],
    script_text: Optional[Dict[str, Any]],
    doc: Dict[str, Any],
    thumbnail_title_override: Optional[str],
    thumbnail_summary_override: Optional[str],
) -> Tuple[str, str]:
    """Titel/Zeilen für Thumbnail-Text — keine Secrets."""
    ov_t = (thumbnail_title_override or "").strip()
    ov_s = (thumbnail_summary_override or "").strip()
    st = script_text if isinstance(script_text, dict) else None

    if ov_t:
        t = ov_t
    else:
        t = (title or "").strip()
        if not t and st:
            t = str(st.get("title") or "").strip()
        if not t:
            t = str(doc.get("title") or "").strip()
        if not t and st:
            t = str(st.get("hook") or "").strip()[:140]

    if ov_s:
        s = ov_s
    else:
        s = ""
        if st:
            s = str(st.get("hook") or "").strip()
            if not s:
                fs = st.get("full_script")
                if isinstance(fs, str) and fs.strip():
                    s = fs.strip()[:500]
        if not s:
            s = (raw_text or "").strip()[:500]

    if not t:
        t = (s[:120] if s else "Video")
    if not s:
        s = t
    return t, s


def execute_dashboard_video_generate(
    *,
    url: Optional[str],
    raw_text: Optional[str] = None,
    title: Optional[str] = None,
    script_text: Optional[Dict[str, Any]] = None,
    source_youtube_url: Optional[str] = None,
    rewrite_style: Optional[str] = None,
    video_template: Optional[str] = None,
    target_language: str = "de",
    output_dir: Path,
    run_id: str,
    duration_target_seconds: int,
    max_scenes: int,
    max_live_assets: int,
    motion_clip_every_seconds: int,
    motion_clip_duration_seconds: int,
    max_motion_clips: int,
    allow_live_assets: bool,
    allow_live_motion: bool,
    voice_mode: str,
    motion_mode: str,
    image_provider: Optional[str] = None,
    openai_image_model: Optional[str] = None,
    openai_image_size: Optional[str] = None,
    openai_image_timeout_seconds: Optional[float] = None,
    # BA 32.72b — dev-only, transient per-request key overrides.
    # Niemals zurückgeben, loggen oder persistieren.
    dev_openai_api_key: Optional[str] = None,
    dev_elevenlabs_api_key: Optional[str] = None,
    dev_runway_api_key: Optional[str] = None,
    dev_leonardo_api_key: Optional[str] = None,
    # BA 32.78 — optional Thumbnail Pack (OpenAI Candidates + lokales Overlay)
    generate_thumbnail_pack: bool = False,
    thumbnail_candidate_count: int = 3,
    thumbnail_max_outputs: int = 6,
    thumbnail_model: Optional[str] = None,
    thumbnail_size: Optional[str] = None,
    thumbnail_style_presets: Optional[List[str]] = None,
    thumbnail_title_override: Optional[str] = None,
    thumbnail_summary_override: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Ruft ``run_ba265_url_to_final`` auf. Optional (``max_motion_clips`` ≥ 1 + Key)
    ein Runway Motion-Clip pro Lauf — siehe BA 32.63; Readiness BA 32.64.
    """
    def _tmp_env_overrides(overrides: Dict[str, Optional[str]]) -> Dict[str, Optional[str]]:
        """
        Setzt ENV nur transient für den laufenden Request.
        Rückgabe: vorherige Werte (None bedeutet „nicht gesetzt“), zum Restore.
        """
        prev: Dict[str, Optional[str]] = {}
        for k, v in (overrides or {}).items():
            if v is None:
                continue
            s = str(v).strip()
            if not s:
                continue
            prev[k] = os.environ.get(k)
            os.environ[k] = s
        return prev

    def _restore_env(prev: Dict[str, Optional[str]]) -> None:
        for k, old in (prev or {}).items():
            if old is None:
                try:
                    del os.environ[k]
                except KeyError:
                    pass
            else:
                os.environ[k] = old

    env_prev: Dict[str, Optional[str]] = {}
    try:
        env_prev = _tmp_env_overrides(
            {
                "OPENAI_API_KEY": dev_openai_api_key,
                "ELEVENLABS_API_KEY": dev_elevenlabs_api_key,
                "RUNWAY_API_KEY": dev_runway_api_key,
                "LEONARDO_API_KEY": dev_leonardo_api_key,
            }
        )

        mod = _load_run_url_to_final_mod()
        vm, vm_warns = resolve_voice_mode_dashboard(voice_mode)
        live_motion_available = runway_live_configured()
        warnings_extra: List[str] = list(vm_warns)
        requested_voice_mode = (voice_mode or "").strip().lower() or "none"
        pr = build_provider_readiness()

        if allow_live_motion and live_motion_available and int(max_motion_clips) <= 0:
            warnings_extra.append(
                "ba323_live_motion_allowed_but_max_motion_clips_zero_no_runway_slot_rendering"
            )

        mm = (motion_mode or "basic").strip().lower()
        if mm not in ("static", "basic"):
            mm = "basic"
            warnings_extra.append("ba323_motion_mode_invalid_fallback_basic")

        req_ip = (image_provider or "").strip() or None
        req_oai_m = (str(openai_image_model).strip() if openai_image_model is not None else None) or None
        if allow_live_assets and (req_ip or "").strip().lower() == "openai_image" and not req_oai_m:
            req_oai_m = "gpt-image-2"
        req_oai_sz = (str(openai_image_size).strip() if openai_image_size is not None else None) or None
        req_oai_to = float(openai_image_timeout_seconds) if openai_image_timeout_seconds is not None else None
        had_img_opts = bool(req_ip) or any(
            x is not None for x in (openai_image_model, openai_image_size, openai_image_timeout_seconds)
        )
        if had_img_opts and not allow_live_assets:
            warnings_extra.append("ba372_image_generation_options_ignored_without_live_assets")

        ba265_img_kw: Dict[str, Any] = {}
        if allow_live_assets:
            if req_ip:
                ba265_img_kw["image_provider"] = req_ip
            if req_oai_m:
                ba265_img_kw["openai_image_model"] = req_oai_m
            if req_oai_sz:
                ba265_img_kw["openai_image_size"] = req_oai_sz
            if req_oai_to is not None:
                ba265_img_kw["openai_image_timeout_seconds"] = req_oai_to

        doc = mod.run_ba265_url_to_final(
            url=(url or "").strip() if isinstance(url, str) else None,
            raw_text=(raw_text or ""),
            title=(title or "") if isinstance(title, str) else "",
            script_json_path=None,
            inline_script=script_text,
            source_youtube_url=(source_youtube_url or "").strip() or None,
            rewrite_style=(rewrite_style or "").strip() or None,
            video_template=(video_template or "").strip() or None,
            target_language=(target_language or "de").strip() or "de",
            out_dir=Path(output_dir).resolve(),
            max_scenes=int(max_scenes),
            duration_seconds=int(duration_target_seconds),
            asset_dir=None,
            run_id=str(run_id).strip(),
            motion_mode=mm,
            voice_mode=vm,
            asset_runner_mode="live" if allow_live_assets else "placeholder",
            max_live_assets=int(max_live_assets) if allow_live_assets else None,
            motion_clip_every_seconds=int(motion_clip_every_seconds),
            motion_clip_duration_seconds=int(motion_clip_duration_seconds),
            max_motion_clips=int(max_motion_clips),
            **ba265_img_kw,
        )
    finally:
        try:
            _restore_env(env_prev)
        except Exception:
            # Best-effort Restore; niemals crashen (aber auch niemals loggen)
            pass

    warnings = list(doc.get("warnings") or []) + warnings_extra
    blocking = list(doc.get("blocking_reasons") or [])
    ok = bool(doc.get("ok"))

    msp_from_doc = doc.get("motion_slot_plan") if isinstance(doc.get("motion_slot_plan"), dict) else None
    msc_from_doc = doc.get("motion_slot_count")
    try:
        msc_int = int(msc_from_doc) if msc_from_doc is not None else int((msp_from_doc or {}).get("planned_count") or 0)
    except (TypeError, ValueError):
        msc_int = 0

    mac = doc.get("motion_clip_artifact") if isinstance(doc.get("motion_clip_artifact"), dict) else {}

    next_action = "Final Video prüfen" if ok else "Fehler prüfen und Parameter anpassen"

    joined = " ".join(str(x or "") for x in (warnings or [])).lower()
    has_voice_fallback = any(sig in joined for sig in ("dummy", "voice_mode_fallback", "no_elevenlabs_key"))
    live_motion_available = bool(live_motion_available)

    asset_artifact = build_asset_artifact(asset_manifest_path=str(doc.get("asset_manifest_path") or ""))
    ara_doc = doc.get("asset_runner_audit") if isinstance(doc.get("asset_runner_audit"), dict) else {}
    oro_doc = ara_doc.get("openai_image_runner_options")
    if not isinstance(oro_doc, dict):
        oro_doc = {}
    image_asset_audit = {
        "requested_image_provider": req_ip if allow_live_assets else None,
        "requested_openai_image_model": req_oai_m if allow_live_assets else None,
        "requested_openai_image_size": req_oai_sz if allow_live_assets else None,
        "requested_openai_image_timeout_seconds": req_oai_to if allow_live_assets else None,
        "effective_image_provider": ara_doc.get("effective_image_provider"),
        "openai_image_runner_options": oro_doc if oro_doc else None,
        "asset_manifest_file_count": asset_artifact.get("asset_manifest_file_count"),
        "real_asset_file_count": asset_artifact.get("real_asset_file_count"),
        "asset_manifest_path": str(doc.get("asset_manifest_path") or ""),
    }
    gen_modes = asset_artifact.get("generation_modes") if isinstance(asset_artifact.get("generation_modes"), dict) else {}
    motion_rd = derive_motion_readiness_fields(
        allow_live_motion=bool(allow_live_motion),
        live_motion_available=bool(live_motion_available),
        max_motion_clips=int(max_motion_clips),
        motion_slot_plan=msp_from_doc,
        motion_clip_artifact=mac,
        generation_modes=gen_modes,
    )
    try:
        planned_slots_int = int((msp_from_doc or {}).get("planned_count") or msc_int)
    except (TypeError, ValueError):
        planned_slots_int = msc_int
    try:
        rendered_int = int(mac.get("rendered_count") or 0)
    except (TypeError, ValueError):
        rendered_int = 0

    motion_strategy = {
        "motion_clip_every_seconds": int(motion_clip_every_seconds),
        "motion_clip_duration_seconds": int(motion_clip_duration_seconds),
        "max_motion_clips": int(max_motion_clips),
        "planned_motion_slot_count": planned_slots_int,
        "runway_motion_rendered_count": rendered_int,
        "motion_requested": bool(motion_rd["motion_requested"]),
        "motion_rendered": bool(motion_rd["motion_rendered"]),
        "motion_fallback_to_image": False,
        "motion_skipped_reason": None,
        "live_motion_available": bool(live_motion_available),
        "allow_live_motion_requested": bool(allow_live_motion),
    }

    allow_live_motion_requested = bool(allow_live_motion)

    provider_blockers: List[str] = []
    requested_live_assets = bool(allow_live_assets)
    if not requested_live_assets:
        provider_blockers.append("live_assets_not_requested")
    else:
        # Asset runner live-mode requires provider env; if missing it falls back to placeholder with warning.
        if (
            "leonardo_env_missing_fallback_placeholder" in joined
            or "openai_image_key_missing_fallback_placeholder" in joined
            or "gemini_image_key_missing_fallback_placeholder" in joined
        ):
            provider_blockers.append("live_asset_provider_not_configured")
        # Live requested but still no real files => nothing real was produced/used.
        if int(asset_artifact.get("real_asset_file_count") or 0) <= 0:
            provider_blockers.append("no_real_asset_files")
    if "ba323_voice_mode_fallback_dummy_no_elevenlabs_key" in (warnings or []):
        provider_blockers.append("missing_elevenlabs_key")
    if allow_live_motion_requested and not live_motion_available:
        provider_blockers.append("live_motion_disabled_or_connector_missing")
    if not live_motion_available and not bool(motion_rd["motion_rendered"]):
        provider_blockers.append("live_motion_not_available")

    silent_render_expected, silent_render_reason = _silent_render_audit_fields(
        effective_voice_mode=vm,
        requested_voice_mode=requested_voice_mode,
    )

    voice_artifact = build_voice_artifact(
        output_dir=Path(output_dir).resolve(),
        requested_voice_mode=requested_voice_mode,
        effective_voice_mode=vm,
    )
    render_used_placeholders = (
        any(sig in joined for sig in ("ba266_cinematic_placeholder_applied",))
        or (
            _RENDER_LAYER_AUDIO_SILENT_SIGNAL in joined
            and (vm != "none")
            and not silent_render_expected
            and not bool(voice_artifact.get("voice_ready"))
        )
    )
    motion_fallback_to_image = (
        bool(motion_rd["motion_requested"])
        and not bool(motion_rd["motion_rendered"])
        and bool(str(doc.get("final_video_path") or "").strip())
        and requested_live_assets
        and int(asset_artifact.get("real_asset_file_count") or 0) > 0
        and bool(((asset_artifact.get("asset_quality_gate") or {}).get("strict_ready")) if isinstance(asset_artifact.get("asset_quality_gate"), dict) else False)
        and bool(voice_artifact.get("voice_ready"))
        and not render_used_placeholders
    )
    if motion_fallback_to_image and "motion_requested_but_no_clip_fallback_to_image" not in warnings:
        warnings.append("motion_requested_but_no_clip_fallback_to_image")
    motion_strategy["motion_fallback_to_image"] = bool(motion_fallback_to_image)
    motion_strategy["motion_skipped_reason"] = (
        "motion_requested_but_no_clip_fallback_to_image" if motion_fallback_to_image else None
    )

    readiness_audit = {
        "requested_live_assets": requested_live_assets,
        "requested_voice_mode": requested_voice_mode,
        "script_ready": bool(str(doc.get("script_path") or "").strip()),
        "scene_asset_pack_ready": bool(str(doc.get("scene_asset_pack_path") or "").strip()),
        "asset_manifest_ready": bool(str(doc.get("asset_manifest_path") or "").strip()),
        "asset_runner_mode": "live" if requested_live_assets else "placeholder",
        "real_assets_ready": requested_live_assets and int(asset_artifact.get("real_asset_file_count") or 0) > 0,
        "asset_quality_status": ((asset_artifact.get("asset_quality_gate") or {}).get("status") if isinstance(asset_artifact.get("asset_quality_gate"), dict) else None),
        "asset_strict_ready": bool(((asset_artifact.get("asset_quality_gate") or {}).get("strict_ready")) if isinstance(asset_artifact.get("asset_quality_gate"), dict) else False),
        "asset_loose_ready": bool(((asset_artifact.get("asset_quality_gate") or {}).get("loose_ready")) if isinstance(asset_artifact.get("asset_quality_gate"), dict) else False),
        # voice_ready: produktiver Voice-Modus (z. B. elevenlabs) + Provider-ENV, ohne Dummy-Fallback.
        # Ob eine TTS-Datei existiert, steht in voice_file_ready (nach build_voice_artifact).
        "voice_ready": (vm not in ("none", "dummy")) and not has_voice_fallback,
        "voice_provider_ready": (
            True
            if requested_voice_mode in ("dummy", "none", "existing", "")
            else (
                (requested_voice_mode == "elevenlabs" and (pr.get("voice_elevenlabs") or {}).get("status") == "ready")
                or (requested_voice_mode == "openai" and (pr.get("voice_openai") or {}).get("status") == "ready")
            )
        ),
        "voice_provider_blocker": (
            None
            if requested_voice_mode in ("dummy", "none", "existing", "")
            else (
                "missing_elevenlabs_key"
                if requested_voice_mode == "elevenlabs" and (pr.get("voice_elevenlabs") or {}).get("status") != "ready"
                else (
                    "missing_openai_key"
                    if requested_voice_mode == "openai" and (pr.get("voice_openai") or {}).get("status") != "ready"
                    else None
                )
            )
        ),
        "motion_ready": bool(motion_rd["motion_ready"]),
        "motion_requested": bool(motion_rd["motion_requested"]),
        "motion_rendered": bool(motion_rd["motion_rendered"]),
        "motion_fallback_to_image": bool(motion_fallback_to_image),
        "motion_skipped_reason": "motion_requested_but_no_clip_fallback_to_image" if motion_fallback_to_image else None,
        "render_used_placeholders": bool(render_used_placeholders),
        "provider_blockers": provider_blockers,
        "effective_voice_mode": vm,
        "live_motion_available": bool(live_motion_available),
        "allow_live_motion_requested": bool(allow_live_motion_requested),
        "silent_render_expected": bool(silent_render_expected),
        "silent_render_reason": silent_render_reason,
    }

    readiness_audit["voice_file_path_present"] = bool(str(voice_artifact.get("voice_file_path") or "").strip())
    readiness_audit["voice_file_ready"] = bool(voice_artifact.get("voice_ready"))
    readiness_audit["voice_is_dummy"] = bool(voice_artifact.get("is_dummy"))

    thumb_attach_ran = False
    key_missing_thumb = False
    if generate_thumbnail_pack and not ok:
        warnings.append("ba3278_thumbnail_pack_skipped_video_not_ok")
    elif generate_thumbnail_pack and ok:
        thumb_attach_ran = True
        pack_dir = Path(output_dir).resolve() / "thumbnail_pack"
        pack_dir.mkdir(parents=True, exist_ok=True)
        env_thumb = _tmp_env_overrides({"OPENAI_API_KEY": dev_openai_api_key})
        try:
            t_title, t_summary = _derive_thumbnail_title_summary_for_pack(
                title=title,
                raw_text=raw_text,
                script_text=script_text,
                doc=doc,
                thumbnail_title_override=thumbnail_title_override,
                thumbnail_summary_override=thumbnail_summary_override,
            )
            if not (os.environ.get("OPENAI_API_KEY") or "").strip():
                key_missing_thumb = True
                warnings.append("ba3278_thumbnail_pack_openai_key_missing")
            else:
                eff_to = (
                    float(openai_image_timeout_seconds)
                    if openai_image_timeout_seconds is not None
                    else 120.0
                )
                eff_tm = (str(thumbnail_model).strip() if thumbnail_model else "") or None
                eff_ts = (str(thumbnail_size).strip() if thumbnail_size else "") or "1024x1024"
                cand_res = run_thumbnail_candidates_v1(
                    output_dir=pack_dir,
                    title=t_title,
                    summary=t_summary,
                    count=int(thumbnail_candidate_count),
                    target_platform="youtube",
                    model=eff_tm,
                    size=eff_ts,
                    timeout_seconds=eff_to,
                    dry_run=False,
                )
                warnings.extend(list(cand_res.get("warnings") or []))
                ordered = _ordered_thumbnail_candidate_paths(cand_res.get("candidate_paths"))
                if not ordered:
                    warnings.append("ba3278_thumbnail_pack_no_candidate_images")
                else:
                    batch_res = run_thumbnail_batch_overlay_v1(
                        candidate_paths=ordered,
                        title=t_title,
                        summary=t_summary,
                        output_dir=pack_dir,
                        language=(target_language or "de").strip() or "de",
                        max_outputs=int(thumbnail_max_outputs),
                        style_presets=thumbnail_style_presets,
                    )
                    warnings.extend(list(batch_res.get("warnings") or []))
                    if not batch_res.get("ok"):
                        warnings.append("ba3278_thumbnail_batch_overlay_incomplete")
        except Exception as e:
            warnings.append(f"ba3278_thumbnail_pack_attach_failed:{type(e).__name__}")
        finally:
            _restore_env(env_thumb)

    thumb_pack = load_thumbnail_pack_v1(output_dir=Path(output_dir).resolve())
    if generate_thumbnail_pack:
        thumb_pack = dict(thumb_pack)
        thumb_pack["thumbnail_pack_auto_attach"] = True
        thumb_pack["thumbnail_pack_auto_attach_ran"] = bool(thumb_attach_ran)
        st0 = str(thumb_pack.get("thumbnail_pack_status") or "")
        if thumb_attach_ran and st0 == "missing_report":
            if key_missing_thumb:
                thumb_pack["thumbnail_pack_status"] = "warning"
            else:
                thumb_pack["thumbnail_pack_status"] = "failed"

    out_resolved = Path(output_dir).resolve()
    pb = build_production_bundle_v1(
        output_dir=out_resolved,
        run_id=str(run_id).strip(),
        final_video_path=str(doc.get("final_video_path") or ""),
        script_path=str(doc.get("script_path") or ""),
        scene_asset_pack_path=str(doc.get("scene_asset_pack_path") or ""),
        asset_manifest_path=str(doc.get("asset_manifest_path") or ""),
        open_me_path=None,
        thumbnail_pack=thumb_pack,
        warnings=list(warnings),
    )
    for w in list(pb.get("warnings") or []):
        if w and w not in warnings:
            warnings.append(w)

    out_payload: Dict[str, Any] = {
        "ok": ok,
        "run_id": str(run_id).strip(),
        "input_mode": doc.get("input_mode"),
        "source_youtube_url": doc.get("source_youtube_url"),
        "transcript_available": doc.get("transcript_available"),
        "generated_original_script": doc.get("generated_original_script"),
        "output_dir": str(doc.get("output_dir") or ""),
        "final_video_path": str(doc.get("final_video_path") or ""),
        "script_path": str(doc.get("script_path") or ""),
        "scene_asset_pack_path": str(doc.get("scene_asset_pack_path") or ""),
        "asset_manifest_path": str(doc.get("asset_manifest_path") or ""),
        "timing_audit": (doc.get("timing_audit") if isinstance(doc.get("timing_audit"), dict) else {}),
        "duration_target_seconds": int(duration_target_seconds),
        "max_scenes": int(max_scenes),
        "max_live_assets": int(max_live_assets),
        "motion_strategy": motion_strategy,
        "motion_slot_plan": msp_from_doc,
        "motion_slot_count": msc_int,
        "motion_clip_artifact": (
            doc.get("motion_clip_artifact") if isinstance(doc.get("motion_clip_artifact"), dict) else None
        ),
        "warnings": warnings,
        "blocking_reasons": blocking,
        "next_action": next_action,
        "readiness_audit": readiness_audit,
        "provider_readiness": pr,
        "asset_artifact": asset_artifact,
        "voice_artifact": voice_artifact,
        "asset_runner_audit": doc.get("asset_runner_audit")
        if isinstance(doc.get("asset_runner_audit"), dict)
        else None,
        "image_asset_audit": image_asset_audit,
        "thumbnail_pack": thumb_pack,
        "production_bundle": pb,
    }
    try:
        scrub_video_generate_warnings_ba3280(out_payload)
        _st_o = derive_video_generate_status(out_payload)
        out_payload["video_generate_run_status"] = _st_o
        out_payload["video_generate_operator"] = build_video_generate_operator_ui_ba3280(_st_o, out_payload)
    except Exception:
        pass
    return out_payload
