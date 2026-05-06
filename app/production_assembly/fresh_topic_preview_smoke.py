"""BA 30.2 — Fresh topic / URL / script.json → placeholder asset_manifest → preview smoke (no publishing)."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from app.utils import build_script_response_from_extracted_text, extract_text_from_url

_FRESH_VERSION = "ba30_2_v1"


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _load_module(name: str, rel_path: str):
    root = _repo_root()
    p = root / rel_path
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, p)
    assert spec and spec.loader
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


def _build_script_for_fresh_input(
    *,
    run_id: str,
    topic: Optional[str],
    url: Optional[str],
    script_json: Optional[Path],
    duration_target_seconds: int,
) -> Tuple[Dict[str, Any], List[str], List[str]]:
    warnings: List[str] = []
    blocking: List[str] = []
    dm = max(1, int(round(max(5, int(duration_target_seconds)) / 60.0)))

    if script_json is not None:
        ba = _load_module("run_url_to_final_mp4_ba302", "scripts/run_url_to_final_mp4.py")
        raw = json.loads(Path(script_json).read_text(encoding="utf-8"))
        script = ba._tolerant_script(raw)
        warnings.append("ba302_fresh_input:script_json")
        return script, warnings, blocking

    if url:
        text, ext_warns = extract_text_from_url(url.strip())
        warnings.extend(ext_warns)
        if not (text or "").strip():
            blocking.append("url_extraction_empty")
            return {}, warnings, blocking
        title, hook, chapters, full_script, sources, gen_warns = build_script_response_from_extracted_text(
            extracted_text=text,
            source_url=url.strip(),
            target_language="de",
            duration_minutes=dm,
            extraction_warnings=[],
            extra_warnings=[f"ba302_fresh_preview_smoke:{run_id}"],
        )
        warnings.extend(gen_warns)
        warnings.append("ba302_fresh_input:url")
        return (
            {
                "title": title,
                "hook": hook,
                "chapters": chapters,
                "full_script": full_script,
                "sources": sources,
                "warnings": list(warnings),
            },
            warnings,
            blocking,
        )

    if topic and str(topic).strip():
        t = str(topic).strip()
        title, hook, chapters, full_script, sources, gen_warns = build_script_response_from_extracted_text(
            extracted_text=t,
            source_url="manual_topic:ba30_2_fresh_preview_smoke",
            target_language="de",
            duration_minutes=dm,
            extraction_warnings=[],
            extra_warnings=[f"ba302_fresh_topic_only:{run_id}"],
        )
        warnings.extend(gen_warns)
        warnings.append("ba302_fresh_input:topic")
        return (
            {
                "title": title,
                "hook": hook,
                "chapters": chapters,
                "full_script": full_script,
                "sources": sources,
                "warnings": list(warnings),
            },
            warnings,
            blocking,
        )

    blocking.append("ba302_no_input:provide_topic_url_or_script_json")
    return {}, warnings, blocking


def run_fresh_topic_preview_smoke(
    *,
    run_id: str,
    output_root: Path,
    topic: Optional[str] = None,
    url: Optional[str] = None,
    script_json: Optional[Path] = None,
    duration_target_seconds: int = 45,
    provider: str = "auto",
    dry_run: bool = False,
    max_scenes: int = 5,
    asset_dir: Optional[Path] = None,
    asset_runner_mode: str = "placeholder",
    max_live_assets: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Build script → scene_asset_pack → placeholder (or configured) asset_runner → optional ``execute_preview_smoke_auto``.

    ``asset_runner_mode``: ``placeholder`` (default, no live provider) or ``live`` (requires keys/env; operator responsibility).

    ``max_live_assets``: optional cap on Leonardo live generations (forwarded as ``max_assets_live``); unset keeps Asset Runner default (3).
    """
    from app.production_assembly.preview_smoke_auto import execute_preview_smoke_auto

    rid = str(run_id).strip()
    out_root = Path(output_root).resolve()
    out_root.mkdir(parents=True, exist_ok=True)
    fresh_root = out_root / "fresh_topic_preview" / rid
    fresh_root.mkdir(parents=True, exist_ok=True)

    result: Dict[str, Any] = {
        "fresh_topic_preview_version": _FRESH_VERSION,
        "run_id": rid,
        "ok": False,
        "dry_run": bool(dry_run),
        "fresh_work_dir": str(fresh_root.resolve()),
        "script_path": "",
        "scene_asset_pack_path": "",
        "asset_manifest_path": "",
        "preview_smoke_summary_path": "",
        "preview_smoke_exit_code": None,
        "warnings": [],
        "blocking_reasons": [],
    }

    script, swarns, blocking = _build_script_for_fresh_input(
        run_id=rid,
        topic=topic,
        url=url,
        script_json=script_json,
        duration_target_seconds=int(duration_target_seconds),
    )
    result["warnings"].extend(swarns)
    if blocking:
        result["blocking_reasons"].extend(blocking)
        return result

    script_path = fresh_root / "script.json"
    script_path.write_text(json.dumps(script, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    result["script_path"] = str(script_path.resolve())

    ba = _load_module("run_url_to_final_mp4_ba302", "scripts/run_url_to_final_mp4.py")
    ar = _load_module("run_asset_runner_ba302", "scripts/run_asset_runner.py")

    videos, images = ba._collect_assets(Path(asset_dir).resolve() if asset_dir else None)
    try:
        scene_rows = ba._build_scene_rows_from_script(
            script,
            max_scenes=int(max_scenes),
            total_duration_seconds=int(duration_target_seconds),
        )
    except ValueError as e:
        result["blocking_reasons"].append(f"scene_plan_failed:{e}")
        return result

    n_scenes = len(scene_rows)
    rel_videos, img_overrides, assign_warns = ba._assign_media(n_scenes, videos, images, fresh_root)
    result["warnings"].extend(assign_warns)

    pack = ba._build_scene_asset_pack(scene_rows, script=script, rel_videos=rel_videos, pack_parent=fresh_root)
    pack_path = fresh_root / "scene_asset_pack.json"
    pack_path.write_text(json.dumps(pack, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    result["scene_asset_pack_path"] = str(pack_path.resolve())

    mode_l = (asset_runner_mode or "placeholder").strip().lower()
    if mode_l not in ("placeholder", "live"):
        mode_l = "placeholder"
        result["warnings"].append("ba302_invalid_asset_runner_mode_fallback_placeholder")

    runner_kw: Dict[str, Any] = dict(
        pack_path=pack_path,
        out_root=fresh_root,
        run_id=rid,
        mode=mode_l,
    )
    if max_live_assets is not None:
        runner_kw["max_assets_live"] = int(max_live_assets)

    try:
        ameta = ar.run_local_asset_runner(**runner_kw)
    except (OSError, ValueError, FileNotFoundError, json.JSONDecodeError) as e:
        result["blocking_reasons"].append(f"asset_runner_failed:{type(e).__name__}")
        result["warnings"].append(str(e)[:300])
        return result

    result["warnings"].extend(list(ameta.get("warnings") or []))
    if not ameta.get("ok"):
        result["blocking_reasons"].append("asset_runner_not_ok")
        return result

    manifest_path = Path(str(ameta["manifest_path"]))
    result["asset_manifest_path"] = str(manifest_path.resolve())
    gen_dir = manifest_path.parent
    ba._apply_post_runner_images(gen_dir, manifest_path, img_overrides)

    if dry_run:
        result["ok"] = True
        result["warnings"].append("ba302_dry_run:no_preview_smoke_executed")
        return result

    summ, code = execute_preview_smoke_auto(
        run_id=rid,
        output_root=out_root,
        asset_manifest=manifest_path,
        duration_target_seconds=int(duration_target_seconds),
        provider=str(provider),
        max_timeline_scenes=int(max_scenes),
    )
    result["preview_smoke_exit_code"] = int(code)
    result["preview_smoke_summary"] = summ
    sp = out_root / f"preview_smoke_auto_summary_{rid}.json"
    if sp.is_file():
        result["preview_smoke_summary_path"] = str(sp.resolve())
    result["ok"] = bool(summ.get("ok"))
    if not result["ok"]:
        result["blocking_reasons"].extend([str(x) for x in (summ.get("operator_blocking_reasons") or []) if str(x or "").strip()])
    return result
