"""BA 25.5 / BA 25.6 — URL-to-Final-Video Smoke (lokal, one-command).

Ziel: lokaler End-to-End Smoke von URL → final_video.mp4, ohne Publishing.

**BA 25.6** härtet den Runner: klares Result-Schema, Auto-Approve-Kennzeichnung,
strukturierte Fehlerstufen, Idempotenz-Anzeige (`skipped_existing`), Operator-OPEN_ME.

Wiring (bestehende Runner, nur verdrahten):

URL
  → BA 25.3: scripts/run_url_to_script_bridge.py (oder run_bridge())
  → generate_script_response.json
  → BA 25.4: scripts/run_ba_25_4_local_preview.py (oder run_real_local_preview())
  → preview_with_subtitles.mp4 (real build chain)
  → BA 25.5/25.6: schreibt local_preview_<run_id>/ Snapshot + optional human_approval.json (Smoke-only)
  → BA 24.3: scripts/run_final_render.py (oder run_final_render_for_local_preview())
  → final_render_<run_id>/final_video.mp4

Grenzen:
- Kein Publishing/Upload/Scheduling.
- Keine neuen Provider-Integrationen; placeholder/smoke sind ok.
- GenerateScriptResponse-Vertrag bleibt unverändert (nur reuse).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Sequence

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.run_url_to_script_bridge import run_bridge
from scripts.run_ba_25_4_local_preview import run_real_local_preview
from scripts.run_final_render import run_final_render_for_local_preview

_RUN_ID_RE = re.compile(r"^[A-Za-z0-9_-]{1,80}$")

RESULT_SCHEMA = "ba_25_6_url_to_final_video_result_v1"
RESULT_FILENAME = "url_to_final_video_result.json"
OPEN_ME_FILENAME = "URL_TO_FINAL_VIDEO_OPEN_ME.md"

EXIT_OK = 0
EXIT_FAILED = 1
EXIT_BLOCKED = 2
EXIT_INVALID_INPUT = 3

# Strukturierte Fehlerstufen (kein Stacktrace im JSON-Pfad)
FAILURE_INPUT = "input_validation"
FAILURE_BRIDGE = "ba25_3_url_to_script_bridge"
FAILURE_PREVIEW = "ba25_4_real_local_preview"
FAILURE_ADAPTER = "ba25_5_preview_adapter"
FAILURE_APPROVAL_GATE = "human_approval_gate"
FAILURE_FINAL_RENDER = "ba24_3_final_render"
FAILURE_INTERNAL = "internal_unexpected"

DEFAULT_APPROVAL_NOTE = (
    "Smoke/Dev auto-approval (BA 25.6). Nur für lokale MVP-Smoke-Tests; vor Publishing manuell prüfen."
)


def _s(v: Any) -> str:
    if v is None:
        return ""
    return str(v).strip()


def _list_str(x: Any) -> List[str]:
    if x is None:
        return []
    if isinstance(x, list):
        return [str(i) for i in x if i is not None and str(i).strip() != ""]
    if isinstance(x, (str, int, float, bool)):
        t = str(x).strip()
        return [t] if t else []
    return [str(x)]


def _validate_run_id(run_id: str) -> bool:
    s = (run_id or "").strip()
    if not s or ".." in s or "/" in s or "\\" in s:
        return False
    return bool(_RUN_ID_RE.fullmatch(s))


def _default_run_id() -> str:
    return f"ba25_5_{int(time.time())}"


def _write_json(path: Path, obj: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _safe_nonempty_file(p: Path) -> bool:
    try:
        if p.is_symlink() or not p.is_file():
            return False
        return int(p.stat().st_size) > 0
    except OSError:
        return False


def _write_url_to_final_open_me(*, run_dir: Path, result: Dict[str, Any]) -> None:
    """Kurzer Operator-Hinweis neben dem Result-JSON (BA 25.6)."""
    auto = bool(result.get("auto_approved"))
    lines = [
        "# URL-to-Final-Video Smoke — Operator",
        "",
        f"- **schema_version**: `{result.get('schema_version', '')}`",
        f"- **run_id**: `{result.get('run_id', '')}`",
        f"- **ok**: `{result.get('ok')}`",
        f"- **status**: `{result.get('status', '')}`",
        f"- **auto_approved**: `{auto}`",
        "",
        "## Pfade",
        f"- Result JSON: `{result.get('result_json_path', '')}`",
        f"- Final Video: `{result.get('final_video_path', '')}`",
        f"- Human Approval: `{result.get('human_approval_path', '') or '—'}`",
        "",
        "## Hinweis",
    ]
    if auto:
        lines.extend(
            [
                "Dieser Lauf nutzte **Auto-Approve** (Smoke/Dev). Es wurde automatisch "
                "`human_approval.json` geschrieben, damit BA 24.x Final Render die Gates passiert. "
                "**Nicht** als Produktions-Freigabe missverstehen.",
                "",
            ]
        )
    else:
        lines.extend(
            [
                "Ohne Auto-Approve wird **kein** `human_approval.json` erzeugt und kein Final Render "
                "ausgeführt. Für den Smoke-Flow mit finalem Video: Standard (Auto-Approve an) oder "
                "manuell freigeben und `run_final_render.py` starten.",
                "",
            ]
        )
    lines.extend(
        [
            "## Nächster Schritt",
            (result.get("next_step") or "Siehe `url_to_final_video_result.json`.").strip(),
            "",
            "Kein Publishing, kein Upload in diesem Schritt.",
            "",
        ]
    )
    (run_dir / OPEN_ME_FILENAME).write_text("\n".join(lines), encoding="utf-8")


def _ensure_local_preview_package_from_ba254(
    *,
    out_root: Path,
    run_id: str,
    preview_with_subtitles_path: str,
    real_local_preview_result_path: str,
    warnings: List[str],
) -> Dict[str, str]:
    paths: Dict[str, str] = {
        "local_preview_dir": "",
        "local_preview_video": "",
        "local_preview_result": "",
        "local_preview_human_approval": "",
    }
    root = Path(out_root).resolve()
    lp_dir = root / f"local_preview_{run_id}"
    lp_dir.mkdir(parents=True, exist_ok=True)
    paths["local_preview_dir"] = str(lp_dir.resolve())

    src_preview = Path(preview_with_subtitles_path).resolve()
    dst_preview = lp_dir / "preview_with_subtitles.mp4"
    if _safe_nonempty_file(dst_preview):
        paths["local_preview_video"] = str(dst_preview.resolve())
    else:
        if not _safe_nonempty_file(src_preview):
            warnings.append("ba25_5_missing_preview_from_ba25_4")
        else:
            dst_preview.write_bytes(src_preview.read_bytes())
            paths["local_preview_video"] = str(dst_preview.resolve())

    snap = {
        "schema_version": "local_preview_result_smoke_v1",
        "run_id": run_id,
        "verdict": "PASS",
        "quality_checklist": {"status": "pass"},
        "founder_quality_decision": {
            "decision_code": "GO_PREVIEW",
            "top_issue": "",
            "next_step": "BA 25.5/25.6 smoke created this snapshot; review preview manually.",
        },
        "production_costs": {"estimated_total_cost": 0.0, "over_budget_flag": False},
        "warnings": [
            "BA 25.5/25.6 smoke: local_preview_result.json ist ein minimales Snapshot-Stub für Final Render Gates.",
            f"BA 25.5/25.6 smoke: source_real_local_preview_result={real_local_preview_result_path}",
        ],
        "created_at_epoch": int(time.time()),
    }
    snap_path = lp_dir / "local_preview_result.json"
    if not snap_path.is_file():
        _write_json(snap_path, snap)
    paths["local_preview_result"] = str(snap_path.resolve())

    return paths


def _write_human_approval(
    *,
    local_preview_dir: Path,
    run_id: str,
    note: str,
    warnings: List[str],
) -> str:
    doc = {
        "schema_version": "local_preview_human_approval_v1",
        "run_id": run_id,
        "status": "approved",
        "approved_at": time.strftime("%Y-%m-%dT%H:%M:%S+00:00", time.gmtime()),
        "approved_by": "ba25_5_smoke_runner",
        "note": (note or "").strip(),
        "source": "ba25_5_smoke",
        "auto_approved": True,
        "smoke_dev_flow": True,
    }
    p = Path(local_preview_dir).resolve() / "human_approval.json"
    _write_json(p, doc)
    warnings.append("ba25_6_auto_approved_for_smoke_dev_only")
    return str(p.resolve())


def _resolve_status_after_final(*, final_ok: bool, final_status: str, final_video: str) -> str:
    fs = (final_status or "").strip().lower()
    if not final_ok:
        return fs or "failed"
    if fs == "skipped_existing":
        return "skipped_existing"
    if final_video and _safe_nonempty_file(Path(final_video)):
        return fs if fs == "completed" else "completed"
    return fs or "completed"


def _next_step_for_result(
    *,
    ok: bool,
    status: str,
    auto_approved: bool,
    failure_stage: str,
) -> str:
    if failure_stage == FAILURE_APPROVAL_GATE:
        return (
            "Human approval required before final render. "
            "Ohne `--no-auto-approve` legt der Smoke-Runner eine Dev-Freigabe an; "
            "oder manuell `human_approval.json` im Paket `local_preview_<run_id>/` erstellen und "
            "`scripts/run_final_render.py` ausführen."
        )
    if failure_stage == FAILURE_INPUT:
        return (
            "run_id ungültig: nur A–Z, a–z, 0–9, Unterstrich und Bindestrich (max. 80), keine Pfadzeichen."
        )
    if not ok and failure_stage == FAILURE_BRIDGE:
        return "URL-Script-Bridge fehlgeschlagen: URL/Extraktion/Quelle prüfen; siehe steps.ba25_3_url_to_script und blocking_reasons."
    if not ok and failure_stage == FAILURE_PREVIEW:
        return "Real Local Preview fehlgeschlagen: ffmpeg/Artefakte prüfen; siehe steps.ba25_4_real_local_preview."
    if not ok and failure_stage == FAILURE_ADAPTER:
        return "Preview-Adapter: preview_with_subtitles fehlt oder konnte nicht ins Local-Preview-Paket kopiert werden."
    if not ok and failure_stage == FAILURE_FINAL_RENDER:
        return "Final Render fehlgeschlagen oder blockiert: Gates/Approval/Pfade prüfen; siehe steps.ba24_3_final_render."
    st = (status or "").strip().lower()
    if st == "skipped_existing":
        return "final_video.mp4 existierte bereits (>0 Byte); kein erneutes Kopieren. Mit --force neu erzwingen."
    if ok:
        return "Öffne final_video.mp4 und URL_TO_FINAL_VIDEO_OPEN_ME.md; vor Publishing manuell prüfen."
    return "Siehe blocking_reasons und warnings im Result JSON."


def run_url_to_final_video_smoke(
    *,
    url: str,
    run_id: str,
    out_root: Path,
    target_language: str = "de",
    duration_minutes: int = 3,
    source_type: str = "auto",
    asset_mode: str = "placeholder",
    voice_mode: str = "smoke",
    motion_mode: str = "static",
    subtitle_style: str = "typewriter",
    subtitle_mode: str = "simple",
    force: bool = False,
    auto_approve: bool = True,
    approval_note: str = DEFAULT_APPROVAL_NOTE,
    bridge_fn: Optional[Callable[..., Dict[str, Any]]] = None,
    preview_fn: Optional[Callable[..., Dict[str, Any]]] = None,
    final_render_fn: Optional[Callable[..., Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """
    Programmatische Eintrittsfunktion (für Tests/CI).
    Schreibt `url_to_final_video_result.json` + `URL_TO_FINAL_VIDEO_OPEN_ME.md`.
    """
    src_url = _s(url)
    rid = (run_id or "").strip()
    if not rid:
        rid = _default_run_id()

    def _fail_early(
        *,
        ok_v: bool,
        status: str,
        exit_code: int,
        warnings: List[str],
        blocking: List[str],
        paths: Dict[str, str],
        failure_stage: str,
        steps: Optional[Dict[str, Any]] = None,
        bridge_res: Optional[Dict[str, Any]] = None,
        preview_res: Optional[Dict[str, Any]] = None,
        final_res: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        merged_steps: Dict[str, Any] = dict(steps or {})
        if bridge_res is not None:
            merged_steps["ba25_3_url_to_script"] = bridge_res
        if preview_res is not None:
            merged_steps["ba25_4_real_local_preview"] = preview_res
        if final_res is not None:
            merged_steps["ba24_3_final_render"] = final_res

        scene_pack = ""
        if preview_res and isinstance(preview_res.get("paths"), dict):
            scene_pack = _s((preview_res["paths"] or {}).get("scene_asset_pack"))

        flat = _flatten_output_paths(
            paths=paths,
            scene_asset_pack_path=scene_pack,
        )
        nk = ok_v
        st = status
        result = {
            "schema_version": RESULT_SCHEMA,
            "ok": nk,
            "status": st,
            "run_id": rid,
            "source_url": src_url,
            "url": src_url,
            "auto_approved": bool(auto_approve),
            "failure_stage": failure_stage,
            "output_root": str(Path(out_root).resolve()),
            "run_output_dir": str(Path(paths.get("result_json", "")).parent) if paths.get("result_json") else "",
            **flat,
            "warnings": list(dict.fromkeys(warnings)),
            "blocking_reasons": list(dict.fromkeys(blocking)),
            "next_step": _next_step_for_result(
                ok=nk, status=st, auto_approved=bool(auto_approve), failure_stage=failure_stage
            ),
            "metadata": {
                "target_language": target_language,
                "duration_minutes": int(duration_minutes),
                "source_type": source_type,
                "asset_mode": asset_mode,
                "voice_mode": voice_mode,
                "motion_mode": motion_mode,
                "subtitle_style": subtitle_style,
                "subtitle_mode": subtitle_mode,
                "force": bool(force),
                "auto_approve": bool(auto_approve),
                "approval_note": (approval_note or "").strip() if auto_approve else "",
            },
            "steps": merged_steps,
            "paths": paths,
            "exit_code": int(exit_code),
            "created_at_epoch": int(time.time()),
        }
        if paths.get("result_json"):
            rp = Path(paths["result_json"])
            _write_json(rp, result)
            _write_url_to_final_open_me(run_dir=rp.parent, result=result)
        return result

    if not _validate_run_id(rid):
        root0 = Path(out_root).resolve()
        run_dir0 = root0 / f"url_to_final_video_{rid}"
        paths0: Dict[str, str] = {
            "result_json": str((run_dir0 / RESULT_FILENAME).resolve()),
            "url_script_dir": "",
            "generate_script_response": "",
            "scene_asset_pack": "",
            "real_local_preview_dir": "",
            "real_local_preview_result": "",
            "preview_with_subtitles": "",
            "local_preview_dir": "",
            "local_preview_result": "",
            "human_approval": "",
            "final_render_dir": "",
            "final_video": "",
            "final_render_result": "",
        }
        return _fail_early(
            ok_v=False,
            status="blocked",
            exit_code=EXIT_INVALID_INPUT,
            warnings=[
                "run_id must match ^[A-Za-z0-9_-]{1,80}$ and contain no path separators."
            ],
            blocking=["invalid_run_id"],
            paths=paths0,
            failure_stage=FAILURE_INPUT,
        )

    warnings: List[str] = []
    blocking: List[str] = []
    root = Path(out_root).resolve()
    run_dir = root / f"url_to_final_video_{rid}"
    run_dir.mkdir(parents=True, exist_ok=True)

    paths: Dict[str, str] = {
        "result_json": str((run_dir / RESULT_FILENAME).resolve()),
        "url_script_dir": "",
        "generate_script_response": "",
        "scene_asset_pack": "",
        "real_local_preview_dir": "",
        "real_local_preview_result": "",
        "preview_with_subtitles": "",
        "local_preview_dir": "",
        "local_preview_result": "",
        "human_approval": "",
        "final_render_dir": "",
        "final_video": "",
        "final_render_result": "",
    }

    try:
        bfn = bridge_fn or run_bridge
        bridge_res = bfn(
            url=url,
            run_id=rid,
            target_language=target_language,
            duration_minutes=int(duration_minutes),
            source_type=source_type,
            out_root=str(root),
            write_open_me=True,
        )
        if not isinstance(bridge_res, dict) or not bridge_res.get("ok"):
            blocking.extend(_list_str((bridge_res or {}).get("blocking_reasons")) or ["bridge_failed"])
            warnings.extend(_list_str((bridge_res or {}).get("warnings")))
            return _fail_early(
                ok_v=False,
                status="failed",
                exit_code=EXIT_FAILED,
                warnings=warnings,
                blocking=blocking,
                paths=paths,
                failure_stage=FAILURE_BRIDGE,
                bridge_res=bridge_res if isinstance(bridge_res, dict) else {"invalid_bridge_result": True},
            )

        paths["url_script_dir"] = _s(bridge_res.get("build_dir"))
        paths["generate_script_response"] = _s(bridge_res.get("generate_script_response_path"))

        pfn = preview_fn or run_real_local_preview
        preview_res = pfn(
            script_json_path=Path(paths["generate_script_response"]),
            run_id=rid,
            out_root=root,
            asset_mode=asset_mode,
            voice_mode=voice_mode,
            motion_mode=motion_mode,
            subtitle_style=subtitle_style,
            subtitle_mode=subtitle_mode,
            force=bool(force),
            write_open_me=True,
        )
        if not isinstance(preview_res, dict):
            preview_res = {
                "ok": False,
                "status": "failed",
                "blocking_reasons": ["preview_invalid_result"],
            }

        paths["real_local_preview_dir"] = _s(preview_res.get("build_dir"))
        pr_paths = preview_res.get("paths") if isinstance(preview_res.get("paths"), dict) else {}
        paths["scene_asset_pack"] = _s(pr_paths.get("scene_asset_pack"))
        paths["real_local_preview_result"] = (
            str(Path(paths["real_local_preview_dir"]) / "real_local_preview_result.json")
            if paths["real_local_preview_dir"]
            else ""
        )
        paths["preview_with_subtitles"] = _s(pr_paths.get("preview_with_subtitles"))
        warnings.extend(_list_str(preview_res.get("warnings")))
        blocking.extend(_list_str(preview_res.get("blocking_reasons")))

        prev_st = str(preview_res.get("status") or "").lower()
        if not preview_res.get("ok") or not paths["preview_with_subtitles"]:
            if not paths["preview_with_subtitles"]:
                blocking.append("preview_with_subtitles_missing")
            return _fail_early(
                ok_v=False,
                status="blocked" if prev_st == "blocked" else "failed",
                exit_code=EXIT_BLOCKED if prev_st == "blocked" else EXIT_FAILED,
                warnings=warnings,
                blocking=blocking,
                paths=paths,
                failure_stage=FAILURE_PREVIEW,
                bridge_res=bridge_res,
                preview_res=preview_res,
            )

        lp_paths = _ensure_local_preview_package_from_ba254(
            out_root=root,
            run_id=rid,
            preview_with_subtitles_path=paths["preview_with_subtitles"],
            real_local_preview_result_path=paths["real_local_preview_result"],
            warnings=warnings,
        )
        paths["local_preview_dir"] = lp_paths.get("local_preview_dir", "")
        paths["local_preview_result"] = lp_paths.get("local_preview_result", "")

        if not _s(lp_paths.get("local_preview_video")):
            blocking.append("local_preview_preview_video_missing")
            return _fail_early(
                ok_v=False,
                status="failed",
                exit_code=EXIT_FAILED,
                warnings=warnings,
                blocking=blocking,
                paths=paths,
                failure_stage=FAILURE_ADAPTER,
                bridge_res=bridge_res,
                preview_res=preview_res,
            )

        if auto_approve and paths["local_preview_dir"]:
            paths["human_approval"] = _write_human_approval(
                local_preview_dir=Path(paths["local_preview_dir"]),
                run_id=rid,
                note=approval_note,
                warnings=warnings,
            )
        else:
            paths["human_approval"] = ""
            warnings.append("ba25_6_human_approval_not_written_no_auto_approve")

        if not auto_approve:
            blocking = list(
                dict.fromkeys(blocking + ["human_approval_required_before_final_render"])
            )
            return _fail_early(
                ok_v=False,
                status="blocked",
                exit_code=EXIT_BLOCKED,
                warnings=warnings,
                blocking=blocking,
                paths=paths,
                failure_stage=FAILURE_APPROVAL_GATE,
                bridge_res=bridge_res,
                preview_res=preview_res,
            )

        ffn = final_render_fn or run_final_render_for_local_preview
        final_res = ffn(run_id=rid, out_root=root, force=bool(force))
        if not isinstance(final_res, dict):
            final_res = {"ok": False, "status": "failed", "blocking_reasons": ["final_render_invalid_result"]}

        fr_paths = final_res.get("paths") if isinstance(final_res.get("paths"), dict) else {}
        paths["final_render_dir"] = _s(fr_paths.get("final_render_dir"))
        paths["final_video"] = _s(fr_paths.get("final_video_path"))
        if paths["final_render_dir"]:
            paths["final_render_result"] = str(Path(paths["final_render_dir"]) / "final_render_result.json")

        warnings.extend(_list_str(final_res.get("warnings")))
        blocking.extend(_list_str(final_res.get("blocking_reasons")))

        fv = paths["final_video"]
        final_ok = bool(final_res.get("ok"))
        video_ok = _safe_nonempty_file(Path(fv)) if fv else False
        ok = final_ok and video_ok
        final_status = str(final_res.get("status") or "")
        status = _resolve_status_after_final(
            final_ok=final_ok, final_status=final_status, final_video=fv
        )
        if final_ok and not video_ok and final_status.lower() != "skipped_existing":
            ok = False
            blocking.append("final_video_missing_or_empty")
            status = "failed"
            if FAILURE_ADAPTER not in blocking:
                warnings.append("ba25_6_final_video_not_nonempty_after_render")

        exit_code = (
            EXIT_OK
            if ok
            else (
                EXIT_BLOCKED
                if str(status).lower() in ("locked", "blocked", "unknown")
                else EXIT_FAILED
            )
        )

        flat = _flatten_output_paths(paths=paths, scene_asset_pack_path=paths.get("scene_asset_pack", ""))
        result = {
            "schema_version": RESULT_SCHEMA,
            "ok": ok,
            "status": status,
            "run_id": rid,
            "source_url": src_url,
            "url": src_url,
            "auto_approved": True,
            "failure_stage": "" if ok else FAILURE_FINAL_RENDER,
            "output_root": str(root),
            "run_output_dir": str(run_dir.resolve()),
            **flat,
            "warnings": list(dict.fromkeys(warnings)),
            "blocking_reasons": list(dict.fromkeys(blocking)),
            "next_step": _next_step_for_result(
                ok=ok, status=status, auto_approved=True, failure_stage=""
            ),
            "metadata": {
                "target_language": target_language,
                "duration_minutes": int(duration_minutes),
                "source_type": source_type,
                "asset_mode": asset_mode,
                "voice_mode": voice_mode,
                "motion_mode": motion_mode,
                "subtitle_style": subtitle_style,
                "subtitle_mode": subtitle_mode,
                "force": bool(force),
                "auto_approve": True,
                "approval_note": (approval_note or "").strip(),
            },
            "steps": {
                "ba25_3_url_to_script": bridge_res,
                "ba25_4_real_local_preview": preview_res,
                "ba24_3_final_render": final_res,
            },
            "paths": paths,
            "exit_code": int(exit_code),
            "created_at_epoch": int(time.time()),
        }
        _write_json(Path(paths["result_json"]), result)
        _write_url_to_final_open_me(run_dir=run_dir, result=result)
        return result

    except Exception as e:
        msg = str(getattr(e, "message", "") or str(e) or "unknown error")
        if len(msg) > 500:
            msg = msg[:497] + "..."
        warnings_e = list(dict.fromkeys(warnings + [f"ba25_6_internal:{type(e).__name__}:{msg}"]))
        flat = _flatten_output_paths(paths=paths, scene_asset_pack_path=paths.get("scene_asset_pack", ""))
        result = {
            "schema_version": RESULT_SCHEMA,
            "ok": False,
            "status": "failed",
            "run_id": rid,
            "source_url": src_url,
            "url": src_url,
            "auto_approved": bool(auto_approve),
            "failure_stage": FAILURE_INTERNAL,
            "output_root": str(root),
            "run_output_dir": str(run_dir.resolve()),
            **flat,
            "warnings": warnings_e,
            "blocking_reasons": ["unexpected_internal_error"],
            "next_step": _next_step_for_result(
                ok=False,
                status="failed",
                auto_approved=bool(auto_approve),
                failure_stage=FAILURE_INTERNAL,
            ),
            "metadata": {
                "target_language": target_language,
                "duration_minutes": int(duration_minutes),
                "source_type": source_type,
                "asset_mode": asset_mode,
                "voice_mode": voice_mode,
                "motion_mode": motion_mode,
                "subtitle_style": subtitle_style,
                "subtitle_mode": subtitle_mode,
                "force": bool(force),
                "auto_approve": bool(auto_approve),
                "approval_note": (approval_note or "").strip() if auto_approve else "",
            },
            "steps": {},
            "paths": paths,
            "exit_code": EXIT_FAILED,
            "created_at_epoch": int(time.time()),
            "error": {"type": type(e).__name__, "message": msg},
        }
        _write_json(Path(paths["result_json"]), result)
        _write_url_to_final_open_me(run_dir=run_dir, result=result)
        return result


def _flatten_output_paths(*, paths: Dict[str, str], scene_asset_pack_path: str) -> Dict[str, str]:
    gen = _s(paths.get("generate_script_response"))
    return {
        "result_json_path": _s(paths.get("result_json")),
        "url_script_result_path": gen,
        "generate_script_response_path": gen,
        "scene_asset_pack_path": _s(scene_asset_pack_path),
        "real_local_preview_result_path": _s(paths.get("real_local_preview_result")),
        "preview_with_subtitles_path": _s(paths.get("preview_with_subtitles")),
        "local_preview_dir": _s(paths.get("local_preview_dir")),
        "human_approval_path": _s(paths.get("human_approval")),
        "final_render_result_path": _s(paths.get("final_render_result")),
        "final_video_path": _s(paths.get("final_video")),
    }


def _build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description=(
            "BA 25.5/25.6 — URL-to-Final-Video Smoke (lokal): URL → generate_script_response.json → "
            "preview_with_subtitles.mp4 → final_video.mp4. Kein Publishing/Upload."
        )
    )
    p.add_argument("--url", required=True, dest="url")
    p.add_argument("--run-id", default="", dest="run_id")
    p.add_argument("--out-dir", default="output", dest="out_dir")
    p.add_argument("--target-language", default="de", dest="target_language")
    p.add_argument("--duration-minutes", type=int, default=3, dest="duration_minutes")
    p.add_argument("--source-type", choices=("auto", "article", "youtube"), default="auto", dest="source_type")
    p.add_argument("--asset-mode", choices=("placeholder", "live"), default="placeholder", dest="asset_mode")
    p.add_argument("--voice-mode", choices=("smoke",), default="smoke", dest="voice_mode")
    p.add_argument("--motion-mode", choices=("static", "basic"), default="static", dest="motion_mode")
    p.add_argument(
        "--subtitle-style",
        choices=("classic", "word_by_word", "typewriter", "karaoke", "none"),
        default="typewriter",
        dest="subtitle_style",
    )
    p.add_argument("--subtitle-mode", choices=("none", "simple"), default="simple", dest="subtitle_mode")
    p.add_argument(
        "--force",
        action="store_true",
        dest="force",
        help="Weitergabe an BA 25.4/24.3 (z. B. bestehendes final_video mit --force neu kopieren).",
    )
    p.add_argument(
        "--no-auto-approve",
        action="store_true",
        dest="no_auto_approve",
        help=(
            "Kein automatisches human_approval.json; Final Render wird nicht gestartet (Status blocked). "
            "Standard (ohne dieses Flag): Smoke/Dev Auto-Approve, damit der End-to-End-Smoke lokal durchläuft."
        ),
    )
    p.add_argument(
        "--approval-note",
        default="",
        dest="approval_note",
        help="Optionaler Text in human_approval.json bei Auto-Approve (Smoke/Dev).",
    )
    p.add_argument("--print-json", action="store_true", dest="print_json")
    return p


def main(argv: Optional[Sequence[str]] = None) -> int:
    try:
        args = _build_arg_parser().parse_args(argv)
    except SystemExit:
        raise

    try:
        res = run_url_to_final_video_smoke(
            url=args.url,
            run_id=args.run_id,
            out_root=Path(args.out_dir),
            target_language=args.target_language,
            duration_minutes=int(args.duration_minutes),
            source_type=args.source_type,
            asset_mode=args.asset_mode,
            voice_mode=args.voice_mode,
            motion_mode=args.motion_mode,
            subtitle_style=args.subtitle_style,
            subtitle_mode=args.subtitle_mode,
            force=bool(args.force),
            auto_approve=not bool(args.no_auto_approve),
            approval_note=args.approval_note or DEFAULT_APPROVAL_NOTE,
        )
    except Exception as e:
        msg = str(getattr(e, "message", "") or str(e) or "unknown error")
        if len(msg) > 500:
            msg = msg[:497] + "..."
        err = {
            "schema_version": RESULT_SCHEMA,
            "ok": False,
            "status": "failed",
            "run_id": _s(getattr(args, "run_id", "")),
            "source_url": _s(getattr(args, "url", "")),
            "failure_stage": FAILURE_INTERNAL,
            "error": {"type": type(e).__name__, "message": msg},
            "warnings": [f"ba25_6_cli_unhandled:{type(e).__name__}"],
            "blocking_reasons": ["unexpected_exception"],
            "next_step": "Erneut versuchen; bei Reproduzierbarkeit Issue mit Kontext (ohne Secrets) melden.",
        }
        if getattr(args, "print_json", False):
            print(json.dumps(err, ensure_ascii=False, indent=2))
        else:
            print(json.dumps({"ok": False, "status": "failed", "error": err["error"]}, ensure_ascii=False, indent=2))
        return EXIT_FAILED

    code = int(res.get("exit_code", EXIT_FAILED))
    printable = {k: v for k, v in res.items() if k != "exit_code"}
    if args.print_json:
        print(json.dumps(printable, ensure_ascii=False, indent=2))
    else:
        compact = {
            "ok": printable.get("ok"),
            "status": printable.get("status"),
            "run_id": printable.get("run_id"),
            "auto_approved": printable.get("auto_approved"),
            "final_video_path": printable.get("final_video_path", ""),
            "result_json_path": printable.get("result_json_path", ""),
            "blocking_reasons": printable.get("blocking_reasons", []),
        }
        if not printable.get("ok"):
            compact["warnings"] = printable.get("warnings", [])
            compact["failure_stage"] = printable.get("failure_stage", "")
            compact["next_step"] = printable.get("next_step", "")
        print(json.dumps(compact, ensure_ascii=False, indent=2))
    return code


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
