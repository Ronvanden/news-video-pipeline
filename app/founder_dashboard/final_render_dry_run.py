"""BA 24.2 — Final Render Dry-Run (read-only).

Berechnet Final-Render-Readiness für einen Local-Preview-Run und baut einen
`final_render_result` Contract — ohne Render, ohne ffmpeg, ohne Provider-Calls.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from app.founder_dashboard.local_preview_panel import (
    build_cost_card_from_saved_result,
    load_local_preview_human_approval,
    load_local_preview_saved_result,
    local_preview_safe_resolve_run_dir,
    validate_local_preview_run_id,
)
from scripts.final_render_contract import (
    apply_final_render_result_contract,
    build_final_render_result_contract,
)


def _safe_file_exists_nonempty(p: Path) -> bool:
    try:
        if p.is_symlink() or not p.is_file():
            return False
        return int(p.stat().st_size) > 0
    except OSError:
        return False


def _pick_preview_path(run_dir: Path) -> str:
    for name in ("preview_with_subtitles.mp4", "preview_video.mp4", "clean_video.mp4"):
        p = run_dir / name
        if _safe_file_exists_nonempty(p):
            return str(p)
    return ""


def _gate_state_pass_fail_unknown(ok: Optional[bool]) -> str:
    if ok is None:
        return "unknown"
    return "pass" if ok else "fail"


def build_final_render_dry_run_for_local_preview(
    *,
    run_id: str,
    out_root: Optional[Path] = None,
) -> Dict[str, Any]:
    """
    Return:
      ok: bool  (true sobald berechnet; false nur bei invalid/missing)
      status: ready|locked|blocked|unknown
      contract: final_render_result contract dict
      paths: input/output pfade (nur geplant, nichts wird geschrieben)
    """
    rid = (run_id or "").strip()
    if not validate_local_preview_run_id(rid):
        return {"ok": False, "run_id": rid, "status": "unknown", "message": "invalid run_id"}

    root = Path(out_root) if out_root is not None else (Path(__file__).resolve().parents[2] / "output")
    run_dir = local_preview_safe_resolve_run_dir(root, rid)
    if run_dir is None:
        return {"ok": False, "run_id": rid, "status": "unknown", "message": "run not found"}

    preview_path = _pick_preview_path(run_dir)
    saved = load_local_preview_saved_result(run_dir)
    approval = load_local_preview_human_approval(run_dir)
    cost_card = build_cost_card_from_saved_result(saved)

    gates: Dict[str, str] = {
        "preview_available": "fail" if not preview_path else "pass",
        "quality_not_fail": "unknown",
        "founder_not_block": "unknown",
        "human_approved": "fail",
        "cost_not_over_budget": "pass",
    }
    reasons: List[str] = []
    warnings: List[str] = []
    blocking: List[str] = []

    # quality_not_fail
    qc = saved.get("quality_checklist") if isinstance(saved, dict) else None
    qst = str(qc.get("status") or "").strip().lower() if isinstance(qc, dict) else ""
    if not qst:
        gates["quality_not_fail"] = "unknown"
    elif qst == "fail":
        gates["quality_not_fail"] = "fail"
    else:
        gates["quality_not_fail"] = "pass"

    # founder_not_block
    fq = saved.get("founder_quality_decision") if isinstance(saved, dict) else None
    dec = str(fq.get("decision_code") or "").strip().upper() if isinstance(fq, dict) else ""
    if not dec:
        gates["founder_not_block"] = "unknown"
    elif dec == "BLOCK":
        gates["founder_not_block"] = "fail"
    else:
        gates["founder_not_block"] = "pass"

    # human_approved
    apst = str(approval.get("status") or "").strip().lower() if isinstance(approval, dict) else ""
    gates["human_approved"] = "pass" if apst == "approved" else "fail"

    # cost_not_over_budget
    cst = str(cost_card.get("status") or "UNKNOWN").strip().upper() if isinstance(cost_card, dict) else "UNKNOWN"
    if cst == "OVER_BUDGET":
        gates["cost_not_over_budget"] = "fail"
    else:
        gates["cost_not_over_budget"] = "pass"
        if cst in ("UNKNOWN",):
            warnings.append("Cost status unknown; review recommended.")

    # overall status
    hard_block = (
        gates["preview_available"] == "fail"
        or gates["quality_not_fail"] == "fail"
        or gates["founder_not_block"] == "fail"
    )
    if hard_block:
        status = "blocked"
        if gates["preview_available"] == "fail":
            blocking.append("missing_preview")
            reasons.append("Fehlende Preview-Datei.")
        if gates["quality_not_fail"] == "fail":
            blocking.append("quality_fail")
            reasons.append("Quality FAIL.")
        if gates["founder_not_block"] == "fail":
            blocking.append("founder_block")
            reasons.append("Founder Decision BLOCK.")
    else:
        # locks (approval/cost)
        if gates["human_approved"] == "fail" or gates["cost_not_over_budget"] == "fail":
            status = "locked"
            if gates["human_approved"] == "fail":
                warnings.append("Human approval missing/not approved.")
                reasons.append("Human Approval nicht approved.")
            if gates["cost_not_over_budget"] == "fail":
                warnings.append("Cost is over budget; review required.")
                reasons.append("Cost OVER_BUDGET.")
        else:
            # unknown if too little signal?
            if gates["quality_not_fail"] == "unknown" and gates["founder_not_block"] == "unknown":
                status = "unknown"
                warnings.append("Contract/Quality signals missing; readiness unknown.")
                reasons.append("Zu wenige Signale (kein Contract/Quality) — Readiness unbekannt.")
            else:
                status = "ready"
                reasons.append("Dry-Run ready (no execution in BA 24.2).")

    message = {
        "ready": "Final Render wäre bereit (Dry-Run, keine Ausführung).",
        "locked": "Final Render gesperrt (Review/Approval nötig).",
        "blocked": "Final Render blockiert (harte Gate-Fails).",
        "unknown": "Final Render Readiness unbekannt.",
    }.get(status, "Final Render Dry-Run.")

    final_render_dir = root / f"final_render_{rid}"
    contract_status = "ready" if status == "ready" else ("locked" if status == "locked" else "blocked")
    contract = build_final_render_result_contract(
        run_id=rid,
        source_preview_package_dir=run_dir,
        output_dir=final_render_dir,
        status=contract_status,
        input_preview_path=preview_path or None,
        local_preview_result_path=str(run_dir / "local_preview_result.json") if (run_dir / "local_preview_result.json").is_file() else "",
        human_approval_path=str(run_dir / "human_approval.json") if (run_dir / "human_approval.json").is_file() else "",
        warnings=warnings if warnings else None,
        blocking_reasons=blocking if blocking else None,
        metadata={"dry_run": True},
    )
    contract["gates"] = dict(gates)
    apply_final_render_result_contract(contract)

    paths = {
        "preview_package_dir": str(run_dir),
        "input_preview_path": preview_path,
        "local_preview_result_path": contract["source"].get("local_preview_result_path", ""),
        "human_approval_path": contract["source"].get("human_approval_path", ""),
        "final_render_dir": str(final_render_dir),
        "final_video_path": contract["output"].get("final_video_path", ""),
    }

    return {
        "ok": True,
        "run_id": rid,
        "status": status,
        "message": message,
        "gates": gates,
        "reasons": reasons,
        "contract": contract,
        "paths": paths,
    }

