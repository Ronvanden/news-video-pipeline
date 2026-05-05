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


def _write_final_open_me(
    *,
    out_dir: Path,
    status: str,
    run_id: str,
    final_video_path: Path,
    source_preview_path: str,
    preview_package_dir: str,
    approval_path: str,
    warnings: List[str],
) -> None:
    lines: List[str] = [
        "# Final Render Package",
        "",
        f"Status: {status}",
        f"Run ID: {run_id}",
        f"Final Video: {final_video_path}",
        f"Source Preview: {source_preview_path or '—'}",
        f"Local Preview Package: {preview_package_dir or '—'}",
        f"Approval: {approval_path or '—'}",
        "",
    ]
    if warnings:
        lines.append("Warnings:")
        for w in warnings[:25]:
            lines.append(f"- {w}")
        lines.append("")
    lines.extend(
        [
            "Next Step:",
            "Dieses finale Video prüfen und später für Publishing/Upload verwenden.",
            "",
        ]
    )
    (out_dir / "FINAL_OPEN_ME.md").write_text("\n".join(lines), encoding="utf-8")


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

    final_dir.mkdir(parents=True, exist_ok=True)

    # idempotency
    if _safe_nonempty_file(final_video) and not bool(force):
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
        apply_final_render_result_contract(contract)
        write_final_render_result_json(contract, final_dir)
        _write_final_open_me(
            out_dir=final_dir,
            status="skipped_existing",
            run_id=rid,
            final_video_path=final_video,
            source_preview_path=str(src_preview_path),
            preview_package_dir=str(paths.get("preview_package_dir") or ""),
            approval_path=str(paths.get("human_approval_path") or ""),
            warnings=list(contract.get("warnings") or []),
        )
        return {
            "ok": True,
            "run_id": rid,
            "status": "skipped_existing",
            "message": "Final Render existiert bereits.",
            "result": contract,
            "paths": {
                "final_render_dir": str(final_dir),
                "final_video_path": str(final_video),
                "final_result_path": str(final_result_path),
                "final_open_me_path": str(final_open_me),
            },
            "warnings": list(contract.get("warnings") or []),
            "blocking_reasons": list(contract.get("blocking_reasons") or []),
        }

    # execution (V1 copy)
    try:
        shutil.copy2(src_preview_path, final_video)
    except Exception as e:
        msg = str(getattr(e, "message", "") or str(e) or "copy failed")
        return {"ok": False, "run_id": rid, "status": "failed", "message": msg}

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
    apply_final_render_result_contract(contract)
    write_final_render_result_json(contract, final_dir)

    _write_final_open_me(
        out_dir=final_dir,
        status="completed",
        run_id=rid,
        final_video_path=final_video,
        source_preview_path=str(src_preview_path),
        preview_package_dir=str(paths.get("preview_package_dir") or ""),
        approval_path=str(paths.get("human_approval_path") or ""),
        warnings=list(contract.get("warnings") or []),
    )
    return {
        "ok": True,
        "run_id": rid,
        "status": "completed",
        "message": "Final Render abgeschlossen.",
        "result": contract,
        "paths": {
            "final_render_dir": str(final_dir),
            "final_video_path": str(final_video),
            "final_result_path": str(final_result_path),
            "final_open_me_path": str(final_open_me),
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

    run_id = (args.run_id or "").strip()
    if not _validate_run_id(run_id):
        err = {"ok": False, "status": "invalid", "message": "invalid run_id", "run_id": run_id}
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


if __name__ == "__main__":
    raise SystemExit(main())

