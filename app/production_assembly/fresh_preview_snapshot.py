"""BA 30.3/30.4 — Read-only snapshot + readiness gate for Fresh Topic Preview Smoke (Founder Dashboard)."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

_FRESH_PREVIEW_SNAPSHOT_VERSION = "ba31_0_v1"
_OPERATOR_REVIEW_VERSION = "ba31_0_v1"
_SUMMARY_READ_MAX_BYTES = 512_000
_READ_JSON_MAX_BYTES = 512_000


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _resolve_output_root(output_root: Union[str, Path]) -> Path:
    p = Path(output_root)
    if not p.is_absolute():
        p = _repo_root() / p
    return p.resolve()


def _safe_is_file(path: Path) -> bool:
    try:
        return path.is_file() and not path.is_symlink()
    except OSError:
        return False


def _safe_is_dir(path: Path) -> bool:
    try:
        return path.is_dir() and not path.is_symlink()
    except OSError:
        return False


def _list_run_dirs(fresh_base: Path) -> List[Path]:
    out: List[Path] = []
    try:
        for child in fresh_base.iterdir():
            try:
                if child.name.startswith("."):
                    continue
                if _safe_is_dir(child):
                    out.append(child)
            except OSError:
                continue
    except OSError:
        return []
    return out


def _dir_mtime(p: Path) -> float:
    try:
        return float(p.stat().st_mtime)
    except OSError:
        return 0.0


def _read_json_capped(path: Path, *, max_bytes: int = _READ_JSON_MAX_BYTES) -> Optional[Dict[str, Any]]:
    if not _safe_is_file(path):
        return None
    try:
        sz = path.stat().st_size
        if sz > max_bytes:
            return None
        raw = path.read_text(encoding="utf-8")
        doc = json.loads(raw)
        return doc if isinstance(doc, dict) else None
    except (OSError, json.JSONDecodeError, TypeError, ValueError):
        return None


def evaluate_fresh_preview_readiness(snapshot: Dict[str, Any]) -> Dict[str, Any]:
    """
    BA 30.4 — Additive readiness from an existing snapshot dict (paths + presence flags).
    Returns keys to merge: readiness_status, readiness_score, readiness_reasons, blocking_reasons, operator_next_step.
    """
    rb: List[str] = []
    rr: List[str] = []
    status = "ready"
    score = 100

    avail = bool(snapshot.get("fresh_preview_available"))
    if not avail:
        rb.append("fresh_preview_not_available")
        status = "blocked"
        score = 0
        return {
            "readiness_status": status,
            "readiness_score": score,
            "readiness_reasons": rr,
            "blocking_reasons": rb,
            "operator_next_step": snapshot.get("operator_next_step")
            or (
                "Fresh Preview Smoke starten: "
                "python scripts/run_fresh_topic_preview_smoke.py --run-id <id> --output-root output --topic \"…\""
            ),
        }

    sp = str(snapshot.get("script_path") or "").strip()
    pp = str(snapshot.get("scene_asset_pack_path") or "").strip()
    ap = str(snapshot.get("asset_manifest_path") or "").strip()

    if not snapshot.get("script_json_present"):
        rb.append("missing_script_json")
    elif sp:
        sdoc = _read_json_capped(Path(sp))
        if sdoc is None:
            rb.append("script_json_invalid_or_too_large")
        else:
            has_body = bool(
                (str(sdoc.get("title") or "").strip())
                or (str(sdoc.get("hook") or "").strip())
                or (str(sdoc.get("full_script") or "").strip())
                or (isinstance(sdoc.get("chapters"), list) and len(sdoc.get("chapters") or []) > 0)
            )
            if not has_body:
                rb.append("script_missing_usable_content")

    if not snapshot.get("scene_asset_pack_present"):
        rb.append("missing_scene_asset_pack")
    elif pp:
        pdoc = _read_json_capped(Path(pp))
        if pdoc is None:
            rb.append("scene_asset_pack_invalid_or_too_large")
        else:
            se = pdoc.get("scene_expansion")
            beats = se.get("expanded_scene_assets") if isinstance(se, dict) else None
            if not isinstance(beats, list) or not beats:
                rb.append("scene_asset_pack_missing_scenes")

    if not snapshot.get("asset_manifest_present"):
        rb.append("missing_asset_manifest")
    elif ap:
        adoc = _read_json_capped(Path(ap))
        if adoc is None:
            rb.append("asset_manifest_invalid_or_too_large")
        else:
            assets = adoc.get("assets")
            if not isinstance(assets, list) or not assets:
                rr.append("manifest_assets_empty")
            elif _manifest_assets_look_placeholder_only(assets):
                rr.append("manifest_assets_look_placeholder_only")

    if rb:
        status = "blocked"
        score = max(0, min(35, 28 - 4 * max(0, len(rb) - 1)))
        next_step = (
            "Pflichtartefakte vervollständigen oder Fresh-Smoke erneut ausführen. "
            "Siehe blocking_reasons im Snapshot."
        )
        return {
            "readiness_status": status,
            "readiness_score": score,
            "readiness_reasons": rr,
            "blocking_reasons": rb,
            "operator_next_step": next_step,
        }

    if not snapshot.get("preview_smoke_summary_present"):
        rr.append("missing_preview_smoke_auto_summary")
    else:
        summ_p = str(snapshot.get("preview_smoke_summary_path") or "").strip()
        if summ_p:
            sdoc = _read_json_capped(Path(summ_p))
            if sdoc is None:
                rr.append("preview_smoke_summary_unparseable")
            elif sdoc.get("ok") is not True:
                rr.append("preview_smoke_summary_ok_false")

    if not snapshot.get("open_preview_smoke_report_present"):
        rr.append("missing_open_preview_smoke_md")

    if rr:
        status = "warning"
        score = max(40, min(78, 72 - 6 * len(rr)))

    if status == "ready":
        score = min(100, 95)

    if status == "blocked":
        next_step = snapshot.get("operator_next_step") or "Run prüfen und blocking_reasons abarbeiten."
    elif status == "warning":
        next_step = (
            "Vorschau-Pipeline vervollständigen (ohne --dry-run), OPEN_PREVIEW_SMOKE.md und Summary prüfen. "
            "Bei nur-Placeholder-Assets optional --allow-live-assets nur mit Keys."
        )
    else:
        next_step = (
            snapshot.get("operator_next_step")
            or "OPEN_PREVIEW_SMOKE.md und MP4 prüfen; bei Bedarf Human Preview Review (patch_human_preview_review.py)."
        )

    return {
        "readiness_status": status,
        "readiness_score": int(score),
        "readiness_reasons": rr,
        "blocking_reasons": rb,
        "operator_next_step": next_step,
    }


def _manifest_assets_look_placeholder_only(assets: List[Any]) -> bool:
    if not assets:
        return False
    http_re = re.compile(r"https?://", re.I)
    for a in assets:
        if not isinstance(a, dict):
            continue
        for key in ("selected_asset_path", "image_path", "generated_image_path", "video_path", "clip_path"):
            raw = str(a.get(key) or "").strip()
            if http_re.search(raw):
                return False
            if raw.lower().endswith(".mp4") and not raw.lower().endswith("_placeholder.mp4"):
                if "placeholder" not in raw.lower():
                    return False
    return True


def _blocking_reason_label(code: str) -> str:
    m = {
        "fresh_preview_not_available": "Kein Fresh-Preview-Run unter output/fresh_topic_preview.",
        "missing_script_json": "Pflicht: script.json fehlt oder ist nicht lesbar.",
        "script_json_invalid_or_too_large": "script.json ungültig oder zu groß.",
        "script_missing_usable_content": "Skript ohne nutzbaren Text/Kapitel.",
        "missing_scene_asset_pack": "Pflicht: scene_asset_pack.json fehlt.",
        "scene_asset_pack_invalid_or_too_large": "scene_asset_pack.json ungültig oder zu groß.",
        "scene_asset_pack_missing_scenes": "scene_asset_pack ohne Szenen.",
        "missing_asset_manifest": "Pflicht: asset_manifest.json fehlt.",
        "asset_manifest_invalid_or_too_large": "asset_manifest.json ungültig oder zu groß.",
    }
    return m.get(code, code)


def _readiness_reason_label(code: str) -> str:
    m = {
        "manifest_assets_empty": "Manifest ohne Asset-Einträge.",
        "manifest_assets_look_placeholder_only": "Manifest wirkt nur Placeholder — ggf. Live-Assets oder erneuter Lauf.",
        "missing_preview_smoke_auto_summary": "preview_smoke_auto_summary_<run>.json fehlt (Full Preview noch nicht oder fehlgeschlagen).",
        "preview_smoke_summary_unparseable": "Preview-Summary JSON nicht lesbar.",
        "preview_smoke_summary_ok_false": "Preview-Summary meldet ok=false.",
        "missing_open_preview_smoke_md": "OPEN_PREVIEW_SMOKE.md fehlt oder Pfad unbekannt.",
    }
    return m.get(code, code)


def evaluate_operator_review(snapshot: Dict[str, Any]) -> Dict[str, Any]:
    """
    BA 31.0 — Read-only Review-Empfehlung (keine Persistenz, keine Freigabe).

    Entscheidung: approve | rework | blocked | pending
    """
    avail = bool(snapshot.get("fresh_preview_available"))
    rs = str(snapshot.get("readiness_status") or "").lower()
    rb = [str(x) for x in (snapshot.get("blocking_reasons") or [])]
    rr = [str(x) for x in (snapshot.get("readiness_reasons") or [])]

    summ_present = bool(snapshot.get("preview_smoke_summary_present"))
    open_present = bool(snapshot.get("open_preview_smoke_report_present"))
    am_present = bool(snapshot.get("asset_manifest_present"))

    summary_ok: Optional[bool] = None
    sp = str(snapshot.get("preview_smoke_summary_path") or "").strip()
    if summ_present and sp:
        doc = _read_json_capped(Path(sp))
        if doc is not None:
            if doc.get("ok") is True:
                summary_ok = True
            elif doc.get("ok") is False:
                summary_ok = False

    full_preview_available = summ_present or open_present

    reasons_out: List[str] = []

    def add_reason(msg: str) -> None:
        if msg and msg not in reasons_out:
            reasons_out.append(msg)

    base_out = {
        "review_decision": "pending",
        "review_decision_label": "Ausstehend",
        "review_decision_reasons": reasons_out,
        "review_next_action": "Full Preview Smoke lokal über CLI-Handoff starten",
        "full_preview_available": full_preview_available,
        "preview_smoke_summary_ok": summary_ok,
        "operator_review_version": _OPERATOR_REVIEW_VERSION,
    }

    if not avail:
        add_reason("Kein Fresh-Preview-Run unter output/fresh_topic_preview.")
        return base_out

    if rb or rs == "blocked":
        decision = "blocked"
        label = "Blockiert"
        for code in rb[:16]:
            add_reason(_blocking_reason_label(code))
        next_action = "Blocker beheben, bevor weiter produziert wird"
        if summ_present and summary_ok is False:
            add_reason("Preview-Summary meldet ok=false.")
        return {
            **base_out,
            "review_decision": decision,
            "review_decision_label": label,
            "review_decision_reasons": reasons_out,
            "review_next_action": next_action,
            "full_preview_available": full_preview_available,
            "preview_smoke_summary_ok": summary_ok,
        }

    if summ_present and summary_ok is False:
        add_reason("Preview-Summary meldet ok=false — Smoke nicht erfolgreich.")
        return {
            **base_out,
            "review_decision": "blocked",
            "review_decision_label": "Blockiert",
            "review_decision_reasons": reasons_out,
            "review_next_action": "Blocker beheben, bevor weiter produziert wird",
            "preview_smoke_summary_ok": False,
        }

    if am_present and not summ_present and not open_present:
        add_reason("Dry-Run/Manifest vorhanden — Full Preview Smoke (ohne --dry-run) noch nicht gelaufen.")
        return {
            **base_out,
            "review_decision": "pending",
            "review_decision_label": "Ausstehend",
            "review_decision_reasons": reasons_out,
            "review_next_action": "Full Preview Smoke lokal über CLI-Handoff starten",
            "full_preview_available": False,
            "preview_smoke_summary_ok": summary_ok,
        }

    if rs == "ready" and summ_present and open_present and summary_ok is True and not rb:
        add_reason("Readiness ready, Summary ok, OPEN_PREVIEW vorhanden.")
        return {
            **base_out,
            "review_decision": "approve",
            "review_decision_label": "Freigabe (Review)",
            "review_decision_reasons": reasons_out,
            "review_next_action": "Preview visuell prüfen und finalen Render vorbereiten",
            "full_preview_available": True,
            "preview_smoke_summary_ok": True,
        }

    if rs == "warning" or rr:
        for code in rr[:16]:
            add_reason(_readiness_reason_label(code))
        return {
            **base_out,
            "review_decision": "rework",
            "review_decision_label": "Nacharbeit",
            "review_decision_reasons": reasons_out,
            "review_next_action": "Prompt/Assets prüfen und Full Preview erneut starten",
            "preview_smoke_summary_ok": summary_ok,
        }

    if rs == "ready":
        add_reason("Ready, aber Summary ok nicht eindeutig true oder Artefakte noch zu prüfen.")
        return {
            **base_out,
            "review_decision": "rework",
            "review_decision_label": "Nacharbeit",
            "review_decision_reasons": reasons_out,
            "review_next_action": "Prompt/Assets prüfen und Full Preview erneut starten",
            "preview_smoke_summary_ok": summary_ok,
        }

    add_reason("Snapshot auswerten — ggf. Full Preview starten.")
    return base_out


_GUIDED_FLOW_VERSION = "ba31_1b_v1"

# BA 31.1b — Microcopy (Snapshot-Schritt + Dry-Run → Full Preview)
_GUIDED_SNAPSHOT_REFRESH_HINT = (
    "Klicke auf „Fresh Preview aktualisieren“, damit das Dashboard den neuesten Run, "
    "Artefakte und Readiness neu einliest."
)
_GUIDED_PENDING_FULL_PREVIEW_HINT = (
    "Der Dry-Run ist vorhanden. Für OPEN_PREVIEW_SMOKE.md und Review musst du jetzt "
    "den Full Preview Smoke über den CLI-Handoff starten. "
    "Kopiere unten den Full-Preview-CLI-Befehl, führe ihn lokal im Repo aus und "
    "klicke danach auf „Fresh Preview aktualisieren“."
)


def build_guided_production_flow(snapshot: Dict[str, Any]) -> Dict[str, Any]:
    """
    BA 31.1 / 31.1b — Read-only geführter Produktionsflug aus Snapshot-Feldern (keine Persistenz).
    """
    avail = bool(snapshot.get("fresh_preview_available"))
    rid = str(snapshot.get("latest_run_id") or "").strip()
    has_run = avail or bool(rid)

    script_ok = bool(snapshot.get("script_json_present"))
    pack_ok = bool(snapshot.get("scene_asset_pack_present"))
    manifest_ok = bool(snapshot.get("asset_manifest_present"))
    core_ok = script_ok and pack_ok and manifest_ok

    summ_ok_flag = bool(snapshot.get("preview_smoke_summary_present"))
    open_ok_flag = bool(snapshot.get("open_preview_smoke_report_present"))
    full_preview_done = summ_ok_flag or open_ok_flag

    warns = snapshot.get("warnings")
    has_warnings = isinstance(warns, list) and len(warns) > 0

    rs = str(snapshot.get("readiness_status") or "").lower()
    rb = [str(x) for x in (snapshot.get("blocking_reasons") or [])]
    rd = str(snapshot.get("review_decision") or "pending").lower()

    # --- step: input
    if has_run:
        st_input = "done"
    else:
        st_input = "pending"

    # --- step: dry_run
    if not has_run:
        st_dry = "pending"
    elif core_ok:
        st_dry = "done"
    else:
        st_dry = "blocked"

    # --- step: snapshot (scan result)
    if not avail:
        st_snap = "pending"
    elif has_warnings:
        st_snap = "warning"
    else:
        st_snap = "done"

    # --- step: full_preview (blocked nur bei fehlenden Kernartefakten)
    if not has_run:
        st_full = "pending"
    elif not core_ok:
        st_full = "blocked"
    elif full_preview_done:
        st_full = "done"
    else:
        st_full = "pending"

    # --- step: review
    if rd == "approve":
        st_rev = "done"
    elif rd == "rework":
        st_rev = "warning"
    elif rd == "blocked":
        st_rev = "blocked"
    else:
        st_rev = "pending"

    # --- step: final_render
    if rd == "approve":
        st_final = "pending"
    else:
        st_final = "locked"

    steps: List[Dict[str, Any]] = [
        {"id": "input", "order": 1, "label": "Input", "status": st_input},
        {"id": "dry_run", "order": 2, "label": "Dry-Run", "status": st_dry},
        {
            "id": "snapshot",
            "order": 3,
            "label": "Snapshot",
            "status": st_snap,
            "detail": _GUIDED_SNAPSHOT_REFRESH_HINT,
        },
        {"id": "full_preview", "order": 4, "label": "Full Preview", "status": st_full},
        {"id": "review", "order": 5, "label": "Review", "status": st_rev},
        {"id": "final_render", "order": 6, "label": "Final Render", "status": st_final},
    ]

    next_label = "Nächster Schritt"
    next_action = "Fresh Preview Dry-Run starten"

    if not has_run:
        next_label = "Dry-Run"
        next_action = "Fresh Preview Dry-Run starten"
    elif rb or (rs == "blocked" and not core_ok):
        next_label = "Blocker"
        next_action = "Dry-Run erneut starten oder Blocker prüfen"
    elif rd == "blocked":
        next_label = "Review"
        next_action = "Blocker beheben, bevor weiter produziert wird"
    elif rd == "rework":
        next_label = "Review"
        next_action = "Artefakte prüfen, Prompt/Assets anpassen und Full Preview erneut starten"
    elif rd == "pending":
        next_label = "Full Preview"
        next_action = _GUIDED_PENDING_FULL_PREVIEW_HINT
    elif rd == "approve":
        next_label = "Final Render"
        next_action = "Final Render vorbereiten"
    else:
        next_action = _GUIDED_SNAPSHOT_REFRESH_HINT

    current = "input"
    order_ids = ["input", "dry_run", "snapshot", "full_preview", "review", "final_render"]
    by_id = {s["id"]: s for s in steps}
    for sid in order_ids:
        st = str(by_id[sid]["status"])
        if st == "done":
            continue
        if sid == "final_render" and st == "locked":
            current = "review"
            break
        current = sid
        break
    else:
        current = "final_render"

    # Snapshot kann nur „warning“ sein (Scan-Warnungen); fokus dann auf den nächsten echten Schritt
    if (
        current == "snapshot"
        and str(by_id["snapshot"]["status"]) == "warning"
        and str(by_id["full_preview"]["status"]) == "pending"
    ):
        current = "full_preview"

    return {
        "guided_flow_version": _GUIDED_FLOW_VERSION,
        "guided_flow_steps": steps,
        "guided_flow_next_step_label": next_label,
        "guided_flow_next_step_action": next_action,
        "guided_flow_current_step": current,
    }


def _merge_readiness(base: Dict[str, Any]) -> Dict[str, Any]:
    r = evaluate_fresh_preview_readiness(base)
    out = dict(base)
    out.update(r)
    out.update(evaluate_operator_review(out))
    out.update(build_guided_production_flow(out))
    return out


def build_latest_fresh_preview_snapshot(output_root: Union[str, Path] = "output") -> Dict[str, Any]:
    """
    Scan ``<output_root>/fresh_topic_preview/<run_id>/`` for the newest run (by directory mtime).
    BA 30.4: merged ``evaluate_fresh_preview_readiness`` (additive gate fields).
    """
    warnings: List[str] = []
    empty_paths: Dict[str, str] = {
        "latest_run_id": "",
        "latest_run_dir": "",
        "script_path": "",
        "scene_asset_pack_path": "",
        "asset_manifest_path": "",
        "preview_smoke_summary_path": "",
        "open_preview_smoke_report_path": "",
        "operator_next_step": (
            "Fresh Preview Smoke starten: "
            "python scripts/run_fresh_topic_preview_smoke.py --run-id <id> --output-root output --topic \"…\""
        ),
    }

    try:
        root = _resolve_output_root(output_root)
    except OSError as e:
        return _merge_readiness(
            {
                "ok": False,
                "fresh_preview_snapshot_version": _FRESH_PREVIEW_SNAPSHOT_VERSION,
                "fresh_preview_available": False,
                **empty_paths,
                "script_json_present": False,
                "scene_asset_pack_present": False,
                "asset_manifest_present": False,
                "preview_smoke_summary_present": False,
                "open_preview_smoke_report_present": False,
                "warnings": [f"output_root_resolve_failed:{type(e).__name__}"],
            }
        )

    fresh_base = root / "fresh_topic_preview"
    if not _safe_is_dir(fresh_base):
        return _merge_readiness(
            {
                "ok": True,
                "fresh_preview_snapshot_version": _FRESH_PREVIEW_SNAPSHOT_VERSION,
                "fresh_preview_available": False,
                **empty_paths,
                "script_json_present": False,
                "scene_asset_pack_present": False,
                "asset_manifest_present": False,
                "preview_smoke_summary_present": False,
                "open_preview_smoke_report_present": False,
                "warnings": ["fresh_topic_preview_dir_absent"],
            }
        )

    candidates = _list_run_dirs(fresh_base)
    if not candidates:
        return _merge_readiness(
            {
                "ok": True,
                "fresh_preview_snapshot_version": _FRESH_PREVIEW_SNAPSHOT_VERSION,
                "fresh_preview_available": False,
                **empty_paths,
                "script_json_present": False,
                "scene_asset_pack_present": False,
                "asset_manifest_present": False,
                "preview_smoke_summary_present": False,
                "open_preview_smoke_report_present": False,
                "warnings": ["no_fresh_run_directories"],
            }
        )

    candidates.sort(key=_dir_mtime, reverse=True)
    run_dir = candidates[0]
    run_id = run_dir.name

    script_path = run_dir / "script.json"
    pack_path = run_dir / "scene_asset_pack.json"
    gen_dir = run_dir / f"generated_assets_{run_id}"
    am_path = gen_dir / "asset_manifest.json"
    summ_path = root / f"preview_smoke_auto_summary_{run_id}.json"
    open_default = root / ".preview_smoke_work" / run_id / "OPEN_PREVIEW_SMOKE.md"

    script_ok = _safe_is_file(script_path)
    pack_ok = _safe_is_file(pack_path)
    am_ok = _safe_is_file(am_path)
    summ_ok = _safe_is_file(summ_path)

    open_path_str = ""
    if summ_ok:
        try:
            sz = summ_path.stat().st_size
            if sz <= _SUMMARY_READ_MAX_BYTES:
                raw = summ_path.read_text(encoding="utf-8")
                doc = json.loads(raw)
                op = doc.get("open_preview_smoke_report_path")
                if op:
                    op_p = Path(str(op))
                    if _safe_is_file(op_p):
                        open_path_str = str(op_p.resolve())
        except (OSError, json.JSONDecodeError, TypeError, ValueError):
            warnings.append("preview_smoke_summary_parse_skipped")

    if not open_path_str and _safe_is_file(open_default):
        open_path_str = str(open_default.resolve())

    if not script_ok:
        warnings.append("missing_script_json")
    if not pack_ok:
        warnings.append("missing_scene_asset_pack")
    if not am_ok:
        warnings.append("missing_asset_manifest")
    if not summ_ok:
        warnings.append("missing_preview_smoke_auto_summary")
    open_present = bool(open_path_str)
    if not open_present:
        warnings.append("missing_open_preview_smoke_md")

    if am_ok and open_present:
        next_step = (
            "Lokale OPEN_PREVIEW_SMOKE.md öffnen, MP4 prüfen, bei Bedarf Human Preview Review setzen "
            "(scripts/patch_human_preview_review.py)."
        )
    elif am_ok and summ_ok:
        next_step = (
            "Preview-Summary vorhanden; OPEN_PREVIEW_SMOKE.md fehlt ggf. (nur --dry-run?). "
            "Erneut ohne --dry-run ausführen oder Report-Pfad im Summary prüfen."
        )
    elif am_ok:
        next_step = "Asset-Manifest vorhanden; vollständigen Preview-Smoke ausführen (ohne --dry-run), um Summary und Open-Me zu erhalten."
    else:
        next_step = (
            "Run-Ordner unvollständig. Fresh-Smoke erneut starten oder Asset-Runner-Fehler im Terminal prüfen."
        )

    base = {
        "ok": True,
        "fresh_preview_snapshot_version": _FRESH_PREVIEW_SNAPSHOT_VERSION,
        "fresh_preview_available": True,
        "latest_run_id": run_id,
        "latest_run_dir": str(run_dir.resolve()),
        "script_path": str(script_path.resolve()) if script_ok else "",
        "scene_asset_pack_path": str(pack_path.resolve()) if pack_ok else "",
        "asset_manifest_path": str(am_path.resolve()) if am_ok else "",
        "preview_smoke_summary_path": str(summ_path.resolve()) if summ_ok else "",
        "open_preview_smoke_report_path": open_path_str,
        "operator_next_step": next_step,
        "script_json_present": script_ok,
        "scene_asset_pack_present": pack_ok,
        "asset_manifest_present": am_ok,
        "preview_smoke_summary_present": summ_ok,
        "open_preview_smoke_report_present": open_present,
        "warnings": warnings,
    }
    return _merge_readiness(base)
