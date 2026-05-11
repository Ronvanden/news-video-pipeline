"""Live motion executor: Runway image-to-video for planned storyboard video tasks."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple

from app.production_connectors.runway_video_connector import run_runway_motion_clip_live
from app.storyboard.schema import (
    AssetExecutionResult,
    AssetGenerationPlan,
    AssetGenerationTask,
    AssetTaskExecutionResult,
    RunwayMotionLiveExecutionRequest,
)


RunwayMotionRunner = Callable[..., Any]


def _norm(s: str) -> str:
    return " ".join(str(s or "").split()).strip()


def _dedupe(items: Iterable[str]) -> List[str]:
    out: List[str] = []
    seen: set[str] = set()
    for item in items:
        value = _norm(item)
        if not value or value in seen:
            continue
        seen.add(value)
        out.append(value)
    return out


def _safe_segment(s: str, default: str) -> str:
    raw = _norm(s) or default
    safe = re.sub(r"[^A-Za-z0-9_.-]+", "_", raw).strip("._-")
    return safe[:96] or default


def _video_tasks(plan: AssetGenerationPlan) -> List[AssetGenerationTask]:
    return [t for t in (plan.tasks or []) if t.asset_type == "video"]


def _live_output_path(task: AssetGenerationTask, *, output_root: str, run_id: str) -> Path:
    root = Path(output_root or "output")
    rid = _safe_segment(run_id, "storyboard_runway_motion_v1")
    scene_id = _safe_segment(task.scene_id or f"scene_{int(task.scene_number or 0):03d}", "scene_000")
    return root / "storyboard_runs" / rid / scene_id / "motion.mp4"


def _file_info(path: Path) -> Tuple[bool, Optional[int]]:
    try:
        if not path.is_file():
            return False, None
        return True, path.stat().st_size
    except OSError:
        return False, None


def _image_paths_by_scene(image_execution_result: Optional[AssetExecutionResult]) -> Dict[int, str]:
    out: Dict[int, str] = {}
    if not image_execution_result:
        return out
    for result in image_execution_result.task_results or []:
        if result.scene_number is None or result.asset_type != "image":
            continue
        if result.execution_status == "live_completed" and result.output_exists:
            path = _norm(result.output_path or result.planned_output_path)
            if path:
                out[int(result.scene_number)] = path
    return out


def _task_result(
    task: AssetGenerationTask,
    *,
    status: str,
    dest: Path,
    warnings: List[str],
    blocking_issues: Optional[List[str]] = None,
    output_exists: bool = False,
    file_size_bytes: Optional[int] = None,
) -> AssetTaskExecutionResult:
    path = str(dest)
    return AssetTaskExecutionResult(
        task_id=task.task_id,
        asset_type=task.asset_type,
        provider_hint="runway",
        execution_status=status,  # type: ignore[arg-type]
        planned_output_path=path,
        output_path=path,
        output_exists=output_exists,
        file_size_bytes=file_size_bytes,
        scene_id=task.scene_id,
        scene_number=task.scene_number,
        provider="runway",
        model="runway_image_to_video",
        warnings=_dedupe(warnings),
        blocking_issues=blocking_issues or [],
    )


def execute_runway_motion_live_from_asset_plan(
    asset_generation_plan: AssetGenerationPlan,
    *,
    image_execution_result: Optional[AssetExecutionResult] = None,
    confirm_provider_costs: bool,
    max_live_motion_tasks: int = 1,
    run_id: str = "storyboard_runway_motion_v1",
    output_root: str = "output",
    runway_duration_seconds: int = 5,
    runner: Optional[RunwayMotionRunner] = None,
) -> AssetExecutionResult:
    """Execute capped Runway motion tasks with explicit provider-cost confirmation."""

    if asset_generation_plan.plan_status == "blocked":
        return AssetExecutionResult(
            execution_version="runway_motion_live_execution_v1",
            execution_status="failed",
            dry_run=False,
            warnings=_dedupe(asset_generation_plan.warnings),
            blocking_issues=_dedupe(asset_generation_plan.blocking_issues + ["runway_motion_live_blocked_by_asset_plan"]),
        )
    if not confirm_provider_costs:
        return AssetExecutionResult(
            execution_version="runway_motion_live_execution_v1",
            execution_status="failed",
            dry_run=False,
            warnings=["runway_motion_live_cost_confirmation_missing"],
            blocking_issues=["confirm_provider_costs_required_for_runway_motion_live"],
        )
    if max_live_motion_tasks < 1:
        return AssetExecutionResult(
            execution_version="runway_motion_live_execution_v1",
            execution_status="skipped",
            dry_run=False,
            warnings=["runway_motion_live_max_tasks_zero"],
        )

    tasks = _video_tasks(asset_generation_plan)
    if not tasks:
        return AssetExecutionResult(
            execution_version="runway_motion_live_execution_v1",
            execution_status="skipped",
            dry_run=False,
            warnings=["runway_motion_live_no_video_tasks"],
        )

    image_paths = _image_paths_by_scene(image_execution_result)
    limit = max(0, min(2, int(max_live_motion_tasks)))
    selected = tasks[:limit]
    skipped = tasks[limit:]
    task_results: List[AssetTaskExecutionResult] = []
    warnings: List[str] = []
    blockers: List[str] = []
    outputs: List[str] = []
    provider_calls = 0
    run_motion = runner or run_runway_motion_clip_live

    for task in selected:
        tw = list(task.warnings or [])
        dest = _live_output_path(task, output_root=output_root, run_id=run_id)
        prompt = _norm(task.prompt)
        image_path = image_paths.get(int(task.scene_number or 0), "")
        if not image_path:
            tw.append(f"{task.task_id}_runway_source_image_missing")
            blockers.append(f"{task.task_id}_execution_failed")
            task_results.append(
                _task_result(task, status="failed", dest=dest, warnings=tw, blocking_issues=[f"{task.task_id}_execution_failed"])
            )
            warnings.extend(tw)
            continue
        if not prompt:
            prompt = "cinematic documentary motion, realistic, grounded, natural camera movement"
            tw.append(f"{task.task_id}_runway_prompt_defaulted")
        try:
            provider_calls += 1
            result = run_motion(
                prompt=prompt,
                duration_seconds=max(5, min(10, int(runway_duration_seconds))),
                image_path=Path(image_path),
                output_path=dest,
                run_id=f"{_safe_segment(run_id, 'storyboard_runway_motion_v1')}_{task.task_id}",
            )
            ok = bool(getattr(result, "ok", False))
            runner_warnings = list(getattr(result, "warnings", []) or [])
        except Exception as exc:
            ok = False
            runner_warnings = [f"runway_motion_live_failed:{type(exc).__name__}:path={dest}"]
        tw.extend(str(w) for w in runner_warnings if str(w or "").strip())
        output_exists, file_size_bytes = _file_info(dest)
        if ok and not output_exists:
            tw.append(f"runway_motion_live_output_missing:path={dest}")
            ok = False
        if ok and (file_size_bytes is None or file_size_bytes <= 0):
            tw.append(f"runway_motion_live_empty_output:path={dest}")
            ok = False
        status = "live_completed" if ok else "failed"
        if ok and output_exists:
            outputs.append(str(dest))
        else:
            blockers.append(f"{task.task_id}_execution_failed")
        task_results.append(
            _task_result(
                task,
                status=status,
                dest=dest,
                warnings=tw,
                blocking_issues=[f"{task.task_id}_execution_failed"] if not ok else [],
                output_exists=output_exists,
                file_size_bytes=file_size_bytes,
            )
        )
        warnings.extend(tw)

    for task in skipped:
        tw = [f"{task.task_id}_skipped_max_live_motion_tasks_{limit}"]
        dest = _live_output_path(task, output_root=output_root, run_id=run_id)
        output_exists, file_size_bytes = _file_info(dest)
        task_results.append(
            _task_result(
                task,
                status="skipped",
                dest=dest,
                warnings=tw,
                output_exists=output_exists,
                file_size_bytes=file_size_bytes,
            )
        )
        warnings.extend(tw)

    execution_status = "live_completed" if outputs and not blockers else ("failed" if blockers else "skipped")
    return AssetExecutionResult(
        execution_version="runway_motion_live_execution_v1",
        execution_status=execution_status,  # type: ignore[arg-type]
        dry_run=False,
        task_results=task_results,
        warnings=_dedupe(warnings),
        blocking_issues=_dedupe(blockers),
        estimated_provider_calls=provider_calls,
        estimated_outputs=outputs,
    )


def execute_runway_motion_live_request(req: RunwayMotionLiveExecutionRequest) -> AssetExecutionResult:
    """Request wrapper for live Runway motion execution."""

    return execute_runway_motion_live_from_asset_plan(
        req.asset_generation_plan,
        image_execution_result=req.image_execution_result,
        confirm_provider_costs=req.confirm_provider_costs,
        max_live_motion_tasks=req.max_live_motion_tasks,
        run_id=req.run_id,
        output_root=req.output_root,
        runway_duration_seconds=req.runway_duration_seconds,
    )
