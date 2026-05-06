"""BA 24.3 — Local Final Render Execution Script (V1: copy preview).

Erzeugt aus einem freigegebenen Local-Preview-Run ein `final_render_<run_id>` Paket:
- kopiert die geprüfte Preview-Datei als `final_video.mp4`
- schreibt `final_render_result.json` (Contract BA 24.1)
- schreibt `FINAL_OPEN_ME.md`

Keine Provider-Calls, kein Upload, kein ffmpeg-Render in BA 24.3.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from app.founder_dashboard.final_render_dry_run import build_final_render_dry_run_for_local_preview
from scripts.final_render_contract import (
    FINAL_RENDER_RESULT_FILENAME,
    apply_final_render_result_contract,
    build_final_render_result_contract,
    write_final_render_result_json,
)

_RUN_ID_RE = re.compile(r"^[A-Za-z0-9_-]{1,80}$")


def _validate_run_id(run_id: str) -> bool:
    s = (run_id or "").strip()
    if not s or ".." in s or "/" in s or "\\" in s:
        return False
    return bool(_RUN_ID_RE.fullmatch(s))


def _safe_nonempty_file(p: Path) -> bool:
    try:
        if p.is_symlink() or not p.is_file():
            return False
        return int(p.stat().st_size) > 0
    except OSError:
        return False


def _file_size_bytes_or_none(p: Path) -> Optional[int]:
    try:
        if p.is_symlink() or not p.is_file():
            return None
        return int(p.stat().st_size)
    except OSError:
        return None


def _recommended_action_for_status(*, status: str) -> str:
    st = str(status or "").strip().lower()
    if st == "completed":
        return "Öffne final_video.mp4 und prüfe es manuell."
    if st == "skipped_existing":
        return "Final Video existierte bereits; nutze --force, wenn du es neu erzeugen willst."
    if st in ("locked", "blocked", "unknown"):
        return "Prüfe Preview Quality, Human Approval und Final Render Gate."
    if st == "failed":
        return "Prüfe Fehlermeldung/Blocking Reasons und starte ggf. erneut mit --force."
    return ""


def _required_final_artifacts(*, final_dir: Path) -> Dict[str, Path]:
    return {
        "final_video.mp4": final_dir / "final_video.mp4",
        "final_render_result.json": final_dir / "final_render_result.json",
        "FINAL_OPEN_ME.md": final_dir / "FINAL_OPEN_ME.md",
        "final_render_report.md": final_dir / "final_render_report.md",
    }


def _validate_final_artifacts(*, final_dir: Path) -> List[str]:
    missing: List[str] = []
    for name, p in _required_final_artifacts(final_dir=final_dir).items():
        if name == "final_video.mp4":
            if not _safe_nonempty_file(p):
                missing.append(name)
        else:
            if not p.is_file():
                missing.append(name)
    return missing


def _write_final_open_me(
    *,
    out_dir: Path,
    status: str,
    run_id: str,
    final_video_path: Path,
    source_preview_path: str,
    preview_package_dir: str,
    approval_path: str,
    gates: Dict[str, Any],
    warnings: List[str],
    blocking_reasons: List[str],
    recommended_action: str,
) -> None:
    # NOTE: Keep this file short, operator-oriented, and path-centric.
    lines: List[str] = [
        "# Final Render Package",
        "",
        "## Status",
        f"Status: {status}",
        "",
        "## Open First",
        f"Final Video: `{final_video_path}`",
        "",
        "## What This Is",
        "Dieses Paket enthält den finalen lokalen Video-Export aus einem freigegebenen Local Preview Run.",
        "",
        "## Source",
        f"Run ID: {run_id}",
        f"Local Preview Package: `{preview_package_dir or '—'}`",
        f"Source Preview: `{source_preview_path or '—'}`",
        f"Local Preview Result: `{(Path(preview_package_dir) / 'local_preview_result.json') if preview_package_dir else '—'}`",
        f"Human Approval: `{approval_path or '—'}`",
        "",
        "## Key Artefacts",
        f"- Final Video: `{final_video_path}`",
        f"- Final Render Result: `{out_dir / 'final_render_result.json'}`",
        f"- Final Render Report: `{out_dir / 'final_render_report.md'}`",
        f"- Source Preview: `{source_preview_path or '—'}`",
        f"- Local Preview Report: `{(Path(preview_package_dir) / 'local_preview_report.md') if preview_package_dir else '—'}`",
        f"- Local Preview OPEN_ME: `{(Path(preview_package_dir) / 'OPEN_ME.md') if preview_package_dir else '—'}`",
        "",
        "## Gates",
        f"- preview_available: {gates.get('preview_available', 'unknown')}",
        f"- quality_not_fail: {gates.get('quality_not_fail', 'unknown')}",
        f"- founder_not_block: {gates.get('founder_not_block', 'unknown')}",
        f"- human_approved: {gates.get('human_approved', 'unknown')}",
        f"- cost_not_over_budget: {gates.get('cost_not_over_budget', 'unknown')}",
        "",
        "## Next Step",
        (recommended_action or _recommended_action_for_status(status=status)) + " Publishing/Upload folgt in einem späteren Block.",
        "",
    ]
    if warnings:
        lines.extend(["## Warnings"] + [f"- {w}" for w in warnings[:50]] + [""])
    else:
        lines.extend(["## Warnings", "- Keine", ""])
    if blocking_reasons:
        lines.extend(["## Blocking Reasons"] + [f"- {b}" for b in blocking_reasons[:50]] + [""])
    else:
        lines.extend(["## Blocking Reasons", "- Keine", ""])
    (out_dir / "FINAL_OPEN_ME.md").write_text("\n".join(lines), encoding="utf-8")


def _write_final_render_report(
    *,
    out_dir: Path,
    contract: Dict[str, Any],
    recommended_action: str,
) -> Path:
    out = Path(out_dir)
    p = out / "final_render_report.md"
    st = str(contract.get("status") or "")
    run_id = str(contract.get("run_id") or "")
    meta = contract.get("metadata") if isinstance(contract.get("metadata"), dict) else {}
    exec_mode = str(meta.get("execution_mode") or "")
    created = str(contract.get("created_at") or "")
    updated = str(contract.get("updated_at") or "")
    src = contract.get("source") if isinstance(contract.get("source"), dict) else {}
    outp = contract.get("output") if isinstance(contract.get("output"), dict) else {}
    gates = contract.get("gates") if isinstance(contract.get("gates"), dict) else {}
    warns = contract.get("warnings") if isinstance(contract.get("warnings"), list) else []
    blocks = contract.get("blocking_reasons") if isinstance(contract.get("blocking_reasons"), list) else []

    lines: List[str] = [
        "# Final Render Report",
        "",
        "## Summary",
        f"- Status: **{st}**",
        f"- Run ID: `{run_id}`",
        f"- Execution mode: `{exec_mode or '—'}`",
        f"- Final video path: `{outp.get('final_video_path') or ''}`",
        f"- Created: `{created}`",
        f"- Updated: `{updated}`",
        "",
        "## Inputs",
        f"- Preview package dir: `{src.get('preview_package_dir') or ''}`",
        f"- Input preview path: `{src.get('input_preview_path') or ''}`",
        f"- Local preview result: `{src.get('local_preview_result_path') or ''}`",
        f"- Human approval: `{src.get('human_approval_path') or ''}`",
        "",
        "## Outputs",
        f"- Final render dir: `{outp.get('final_render_dir') or ''}`",
        f"- Final video: `{outp.get('final_video_path') or ''}`",
        f"- Final OPEN_ME: `{outp.get('final_open_me_path') or ''}`",
        f"- Final report: `{outp.get('final_report_path') or ''}`",
        "",
        "## Gates",
    ]
    for k in (
        "preview_available",
        "quality_not_fail",
        "founder_not_block",
        "human_approved",
        "cost_not_over_budget",
    ):
        lines.append(f"- {k}: `{gates.get(k)}`")
    lines.append("")

    lines.append("## Warnings / Blocking Reasons")
    if warns:
        lines.append("### Warnings")
        for w in warns[:100]:
            lines.append(f"- {w}")
    else:
        lines.append("### Warnings")
        lines.append("- Keine")
    lines.append("")
    if blocks:
        lines.append("### Blocking Reasons")
        for b in blocks[:100]:
            lines.append(f"- {b}")
    else:
        lines.append("### Blocking Reasons")
        lines.append("- Keine")
    lines.append("")
    lines.extend(
        [
            "## Operator Notes",
        "Dieses finale Video wurde lokal erzeugt. Vor Veröffentlichung manuell prüfen.",
        "",
        f"Recommended action: {recommended_action or _recommended_action_for_status(status=st)}",
            "",
        ]
    )
    p.write_text("\n".join(lines), encoding="utf-8")
    return p


def run_final_render_for_local_preview(
    *,
    run_id: str,
    out_root: Path,
    force: bool = False,
) -> Dict[str, Any]:
    """
    BA 24.4 — reusable execution function for CLI + dashboard route.
    Returns a JSON-serializable dict, does not print.
    """
    rid = (run_id or "").strip()
    if not _validate_run_id(rid):
        return {"ok": False, "run_id": rid, "status": "invalid", "message": "invalid run_id"}

    root = Path(out_root)
    dry = build_final_render_dry_run_for_local_preview(run_id=rid, out_root=root)
    if not dry.get("ok"):
        msg = str(dry.get("message") or "dry-run failed")
        return {"ok": False, "run_id": rid, "status": "failed", "message": msg}

    dr_status = str(dry.get("status") or "unknown")
    if dr_status != "ready":
        # Do not write anything on not-ready.
        return {
            "ok": False,
            "run_id": rid,
            "status": dr_status,
            "message": dry.get("message") or "not ready",
            "result": dry.get("contract") or {},
            "paths": dry.get("paths") or {},
            "warnings": list((dry.get("contract") or {}).get("warnings") or []),
            "blocking_reasons": list((dry.get("contract") or {}).get("blocking_reasons") or []),
        }

    paths = dry.get("paths") if isinstance(dry.get("paths"), dict) else {}
    src_preview = str(paths.get("input_preview_path") or "")
    if not src_preview:
        return {"ok": False, "run_id": rid, "status": "blocked", "message": "missing preview path"}
    src_preview_path = Path(src_preview)
    if not _safe_nonempty_file(src_preview_path):
        return {"ok": False, "run_id": rid, "status": "blocked", "message": "preview file missing/empty"}

    final_dir = root / f"final_render_{rid}"
    final_video = final_dir / "final_video.mp4"
    final_open_me = final_dir / "FINAL_OPEN_ME.md"
    final_result_path = final_dir / FINAL_RENDER_RESULT_FILENAME
    final_report_path = final_dir / "final_render_report.md"

    final_dir.mkdir(parents=True, exist_ok=True)

    existing_size = _file_size_bytes_or_none(final_video)
    if existing_size == 0 and not bool(force):
        # Existing but empty file is a hard error unless forced.
        msg = "existing final_video.mp4 is empty; rerun with --force"
        rec = "Lösche die leere Datei oder starte mit --force erneut."
        contract = build_final_render_result_contract(
            run_id=rid,
            source_preview_package_dir=str(paths.get("preview_package_dir") or ""),
            output_dir=final_dir,
            status="failed",
            input_preview_path=src_preview_path,
            output_final_video_path=final_video,
            local_preview_result_path=str(paths.get("local_preview_result_path") or ""),
            human_approval_path=str(paths.get("human_approval_path") or ""),
            warnings=list((dry.get("contract") or {}).get("warnings") or []),
            blocking_reasons=["existing_final_video_empty"],
            metadata={"execution_mode": "copy_preview_v1", "force": False, "dry_run": False},
        )
        contract["gates"] = dict(dry.get("gates") or {})
        if isinstance(contract.get("output"), dict):
            contract["output"]["final_report_path"] = str(final_report_path)
        apply_final_render_result_contract(contract)
        write_final_render_result_json(contract, final_dir)
        _write_final_render_report(out_dir=final_dir, contract=contract, recommended_action=rec)
        _write_final_open_me(
            out_dir=final_dir,
            status="failed",
            run_id=rid,
            final_video_path=final_video,
            source_preview_path=str(src_preview_path),
            preview_package_dir=str(paths.get("preview_package_dir") or ""),
            approval_path=str(paths.get("human_approval_path") or ""),
            gates=dict(contract.get("gates") or {}),
            warnings=list(contract.get("warnings") or []),
            blocking_reasons=list(contract.get("blocking_reasons") or []),
            recommended_action=rec,
        )
        return {
            "ok": False,
            "run_id": rid,
            "status": "failed",
            "message": msg,
            "recommended_action": rec,
            "result": contract,
            "paths": {
                "final_render_dir": str(final_dir),
                "final_video_path": str(final_video),
                "final_result_path": str(final_result_path),
                "final_open_me_path": str(final_open_me),
                "final_report_path": str(final_report_path),
            },
            "warnings": list(contract.get("warnings") or []),
            "blocking_reasons": list(contract.get("blocking_reasons") or []),
        }

    # idempotency
    if _safe_nonempty_file(final_video) and not bool(force):
        rec = _recommended_action_for_status(status="skipped_existing")
        contract = build_final_render_result_contract(
            run_id=rid,
            source_preview_package_dir=str(paths.get("preview_package_dir") or ""),
            output_dir=final_dir,
            status="skipped_existing",
            input_preview_path=src_preview_path,
            output_final_video_path=final_video,
            local_preview_result_path=str(paths.get("local_preview_result_path") or ""),
            human_approval_path=str(paths.get("human_approval_path") or ""),
            warnings=list((dry.get("contract") or {}).get("warnings") or []),
            blocking_reasons=[],
            metadata={"execution_mode": "copy_preview_v1", "force": False, "dry_run": False},
        )
        contract["gates"] = dict(dry.get("gates") or {})
        # BA 24.5: report path is part of output contract
        if isinstance(contract.get("output"), dict):
            contract["output"]["final_report_path"] = str(final_report_path)
        apply_final_render_result_contract(contract)
        write_final_render_result_json(contract, final_dir)
        _write_final_render_report(out_dir=final_dir, contract=contract, recommended_action=rec)
        _write_final_open_me(
            out_dir=final_dir,
            status="skipped_existing",
            run_id=rid,
            final_video_path=final_video,
            source_preview_path=str(src_preview_path),
            preview_package_dir=str(paths.get("preview_package_dir") or ""),
            approval_path=str(paths.get("human_approval_path") or ""),
            gates=dict(contract.get("gates") or {}),
            warnings=list(contract.get("warnings") or []),
            blocking_reasons=list(contract.get("blocking_reasons") or []),
            recommended_action=rec,
        )
        missing = _validate_final_artifacts(final_dir=final_dir)
        if missing:
            contract["status"] = "failed"
            contract["blocking_reasons"] = list(contract.get("blocking_reasons") or []) + [f"final_artifact_missing:{m}" for m in missing]
            if isinstance(contract.get("metadata"), dict):
                contract["metadata"]["recovery_note"] = "artifact validation failed after skipped_existing"
            apply_final_render_result_contract(contract)
            write_final_render_result_json(contract, final_dir)
            msg = "missing final artifacts after skipped_existing"
            return {
                "ok": False,
                "run_id": rid,
                "status": "failed",
                "message": msg,
                "recommended_action": rec,
                "result": contract,
                "paths": {
                    "final_render_dir": str(final_dir),
                    "final_video_path": str(final_video),
                    "final_result_path": str(final_result_path),
                    "final_open_me_path": str(final_open_me),
                    "final_report_path": str(final_report_path),
                },
                "warnings": list(contract.get("warnings") or []),
                "blocking_reasons": list(contract.get("blocking_reasons") or []),
            }
        return {
            "ok": True,
            "run_id": rid,
            "status": "skipped_existing",
            "message": "Final Render existiert bereits.",
            "recommended_action": rec,
            "result": contract,
            "paths": {
                "final_render_dir": str(final_dir),
                "final_video_path": str(final_video),
                "final_result_path": str(final_result_path),
                "final_open_me_path": str(final_open_me),
                "final_report_path": str(final_report_path),
            },
            "warnings": list(contract.get("warnings") or []),
            "blocking_reasons": list(contract.get("blocking_reasons") or []),
        }

    # execution (V1 copy)
    try:
        shutil.copy2(src_preview_path, final_video)
    except Exception as e:
        msg = str(getattr(e, "message", "") or str(e) or "copy failed")
        rec = "Prüfe Schreibrechte und Speicherplatz, dann erneut versuchen."
        return {
            "ok": False,
            "run_id": rid,
            "status": "failed",
            "message": msg,
            "recommended_action": rec,
            "warnings": list((dry.get("contract") or {}).get("warnings") or []),
            "blocking_reasons": ["copy_failed"],
        }

    rec = _recommended_action_for_status(status="completed")
    contract = build_final_render_result_contract(
        run_id=rid,
        source_preview_package_dir=str(paths.get("preview_package_dir") or ""),
        output_dir=final_dir,
        status="completed",
        input_preview_path=src_preview_path,
        output_final_video_path=final_video,
        local_preview_result_path=str(paths.get("local_preview_result_path") or ""),
        human_approval_path=str(paths.get("human_approval_path") or ""),
        warnings=list((dry.get("contract") or {}).get("warnings") or []),
        blocking_reasons=[],
        metadata={"execution_mode": "copy_preview_v1", "force": bool(force), "dry_run": False},
    )
    contract["gates"] = dict(dry.get("gates") or {})
    if isinstance(contract.get("output"), dict):
        contract["output"]["final_report_path"] = str(final_report_path)
    apply_final_render_result_contract(contract)
    write_final_render_result_json(contract, final_dir)
    _write_final_render_report(out_dir=final_dir, contract=contract, recommended_action=rec)

    _write_final_open_me(
        out_dir=final_dir,
        status="completed",
        run_id=rid,
        final_video_path=final_video,
        source_preview_path=str(src_preview_path),
        preview_package_dir=str(paths.get("preview_package_dir") or ""),
        approval_path=str(paths.get("human_approval_path") or ""),
        gates=dict(contract.get("gates") or {}),
        warnings=list(contract.get("warnings") or []),
        blocking_reasons=list(contract.get("blocking_reasons") or []),
        recommended_action=rec,
    )
    missing = _validate_final_artifacts(final_dir=final_dir)
    if missing:
        contract["status"] = "failed"
        contract["blocking_reasons"] = list(contract.get("blocking_reasons") or []) + [f"final_artifact_missing:{m}" for m in missing]
        if isinstance(contract.get("metadata"), dict):
            contract["metadata"]["recovery_note"] = "artifact validation failed after completed"
        apply_final_render_result_contract(contract)
        write_final_render_result_json(contract, final_dir)
        msg = "missing final artifacts after completed"
        return {
            "ok": False,
            "run_id": rid,
            "status": "failed",
            "message": msg,
            "recommended_action": rec,
            "result": contract,
            "paths": {
                "final_render_dir": str(final_dir),
                "final_video_path": str(final_video),
                "final_result_path": str(final_result_path),
                "final_open_me_path": str(final_open_me),
                "final_report_path": str(final_report_path),
            },
            "warnings": list(contract.get("warnings") or []),
            "blocking_reasons": list(contract.get("blocking_reasons") or []),
        }
    return {
        "ok": True,
        "run_id": rid,
        "status": "completed",
        "message": "Final Render abgeschlossen.",
        "recommended_action": rec,
        "result": contract,
        "paths": {
            "final_render_dir": str(final_dir),
            "final_video_path": str(final_video),
            "final_result_path": str(final_result_path),
            "final_open_me_path": str(final_open_me),
            "final_report_path": str(final_report_path),
        },
        "warnings": list(contract.get("warnings") or []),
        "blocking_reasons": list(contract.get("blocking_reasons") or []),
    }


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="BA 24.3 — Local Final Render (V1: copy preview).")
    parser.add_argument("--run-id", required=True, dest="run_id")
    parser.add_argument("--out-root", type=Path, default=Path(__file__).resolve().parents[1] / "output", dest="out_root")
    parser.add_argument("--force", action="store_true", dest="force")
    parser.add_argument("--print-json", action="store_true", dest="print_json")
    args = parser.parse_args(argv)

    try:
        run_id = (args.run_id or "").strip()
        if not _validate_run_id(run_id):
            err = {
                "ok": False,
                "status": "invalid",
                "message": "invalid run_id",
                "run_id": run_id,
                "warnings": [],
                "blocking_reasons": ["invalid_run_id"],
                "recommended_action": "Nutze eine run_id ohne Pfadzeichen (A–Z, 0–9, _, -).",
            }
            if args.print_json:
                print(json.dumps(err, ensure_ascii=False, indent=2))
            return 3

        out_root = Path(args.out_root)
        res = run_final_render_for_local_preview(run_id=run_id, out_root=out_root, force=bool(args.force))
        if args.print_json:
            print(json.dumps(res, ensure_ascii=False, indent=2))
        if not res.get("ok"):
            st = str(res.get("status") or "")
            if st == "invalid":
                return 3
            if st in ("locked", "blocked", "unknown"):
                return 2
            return 1
        return 0
    except Exception as e:
        msg = str(getattr(e, "message", "") or str(e) or "unknown error")
        if len(msg) > 400:
            msg = msg[:397] + "..."
        err = {
            "ok": False,
            "status": "failed",
            "message": msg,
            "warnings": [],
            "blocking_reasons": ["unexpected_exception"],
            "recommended_action": "Erneut versuchen; falls reproduzierbar: Logs prüfen.",
        }
        if getattr(args, "print_json", False):
            print(json.dumps(err, ensure_ascii=False, indent=2))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

