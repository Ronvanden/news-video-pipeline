"""BA 20.13 — Sicheres Aufräumen alter local_preview_* Ordner (Dry-Run standard)."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

_LOCAL_PREVIEW_PREFIX = "local_preview_"


def _nonneg_int(s: str) -> int:
    v = int(s)
    if v < 0:
        raise argparse.ArgumentTypeError("must be >= 0")
    return v


def _safe_out_root(out_root: Path) -> Path | None:
    try:
        p = out_root.resolve()
        if p.exists() and p.is_dir():
            return p
    except OSError:
        pass
    return None


def discover_local_preview_runs(out_root: Path) -> List[Path]:
    """
    Direkte Unterordner von out_root: nur Verzeichnisse, Name local_preview_*,
    kein Symlink — sortiert nach st_mtime absteigend, bei Gleichstand nach Name.
    """
    _, ordered, _skipped = _scan_local_preview_dirs(out_root)
    return ordered


def _scan_local_preview_dirs(out_root: Path) -> Tuple[Path | None, List[Path], Dict[str, List[str]]]:
    skipped: Dict[str, List[str]] = {"symlinks": [], "wrong_name_file": [], "stat_error": []}
    root_res = _safe_out_root(out_root)
    if root_res is None:
        return None, [], skipped

    rows: List[Tuple[float, str, Path]] = []
    try:
        entries = list(root_res.iterdir())
    except OSError:
        return root_res, [], skipped

    for entry in entries:
        if entry.is_symlink():
            skipped["symlinks"].append(str(entry))
            continue
        if not entry.is_dir():
            if entry.is_file() and entry.name.startswith(_LOCAL_PREVIEW_PREFIX):
                skipped["wrong_name_file"].append(str(entry))
            continue
        if not entry.name.startswith(_LOCAL_PREVIEW_PREFIX):
            continue
        try:
            mt = entry.stat().st_mtime
        except OSError:
            skipped["stat_error"].append(str(entry))
            continue
        rows.append((mt, entry.name, entry))

    rows.sort(key=lambda t: (-t[0], t[1]))
    ordered = [t[2] for t in rows]
    return root_res, ordered, skipped


def plan_local_preview_cleanup(
    out_root: Path,
    keep_latest: int = 5,
    max_delete: int = 20,
) -> Dict[str, Any]:
    root_res, ordered, skipped = _scan_local_preview_dirs(out_root)
    warnings: List[str] = []
    for s in skipped["symlinks"]:
        warnings.append(f"cleanup_skipped_symlink:{s}")
    for s in skipped["stat_error"]:
        warnings.append(f"cleanup_skipped_stat_error:{s}")

    if root_res is None:
        return {
            "out_root": str(out_root),
            "keep_latest": keep_latest,
            "max_delete": max_delete,
            "found_count": 0,
            "kept_count": 0,
            "kept_paths": [],
            "delete_candidates": [],
            "would_delete_count": 0,
            "skipped_symlinks": skipped["symlinks"],
            "discovered_paths": [],
            "warnings": warnings,
        }

    found = len(ordered)
    kept_paths = ordered[:keep_latest]
    tail = ordered[keep_latest:]
    delete_candidates_paths = tail[:max_delete]
    if len(tail) > max_delete:
        warnings.append(f"cleanup_truncated_by_max_delete:{len(tail) - max_delete}")

    return {
        "out_root": str(root_res),
        "keep_latest": keep_latest,
        "max_delete": max_delete,
        "found_count": found,
        "kept_count": len(kept_paths),
        "kept_paths": [str(p.resolve()) for p in kept_paths],
        "delete_candidates": [str(p.resolve()) for p in delete_candidates_paths],
        "would_delete_count": len(delete_candidates_paths),
        "skipped_symlinks": skipped["symlinks"],
        "discovered_paths": [str(p.resolve()) for p in ordered],
        "warnings": warnings,
    }


def apply_local_preview_cleanup(plan: Dict[str, Any]) -> Dict[str, Any]:
    """Löscht nur Einträge aus delete_candidates nach erneuter Prüfung."""
    out_root = Path(plan.get("out_root") or "")
    extra_warnings: List[str] = []
    deleted_paths: List[str] = []

    try:
        root_res = out_root.resolve()
    except OSError:
        return {
            "deleted_paths": [],
            "deleted_count": 0,
            "apply_warnings": ["cleanup_apply_invalid_out_root"],
        }

    if not root_res.is_dir():
        return {
            "deleted_paths": [],
            "deleted_count": 0,
            "apply_warnings": ["cleanup_apply_out_root_not_dir"],
        }

    for path_str in list(plan.get("delete_candidates") or []):
        p = Path(path_str)
        if p.is_symlink():
            extra_warnings.append(f"cleanup_apply_skip_symlink:{path_str}")
            continue
        if not p.exists():
            extra_warnings.append(f"cleanup_apply_missing:{path_str}")
            continue
        if not p.is_dir():
            extra_warnings.append(f"cleanup_apply_skip_not_dir:{path_str}")
            continue
        if not p.name.startswith(_LOCAL_PREVIEW_PREFIX):
            extra_warnings.append(f"cleanup_apply_skip_bad_prefix:{path_str}")
            continue
        try:
            parent = p.parent.resolve()
        except OSError:
            extra_warnings.append(f"cleanup_apply_skip_parent:{path_str}")
            continue
        if parent != root_res:
            extra_warnings.append(f"cleanup_apply_skip_not_direct_child:{path_str}")
            continue
        try:
            shutil.rmtree(p)
            deleted_paths.append(str(p.resolve()))
        except OSError as e:
            extra_warnings.append(f"cleanup_apply_rmtree_failed:{path_str}:{e!s}")

    return {
        "deleted_paths": deleted_paths,
        "deleted_count": len(deleted_paths),
        "apply_warnings": extra_warnings,
    }


def build_local_preview_cleanup_summary(result: Dict[str, Any]) -> str:
    """Menschenlesbare Zusammenfassung (Dry-Run oder nach Apply)."""
    out = str(result.get("out_root") or "")
    kl = int(result.get("keep_latest") or 0)
    md = int(result.get("max_delete") or 0)
    dry = bool(result.get("dry_run", True))
    found = int(result.get("found_count") or 0)
    would = int(result.get("would_delete_count") or 0)
    kept = int(result.get("kept_count") or 0)
    mode = "DRY RUN" if dry else "APPLY"

    lines = [
        "Local Preview Cleanup",
        "",
        f"Out root: {out}",
        f"Keep latest: {kl}",
        f"Mode: {mode}",
        "",
        f"Found: {found}",
    ]
    if dry:
        lines.append(f"Would delete: {would}")
    else:
        lines.append(f"Deleted: {int(result.get('deleted_count') or 0)}")
    lines.append(f"Kept: {kept}")
    lines.append("")

    cands = result.get("delete_candidates") or []
    if dry and cands:
        lines.append("Delete candidates:")
        for c in cands:
            lines.append(f"- {c}")
        lines.append("")
        lines.append("Next step:")
        lines.append("Run again with --apply to delete the listed candidates.")
    elif dry and not cands:
        lines.append("Delete candidates:")
        lines.append("(none)")
        lines.append("")
    elif not dry:
        lines.append("Removed paths:")
        for c in result.get("deleted_paths") or []:
            lines.append(f"- {c}")
        if not result.get("deleted_paths"):
            lines.append("(none)")
        lines.append("")

    lines.append("")
    return "\n".join(lines)


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="BA 20.13 — Retention: alte local_preview_* Ordner listen oder löschen (Standard: Dry-Run)."
    )
    parser.add_argument("--out-root", type=Path, default=ROOT / "output", dest="out_root")
    parser.add_argument("--keep-latest", type=_nonneg_int, default=5, dest="keep_latest")
    parser.add_argument("--max-delete", type=_nonneg_int, default=20, dest="max_delete")
    parser.add_argument(
        "--apply",
        action="store_true",
        dest="apply",
        help="Kandidaten wirklich löschen (ohne dieses Flag nur Dry-Run)",
    )
    parser.add_argument("--print-json", action="store_true", dest="print_json")
    args = parser.parse_args(argv)

    plan = plan_local_preview_cleanup(args.out_root, args.keep_latest, args.max_delete)
    plan["dry_run"] = not args.apply

    if args.apply:
        execr = apply_local_preview_cleanup(plan)
        merged: Dict[str, Any] = {**plan}
        merged["deleted_paths"] = execr.get("deleted_paths") or []
        merged["deleted_count"] = execr.get("deleted_count") or 0
        aw = list(plan.get("warnings") or [])
        aw.extend(execr.get("apply_warnings") or [])
        merged["warnings"] = aw
    else:
        merged = {**plan}
        merged["deleted_count"] = 0
        merged["deleted_paths"] = []

    print(build_local_preview_cleanup_summary(merged), end="")
    if args.print_json:
        slim = {k: v for k, v in merged.items() if k != "discovered_paths"}
        print("\n---\n")
        print(json.dumps(slim, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
