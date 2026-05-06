"""BA 24.1 — Final Render Contract (final_render_result.json).

Stabiles Result-Schema für spätere Final-Render-Ausführung (ohne Render in BA 24.1).
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

FINAL_RENDER_RESULT_CONTRACT_ID = "final_render_result"
FINAL_RENDER_RESULT_SCHEMA_VERSION = "final_render_result_v1"
FINAL_RENDER_RESULT_FILENAME = "final_render_result.json"

FINAL_RENDER_ALLOWED_STATUSES = frozenset(
    {
        "ready",
        "locked",
        "running",
        "completed",
        "failed",
        "skipped_existing",
        "blocked",
    }
)

_GATE_STATES = frozenset({"unknown", "pass", "fail"})


def _now_iso_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _str_path_or_empty(v: Any) -> str:
    if v is None:
        return ""
    if isinstance(v, Path):
        return str(v)
    s = str(v)
    return s if s.strip() else ""


def _list_str(v: Any) -> List[str]:
    if v is None:
        return []
    if isinstance(v, list):
        out: List[str] = []
        for x in v:
            if x is None:
                continue
            s = str(x).strip()
            if s:
                out.append(s)
        return out
    s = str(v).strip()
    return [s] if s else []


def _gate_state(v: Any) -> str:
    s = str(v or "").strip().lower()
    if s in _GATE_STATES:
        return s
    return "unknown"


def build_final_render_result_contract(
    *,
    run_id: str,
    source_preview_package_dir: str | Path,
    output_dir: str | Path,
    status: str = "ready",
    input_preview_path: str | Path | None = None,
    output_final_video_path: str | Path | None = None,
    local_preview_result_path: str | Path | None = None,
    human_approval_path: str | Path | None = None,
    warnings: list[str] | None = None,
    blocking_reasons: list[str] | None = None,
    metadata: dict | None = None,
) -> Dict[str, Any]:
    st = str(status or "").strip().lower()
    if st not in FINAL_RENDER_ALLOWED_STATUSES:
        raise ValueError(f"invalid final render status: {status!r}")

    out_dir = Path(output_dir)
    src_dir = Path(source_preview_package_dir)

    final_video = (
        Path(output_final_video_path)
        if output_final_video_path is not None
        else (out_dir / "final_video.mp4")
    )
    final_open_me = out_dir / "FINAL_OPEN_ME.md"

    now = _now_iso_utc()
    contract: Dict[str, Any] = {
        "contract_id": FINAL_RENDER_RESULT_CONTRACT_ID,
        "schema_version": FINAL_RENDER_RESULT_SCHEMA_VERSION,
        "run_id": str(run_id or "").strip(),
        "status": st,
        "created_at": now,
        "updated_at": now,
        "source": {
            "preview_package_dir": str(src_dir),
            "input_preview_path": _str_path_or_empty(input_preview_path),
            "local_preview_result_path": _str_path_or_empty(local_preview_result_path),
            "human_approval_path": _str_path_or_empty(human_approval_path),
        },
        "output": {
            "final_render_dir": str(out_dir),
            "final_video_path": str(final_video),
            "final_open_me_path": str(final_open_me),
            "final_report_path": "",
            "export_manifest_path": "",
        },
        "gates": {
            "preview_available": "unknown",
            "quality_not_fail": "unknown",
            "founder_not_block": "unknown",
            "human_approved": "unknown",
            "cost_not_over_budget": "unknown",
        },
        "warnings": _list_str(warnings),
        "blocking_reasons": _list_str(blocking_reasons),
        "metadata": dict(metadata) if isinstance(metadata, dict) else {},
    }
    return contract


def apply_final_render_result_contract(result: Dict[str, Any]) -> Dict[str, Any]:
    """Defensiv: ergänzt fehlende Felder in-place, ohne zu crashen."""
    if not isinstance(result, dict):
        raise TypeError("apply_final_render_result_contract expects dict")

    result.setdefault("contract_id", FINAL_RENDER_RESULT_CONTRACT_ID)
    result.setdefault("schema_version", FINAL_RENDER_RESULT_SCHEMA_VERSION)
    result.setdefault("run_id", str(result.get("run_id") or "").strip())

    st = str(result.get("status") or "ready").strip().lower()
    if st not in FINAL_RENDER_ALLOWED_STATUSES:
        st = "ready"
    result["status"] = st

    ca = str(result.get("created_at") or "").strip()
    if not ca:
        ca = _now_iso_utc()
    result["created_at"] = ca
    ua = str(result.get("updated_at") or "").strip()
    if not ua:
        ua = ca
    result["updated_at"] = ua

    src = result.get("source") if isinstance(result.get("source"), dict) else {}
    src = dict(src)
    src.setdefault("preview_package_dir", "")
    src.setdefault("input_preview_path", "")
    src.setdefault("local_preview_result_path", "")
    src.setdefault("human_approval_path", "")
    result["source"] = src

    out = result.get("output") if isinstance(result.get("output"), dict) else {}
    out = dict(out)
    out.setdefault("final_render_dir", "")
    out.setdefault("final_video_path", "final_video.mp4")
    out.setdefault("final_open_me_path", "FINAL_OPEN_ME.md")
    out.setdefault("final_report_path", "")
    out.setdefault("export_manifest_path", "")
    result["output"] = out

    gates = result.get("gates") if isinstance(result.get("gates"), dict) else {}
    gates = dict(gates)
    for k in (
        "preview_available",
        "quality_not_fail",
        "founder_not_block",
        "human_approved",
        "cost_not_over_budget",
    ):
        gates[k] = _gate_state(gates.get(k))
    result["gates"] = gates

    result["warnings"] = _list_str(result.get("warnings"))
    result["blocking_reasons"] = _list_str(result.get("blocking_reasons"))
    md = result.get("metadata")
    result["metadata"] = dict(md) if isinstance(md, dict) else {}
    return result


def write_final_render_result_json(contract: Dict[str, Any], output_dir: Path) -> Path:
    """Schreibt `final_render_result.json` unter output_dir (UTF-8)."""
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    apply_final_render_result_contract(contract)
    p = out_dir / FINAL_RENDER_RESULT_FILENAME
    p.write_text(json.dumps(contract, ensure_ascii=False, indent=2), encoding="utf-8")
    return p


def load_final_render_result_json(path: Path) -> Dict[str, Any]:
    """Optional: lädt JSON und wendet Contract-Defaults an."""
    p = Path(path)
    raw = json.loads(p.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("final_render_result.json must be a dict")
    apply_final_render_result_contract(raw)
    return raw

