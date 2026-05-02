"""BA 15.9 — Watch/Radar: lokaler Config-Ingest, Relevanz-Gate, Approval-Queues — kein Auto-Video."""

from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Any, Dict, List

from app.cash_optimization.layer import build_cash_optimization_layer
from app.manual_url_story.batch_engine import normalize_url_duplicate_key
from app.manual_url_story.quality_gate import build_url_quality_gate_result
from app.manual_url_story.schema import (
    UrlQualityStatus,
    WatchApprovalResult,
    WatchItemVerdict,
    WatchRecommendedAction,
)
from app.utils import extract_text_from_url


def load_watch_items_from_json(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """items[] oder sources[] mit url / urls — kuratiert, kein Netz-Fetch."""
    items: List[Dict[str, Any]] = []
    raw_items = data.get("items")
    if isinstance(raw_items, list):
        for it in raw_items:
            if isinstance(it, dict) and (it.get("url") or "").strip():
                items.append(it)

    for src in data.get("sources") or []:
        if not isinstance(src, dict):
            continue
        label = str(src.get("label") or "")
        kind = str(src.get("kind") or "")
        nested = src.get("urls")
        if isinstance(nested, list):
            for u in nested:
                if (str(u) or "").strip():
                    items.append({"url": str(u).strip(), "label": label, "kind": kind})
        elif (src.get("url") or "").strip():
            items.append(
                {
                    "url": str(src.get("url")).strip(),
                    "label": label,
                    "kind": kind,
                }
            )
    return items


def load_watch_config_path(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _relevance_from_gate(gate: Any) -> int:
    return int(
        round(
            (
                int(gate.hook_potential_score)
                + int(gate.narrative_density_score)
                + int(gate.emotional_weight_score)
            )
            / 3.0
        )
    )


def _pick_action(
    *,
    duplicate: bool,
    status: UrlQualityStatus,
    hook: int,
    relevance: int,
) -> WatchRecommendedAction:
    if duplicate:
        return "skip"
    if status == "blocked":
        return "skip"
    if status == "strong" and hook >= 58 and relevance >= 55:
        return "approve"
    if status == "weak" and hook < 28:
        return "skip"
    return "review"


def run_watch_approval_scan(items: List[Dict[str, Any]]) -> WatchApprovalResult:
    """Extraktion + BA-15.7-Gate ohne Rewrite (Token-effizient). Duplicate-Guard light."""
    seen_keys: set[str] = set()
    first_id_by_key: Dict[str, str] = {}
    detected: List[WatchItemVerdict] = []

    for raw in items:
        url = str(raw.get("url") or "").strip()
        label = str(raw.get("label") or "")
        iid = str(uuid.uuid4())
        dup_key = normalize_url_duplicate_key(url) if url else ""
        duplicate = bool(dup_key and dup_key in seen_keys)
        duplicate_of = first_id_by_key.get(dup_key, "") if duplicate else ""
        if dup_key and url and not duplicate:
            seen_keys.add(dup_key)
            first_id_by_key[dup_key] = iid

        notes: List[str] = []
        if duplicate:
            notes.append("duplicate_url_normalized_skip_extract")

        ext_warns: List[str] = []
        if duplicate:
            gate = build_url_quality_gate_result(
                extraction_ok=False,
                extracted_text="",
                narrative_ok=False,
                script_title=label,
                full_script="",
                chapter_count=0,
            )
        else:
            text, ext_warns = extract_text_from_url(url) if url else ("", [])
            ext_ok = bool((text or "").strip())
            gate = build_url_quality_gate_result(
                extraction_ok=ext_ok,
                extracted_text=text if ext_ok else "",
                narrative_ok=False,
                script_title=label,
                full_script="",
                chapter_count=0,
            )
        rel = _relevance_from_gate(gate)
        action = _pick_action(
            duplicate=duplicate,
            status=gate.url_quality_status,
            hook=gate.hook_potential_score,
            relevance=rel,
        )
        notes.extend(ext_warns[:3])

        summary_blob = ""
        if not duplicate and url:
            summary_blob = (text if ext_ok else "")[:1400]

        cash_layer = None
        if url and not duplicate:
            cash_layer = build_cash_optimization_layer(
                gate,
                title=label,
                rewrite_summary=summary_blob,
                chapter_count=0,
                recommended_mode="documentary",
            )

        verdict = WatchItemVerdict(
            item_id=iid,
            source_url=url,
            label=label,
            relevance_score=rel,
            recommended_action=action,
            url_quality_status=gate.url_quality_status,
            hook_potential_score=gate.hook_potential_score,
            duplicate_of_item_id=duplicate_of,
            notes=notes,
            cash_layer=cash_layer,
        )
        detected.append(verdict)

    approval_queue = [v for v in detected if v.recommended_action in ("approve", "review")]
    approval_queue.sort(
        key=lambda v: (
            v.cash_layer.roi.candidate_roi_score if v.cash_layer else 0,
            v.relevance_score,
        ),
        reverse=True,
    )
    rejected_items = [v for v in detected if v.recommended_action == "skip"]

    return WatchApprovalResult(
        detected_items=detected,
        approval_queue=approval_queue,
        rejected_items=rejected_items,
    )
