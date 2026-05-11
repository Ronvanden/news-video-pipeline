"""Dry-run/stub executor for planned storyboard asset tasks."""

from __future__ import annotations

from typing import Iterable, List

from app.storyboard.schema import (
    AssetExecutionRequest,
    AssetExecutionResult,
    AssetGenerationPlan,
    AssetGenerationTask,
    AssetTaskExecutionResult,
)


_PROMPT_REQUIRED = {"image", "video", "voice", "thumbnail", "subtitle", "render_hint"}
_PROVIDER_CALL_TASKS = {"image", "video", "voice", "thumbnail", "music"}


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


def _task_warnings(task: AssetGenerationTask) -> List[str]:
    warnings = list(task.warnings or [])
    if not _norm(task.provider_hint):
        warnings.append(f"{task.task_id}_provider_hint_missing")
    if task.asset_type in _PROMPT_REQUIRED and not _norm(task.prompt):
        warnings.append(f"{task.task_id}_prompt_missing")
    if not _norm(task.output_path):
        warnings.append(f"{task.task_id}_output_path_missing")
    return _dedupe(warnings)


def _task_status(task: AssetGenerationTask, dry_run: bool, warnings: List[str]) -> str:
    if any(w.endswith("_prompt_missing") for w in warnings) and task.asset_type in {"image", "video", "voice", "thumbnail"}:
        return "failed"
    if any(w.endswith("_output_path_missing") for w in warnings):
        return "failed"
    if any(w.endswith("_provider_hint_missing") for w in warnings) and task.asset_type in _PROVIDER_CALL_TASKS:
        return "skipped"
    return "dry_run" if dry_run else "completed_stub"


def execute_asset_generation_plan_stub(
    asset_generation_plan: AssetGenerationPlan,
    dry_run: bool = True,
) -> AssetExecutionResult:
    """Simulate execution of planned asset tasks without providers, files, or persistence."""
    if asset_generation_plan.plan_status == "blocked":
        blockers = _dedupe(asset_generation_plan.blocking_issues + ["asset_execution_blocked_by_asset_plan"])
        return AssetExecutionResult(
            execution_status="failed",
            dry_run=dry_run,
            warnings=_dedupe(asset_generation_plan.warnings),
            blocking_issues=blockers,
            estimated_provider_calls=0,
            estimated_outputs=[],
        )

    task_results: List[AssetTaskExecutionResult] = []
    warnings: List[str] = list(asset_generation_plan.warnings or [])
    blockers: List[str] = []
    estimated_outputs: List[str] = []
    estimated_provider_calls = 0

    for task in asset_generation_plan.tasks:
        tw = _task_warnings(task)
        status = _task_status(task, dry_run, tw)
        if status == "failed":
            blockers.append(f"{task.task_id}_execution_failed")
        if status in ("dry_run", "completed_stub"):
            if task.asset_type in _PROVIDER_CALL_TASKS:
                estimated_provider_calls += 1
            if _norm(task.output_path):
                estimated_outputs.append(task.output_path)
        warnings.extend(tw)
        task_results.append(
            AssetTaskExecutionResult(
                task_id=task.task_id,
                asset_type=task.asset_type,
                provider_hint=task.provider_hint,
                execution_status=status,  # type: ignore[arg-type]
                planned_output_path=task.output_path,
                warnings=tw,
                blocking_issues=[f"{task.task_id}_execution_failed"] if status == "failed" else [],
            )
        )

    if blockers:
        overall = "failed"
    elif any(t.execution_status == "skipped" for t in task_results):
        overall = "skipped"
    else:
        overall = "dry_run" if dry_run else "completed_stub"

    return AssetExecutionResult(
        execution_status=overall,  # type: ignore[arg-type]
        dry_run=dry_run,
        task_results=task_results,
        warnings=_dedupe(warnings),
        blocking_issues=_dedupe(blockers),
        estimated_provider_calls=estimated_provider_calls,
        estimated_outputs=_dedupe(estimated_outputs),
    )


def execute_asset_generation_plan_stub_request(req: AssetExecutionRequest) -> AssetExecutionResult:
    return execute_asset_generation_plan_stub(req.asset_generation_plan, req.dry_run)
