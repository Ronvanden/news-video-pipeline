"""First live asset executor: OpenAI Image for one planned image task."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Callable, Iterable, List, Tuple, Dict, Any, Optional

from app.production_connectors.openai_image_connector import run_openai_image_live_to_png
from app.storyboard.schema import (
    AssetExecutionResult,
    AssetGenerationPlan,
    AssetGenerationTask,
    AssetTaskExecutionResult,
    OpenAIImageLiveExecutionRequest,
)


OpenAIImageRunner = Callable[[str, Path], Tuple[bool, List[str], Dict[str, Any]]]


def _norm(s: str) -> str:
    return " ".join(str(s or "").split()).strip()


def _dedupe(items: Iterable[str]) -> List[str]:
    out: List[str] = []
    seen: set[str] = set()
    for item in items:
        v = _norm(item)
        if not v or v in seen:
            continue
        seen.add(v)
        out.append(v)
    return out


def _safe_segment(s: str, default: str) -> str:
    raw = _norm(s) or default
    safe = re.sub(r"[^A-Za-z0-9_.-]+", "_", raw).strip("._-")
    return safe[:96] or default


def _live_output_path(task: AssetGenerationTask, *, output_root: str, run_id: str) -> Path:
    root = Path(output_root or "output")
    rid = _safe_segment(run_id, "storyboard_openai_image_v1")
    scene_id = _safe_segment(task.scene_id or f"scene_{int(task.scene_number or 0):03d}", "scene_000")
    return root / "storyboard_runs" / rid / scene_id / "image.png"


def _image_tasks(plan: AssetGenerationPlan) -> List[AssetGenerationTask]:
    return [t for t in (plan.tasks or []) if t.asset_type == "image"]


def execute_openai_image_live_from_asset_plan(
    asset_generation_plan: AssetGenerationPlan,
    *,
    confirm_provider_costs: bool,
    max_live_image_tasks: int = 1,
    run_id: str = "storyboard_openai_image_v1",
    output_root: str = "output",
    openai_image_model: str = "gpt-image-2",
    openai_image_size: str = "1024x1024",
    openai_image_timeout_seconds: float = 120.0,
    runner: Optional[Callable[..., Tuple[bool, List[str], Dict[str, Any]]]] = None,
) -> AssetExecutionResult:
    """Execute at most one OpenAI image task. This is the first intentionally live path."""
    run_image = runner or run_openai_image_live_to_png
    if asset_generation_plan.plan_status == "blocked":
        return AssetExecutionResult(
            execution_version="openai_image_live_execution_v1",
            execution_status="failed",
            dry_run=False,
            warnings=_dedupe(asset_generation_plan.warnings),
            blocking_issues=_dedupe(asset_generation_plan.blocking_issues + ["openai_image_live_blocked_by_asset_plan"]),
        )
    if not confirm_provider_costs:
        return AssetExecutionResult(
            execution_version="openai_image_live_execution_v1",
            execution_status="failed",
            dry_run=False,
            blocking_issues=["confirm_provider_costs_required_for_openai_image_live"],
            warnings=["openai_image_live_cost_confirmation_missing"],
        )
    if max_live_image_tasks < 1:
        return AssetExecutionResult(
            execution_version="openai_image_live_execution_v1",
            execution_status="skipped",
            dry_run=False,
            warnings=["openai_image_live_max_tasks_zero"],
        )

    tasks = _image_tasks(asset_generation_plan)
    if not tasks:
        return AssetExecutionResult(
            execution_version="openai_image_live_execution_v1",
            execution_status="skipped",
            dry_run=False,
            warnings=["openai_image_live_no_image_tasks"],
        )

    selected = tasks[:1]
    skipped = tasks[1:]
    task_results: List[AssetTaskExecutionResult] = []
    warnings: List[str] = []
    blockers: List[str] = []
    outputs: List[str] = []

    for task in selected:
        tw = list(task.warnings or [])
        prompt = _norm(task.prompt)
        if not prompt:
            tw.append(f"{task.task_id}_prompt_missing")
            blockers.append(f"{task.task_id}_execution_failed")
            task_results.append(
                AssetTaskExecutionResult(
                    task_id=task.task_id,
                    asset_type=task.asset_type,
                    provider_hint="openai_image",
                    execution_status="failed",
                    planned_output_path="",
                    warnings=_dedupe(tw),
                    blocking_issues=[f"{task.task_id}_execution_failed"],
                )
            )
            warnings.extend(tw)
            continue

        dest = _live_output_path(task, output_root=output_root, run_id=run_id)
        ok, runner_warnings, _meta = run_image(
            prompt,
            dest,
            size=openai_image_size or "1024x1024",
            model=openai_image_model or "gpt-image-2",
            timeout_seconds=float(openai_image_timeout_seconds),
        )
        tw.extend(runner_warnings or [])
        status = "live_completed" if ok else "failed"
        if ok:
            outputs.append(str(dest))
        else:
            blockers.append(f"{task.task_id}_execution_failed")
        task_results.append(
            AssetTaskExecutionResult(
                task_id=task.task_id,
                asset_type=task.asset_type,
                provider_hint="openai_image",
                execution_status=status,  # type: ignore[arg-type]
                planned_output_path=str(dest),
                warnings=_dedupe(tw),
                blocking_issues=[f"{task.task_id}_execution_failed"] if not ok else [],
            )
        )
        warnings.extend(tw)

    for task in skipped:
        tw = [f"{task.task_id}_skipped_max_live_image_tasks_1"]
        task_results.append(
            AssetTaskExecutionResult(
                task_id=task.task_id,
                asset_type=task.asset_type,
                provider_hint="openai_image",
                execution_status="skipped",
                planned_output_path=str(_live_output_path(task, output_root=output_root, run_id=run_id)),
                warnings=tw,
            )
        )
        warnings.extend(tw)

    overall = "failed" if blockers else "live_completed"
    return AssetExecutionResult(
        execution_version="openai_image_live_execution_v1",
        execution_status=overall,  # type: ignore[arg-type]
        dry_run=False,
        task_results=task_results,
        warnings=_dedupe(warnings),
        blocking_issues=_dedupe(blockers),
        estimated_provider_calls=len(selected),
        estimated_outputs=_dedupe(outputs),
    )


def execute_openai_image_live_request(req: OpenAIImageLiveExecutionRequest) -> AssetExecutionResult:
    return execute_openai_image_live_from_asset_plan(
        req.asset_generation_plan,
        confirm_provider_costs=req.confirm_provider_costs,
        max_live_image_tasks=req.max_live_image_tasks,
        run_id=req.run_id,
        output_root=req.output_root,
        openai_image_model=req.openai_image_model,
        openai_image_size=req.openai_image_size,
        openai_image_timeout_seconds=req.openai_image_timeout_seconds,
    )
