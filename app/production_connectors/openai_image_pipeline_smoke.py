"""BA 32.71 — Minimaler OpenAI-Image-Pipeline-Smoke (Asset Runner, 1–2 Szenen)."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from app.production_connectors.openai_image_smoke import sanitize_openai_image_smoke_warnings

_REPO_ROOT = Path(__file__).resolve().parents[2]
_ASSET_RUNNER_SCRIPT = _REPO_ROOT / "scripts" / "run_asset_runner.py"


def _load_asset_runner_module():
    spec = importlib.util.spec_from_file_location("run_asset_runner_ba371", _ASSET_RUNNER_SCRIPT)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _sorted_beats(scene_expansion: Dict[str, Any]) -> List[Dict[str, Any]]:
    raw = scene_expansion.get("expanded_scene_assets") or []
    if not isinstance(raw, list):
        return []
    rows = [x for x in raw if isinstance(x, dict)]
    return sorted(rows, key=lambda b: (int(b.get("chapter_index", 0)), int(b.get("beat_index", 0))))


def trim_scene_asset_pack(source_pack: Path, max_beats: int, dest: Path) -> Path:
    """Erste ``max_beats`` Beats nach chapter/beat sortiert; schreibt ``dest``."""
    max_b = max(1, int(max_beats))
    data = json.loads(Path(source_pack).read_text(encoding="utf-8"))
    se = data.get("scene_expansion")
    if not isinstance(se, dict):
        raise ValueError("scene_asset_pack: scene_expansion missing or not object")
    beats = _sorted_beats(se)
    if not beats:
        raise ValueError("scene_expansion.expanded_scene_assets empty")
    se["expanded_scene_assets"] = beats[:max_b]
    dest = Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return dest


def write_builtin_minimal_scene_pack(dest: Path, num_beats: int) -> Path:
    """Sichere Mini-Pack-Struktur (ohne Provider-Secrets); ``num_beats`` 1 oder 2."""
    n = max(1, min(2, int(num_beats)))
    beats: List[Dict[str, Any]] = []
    for idx in range(n):
        beats.append(
            {
                "chapter_index": 0,
                "beat_index": idx,
                "visual_prompt": "Editorial establishing frame, neutral tones, open negative space, no readable text.",
                "visual_prompt_effective": (
                    "Editorial establishing frame, neutral tones, open negative space, no readable text.\n\n"
                    "[visual_no_text_guard_v26_4]\nNo readable text."
                ),
                "visual_prompt_raw": "Editorial establishing frame, neutral tones, open negative space, no readable text.",
                "camera_motion_hint": "static",
                "duration_seconds": 8,
                "asset_type": "establishing",
                "overlay_intent": [],
                "text_sensitive": False,
                "visual_asset_kind": "cinematic_broll",
                "routed_visual_provider": "leonardo",
                "continuity_note": "",
                "safety_notes": [],
            }
        )
    doc = {
        "export_version": "ba32_71_pipeline_smoke-v1",
        "scene_expansion": {"expanded_scene_assets": beats},
    }
    dest = Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")
    return dest


def _parse_meta_from_warnings(warnings: List[str]) -> Tuple[str, str]:
    model = "unknown"
    size = ""
    for w in warnings:
        s = str(w)
        if s.startswith("openai_image_model:"):
            model = s.split(":", 1)[1].strip() or model
        elif s.startswith("openai_image_size:"):
            size = s.split(":", 1)[1].strip()
    return model, size


def run_openai_image_pipeline_smoke_v1(
    *,
    pack_path: Path,
    out_root: Path,
    run_id: str,
    max_scenes: int,
    openai_image_model: Optional[str],
    openai_image_size: str,
    openai_image_timeout_seconds: float,
    invoke_runner: Optional[Any] = None,
) -> Dict[str, Any]:
    """
    Ein Asset-Runner-Lauf mit ``IMAGE_PROVIDER=openai_image`` (ENV wird vom Aufrufer gesetzt).

    ``invoke_runner``: injizierbar für Tests (Callable wie ``run_local_asset_runner``).
    """
    ms = max(1, min(2, int(max_scenes)))
    mod = _load_asset_runner_module() if invoke_runner is None else None
    runner_fn = invoke_runner if invoke_runner is not None else mod.run_local_asset_runner

    meta = runner_fn(
        Path(pack_path).resolve(),
        Path(out_root).resolve(),
        run_id=str(run_id),
        mode="live",
        max_assets_live=ms,
        openai_image_model=openai_image_model,
        openai_image_size=str(openai_image_size).strip() or "1024x1024",
        openai_image_timeout_seconds=float(openai_image_timeout_seconds),
    )

    warns_raw = list(meta.get("warnings") or [])
    warns = sanitize_openai_image_smoke_warnings(warns_raw)
    out_dir = Path(str(meta.get("output_dir") or "")).resolve()
    man_path = Path(str(meta.get("manifest_path") or ""))
    assets: List[Dict[str, Any]] = []
    if man_path.is_file():
        try:
            man = json.loads(man_path.read_text(encoding="utf-8"))
            raw_a = man.get("assets")
            if isinstance(raw_a, list):
                assets = [x for x in raw_a if isinstance(x, dict)]
        except (OSError, json.JSONDecodeError):
            pass

    generated_count = sum(1 for a in assets if a.get("generation_mode") == "openai_image_live")
    failed_count = sum(1 for a in assets if a.get("generation_mode") == "openai_image_fallback_placeholder")
    asset_paths: List[str] = []
    for a in assets:
        if a.get("generation_mode") != "openai_image_live":
            continue
        ip = str(a.get("image_path") or "").strip()
        if ip:
            asset_paths.append(str((out_dir / ip).resolve()))

    model_guess, size_guess = _parse_meta_from_warnings(warns)
    if openai_image_model:
        model_eff = str(openai_image_model).strip() or model_guess
    else:
        model_eff = model_guess
    size_eff = str(openai_image_size).strip() or size_guess or "1024x1024"

    ok = generated_count >= 1

    return {
        "ok": ok,
        "provider": "openai_image",
        "model": model_eff,
        "size": size_eff,
        "run_id": str(run_id),
        "max_scenes": ms,
        "generated_count": int(generated_count),
        "failed_count": int(failed_count),
        "output_dir": str(out_dir),
        "asset_paths": asset_paths,
        "warnings": warns,
        "smoke_version": "ba32_71_v1",
        "manifest_path": str(man_path) if man_path.is_file() else "",
        "runner_meta_ok": bool(meta.get("ok")),
    }
