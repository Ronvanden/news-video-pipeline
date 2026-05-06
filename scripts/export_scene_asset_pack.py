"""BA 18.2 — Scene Expansion → lokaler Founder Asset Pack (JSON, Prompts, Shot-Plan, Summary)."""

from __future__ import annotations

import argparse
import json
import re
import sys
import uuid
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.prompt_engine.pipeline import build_production_prompt_plan
from app.prompt_engine.schema import ProductionPromptPlan, PromptPlanRequest
from app.scene_expansion.layer import build_scene_expansion_layer


def _collapse_ws(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").strip())


def clean_leonardo_prompt_line(visual_prompt: str, camera_motion_hint: str, *, max_len: int = 520) -> str:
    """Produktions-taugliche Einzeiler: keine Debug-Reste, kein harter Mid-Word-Schnitt."""
    t = _collapse_ws(visual_prompt)
    for prefix in (
        "Establishing:",
        "Detail beat:",
        "B-roll / cutaway supporting narrative —",
        "B-roll / cutaway supporting narrative -",
    ):
        if t.lower().startswith(prefix.lower()):
            t = _collapse_ws(t[len(prefix) :])
    t = t.replace(" …", " ").replace("…", " ").strip()
    t = re.sub(r"\s*—\s*—+", " — ", t)
    cam = _collapse_ws(camera_motion_hint)
    if cam:
        extra = f" | Camera: {cam}"
        if len(t) + len(extra) <= max_len:
            t = (t + extra).strip()
    if len(t) > max_len:
        cut = t[: max_len - 1].rsplit(" ", 1)[0].strip()
        t = cut + "…" if cut else t[:max_len]
    return t


def ensure_scene_expansion_on_plan(plan: ProductionPromptPlan) -> ProductionPromptPlan:
    if plan.scene_expansion_result is not None:
        return plan
    return plan.model_copy(update={"scene_expansion_result": build_scene_expansion_layer(plan)})


def load_plan_from_url(url: str, *, topic: str = "Scene Asset Pack Export", duration_minutes: int = 10) -> ProductionPromptPlan:
    req = PromptPlanRequest(
        topic=topic,
        title="",
        source_summary="",
        manual_source_url=url.strip(),
        manual_url_duration_minutes=duration_minutes,
    )
    return build_production_prompt_plan(req)


def load_plan_from_json(path: Path) -> ProductionPromptPlan:
    raw = json.loads(path.read_text(encoding="utf-8"))
    return ProductionPromptPlan.model_validate(raw)


def _recommended_production_mode(plan: ProductionPromptPlan) -> str:
    parts = [plan.video_template or "generic", plan.template_type or "unknown"]
    return " / ".join(p for p in parts if p)


def build_shot_plan_markdown(plan: ProductionPromptPlan) -> str:
    ser = plan.scene_expansion_result
    if not ser:
        return "# Shot plan\n\n(no scene expansion)\n"
    lines: List[str] = ["# Shot plan", "", f"Template: `{plan.template_type}` | Video template: `{plan.video_template}`", ""]
    by_ch: Dict[int, List[Any]] = {}
    for b in ser.expanded_scene_assets:
        by_ch.setdefault(b.chapter_index, []).append(b)
    chapters = list(plan.chapter_outline or [])
    for ci in sorted(by_ch.keys()):
        title = chapters[ci].title if ci < len(chapters) else f"Chapter {ci + 1}"
        summ = (chapters[ci].summary if ci < len(chapters) else "")[:200]
        lines.append(f"## Chapter {ci + 1}: {_collapse_ws(title)}")
        if summ:
            lines.append("")
            lines.append(f"*{summ}*")
        lines.append("")
        for b in sorted(by_ch[ci], key=lambda x: x.beat_index):
            lines.append(
                f"- **Beat {b.beat_index + 1}** ({b.asset_type}, {b.duration_seconds}s): "
                f"{_collapse_ws(b.visual_prompt)[:400]}"
            )
            if b.camera_motion_hint:
                lines.append(f"  - Camera: {_collapse_ws(b.camera_motion_hint)}")
        lines.append("")
    return "\n".join(lines).strip() + "\n"


def build_founder_summary_text(plan: ProductionPromptPlan, *, source_label: str) -> str:
    ser = plan.scene_expansion_result
    n_ch = len(plan.chapter_outline or [])
    n_beats = len(ser.expanded_scene_assets) if ser else 0
    hook = _collapse_ws(plan.hook or "")
    lines = [
        "Founder Scene Asset Pack — BA 18.2",
        "",
        f"Source: {source_label}",
        f"Total chapters: {n_ch}",
        f"Total beats: {n_beats}",
        f"Recommended production mode: {_recommended_production_mode(plan)}",
        f"Viral hook (plan): {hook[:500]}",
        f"Template type: {plan.template_type}",
        "",
        "Pack contains: scene_asset_pack.json, leonardo_prompts.txt, shot_plan.md, founder_summary.txt",
    ]
    return "\n".join(lines) + "\n"


def write_scene_asset_pack(
    plan: ProductionPromptPlan,
    dest_dir: Path,
    *,
    source_label: str,
) -> Dict[str, Any]:
    """Schreibt alle Pack-Dateien nach dest_dir (existiert oder wird angelegt)."""
    plan = ensure_scene_expansion_on_plan(plan)
    ser = plan.scene_expansion_result
    if ser is None:
        raise RuntimeError("scene_expansion_result missing after ensure_scene_expansion_on_plan")
    dest_dir.mkdir(parents=True, exist_ok=True)

    pack_body: Dict[str, Any] = {
        "export_version": "18.2-v1",
        "source_label": source_label,
        "template_type": plan.template_type,
        "video_template": plan.video_template,
        "hook": plan.hook,
        "scene_expansion": ser.model_dump(),
    }
    (dest_dir / "scene_asset_pack.json").write_text(
        json.dumps(pack_body, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    leo_lines: List[str] = []
    for b in ser.expanded_scene_assets:
        line = clean_leonardo_prompt_line(b.visual_prompt, b.camera_motion_hint)
        if line:
            leo_lines.append(line)
    (dest_dir / "leonardo_prompts.txt").write_text("\n".join(leo_lines) + ("\n" if leo_lines else ""), encoding="utf-8")

    (dest_dir / "shot_plan.md").write_text(build_shot_plan_markdown(plan), encoding="utf-8")
    (dest_dir / "founder_summary.txt").write_text(
        build_founder_summary_text(plan, source_label=source_label),
        encoding="utf-8",
    )

    return {
        "output_dir": str(dest_dir.resolve()),
        "files": [
            "scene_asset_pack.json",
            "leonardo_prompts.txt",
            "shot_plan.md",
            "founder_summary.txt",
        ],
        "beat_count": len(ser.expanded_scene_assets),
        "chapter_count": len(plan.chapter_outline or []),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Export Scene Expansion als lokaler Founder Asset Pack.")
    src = parser.add_mutually_exclusive_group(required=True)
    src.add_argument("--url", help="Artikel-URL → voller Prompt-Plan inkl. Scene Expansion")
    src.add_argument(
        "--prompt-plan-json",
        dest="prompt_plan_json",
        type=Path,
        help="Vollständiges ProductionPromptPlan als JSON (z. B. API-Export)",
    )
    parser.add_argument("--topic", default="Scene Asset Pack Export", help="Nur bei --url: topic für PromptPlanRequest.")
    parser.add_argument("--duration-minutes", type=int, default=10, dest="duration_minutes")
    parser.add_argument(
        "--out-root",
        type=Path,
        default=ROOT / "output",
        help="Wurzel für output/scene_asset_pack_<run_id>/ (Standard: ./output)",
    )
    parser.add_argument("--run-id", dest="run_id", default="", help="Optional; sonst UUID.")
    args = parser.parse_args()

    if args.prompt_plan_json:
        plan = load_plan_from_json(args.prompt_plan_json)
        source_label = f"json:{args.prompt_plan_json}"
    else:
        plan = load_plan_from_url(
            args.url,
            topic=args.topic,
            duration_minutes=args.duration_minutes,
        )
        source_label = f"url:{args.url.strip()}"

    run_id = (args.run_id or "").strip() or str(uuid.uuid4())
    out_dir = Path(args.out_root).resolve() / f"scene_asset_pack_{run_id}"
    meta = write_scene_asset_pack(plan, out_dir, source_label=source_label)

    print(json.dumps({"ok": True, "run_id": run_id, **meta}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
