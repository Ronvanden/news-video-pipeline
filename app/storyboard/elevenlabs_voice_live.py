"""Live voice executor: ElevenLabs for planned storyboard voice tasks."""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple
from urllib import request as urlrequest
from urllib.error import HTTPError, URLError

from app.storyboard.schema import (
    AssetExecutionResult,
    AssetGenerationPlan,
    AssetGenerationTask,
    AssetTaskExecutionResult,
    ElevenLabsVoiceLiveExecutionRequest,
)


ElevenLabsVoiceRunner = Callable[[str, Path], Tuple[bool, List[str], Dict[str, Any]]]


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


def _voice_tasks(plan: AssetGenerationPlan) -> List[AssetGenerationTask]:
    return [t for t in (plan.tasks or []) if t.asset_type == "voice"]


def _live_output_path(task: AssetGenerationTask, *, output_root: str, run_id: str) -> Path:
    root = Path(output_root or "output")
    rid = _safe_segment(run_id, "storyboard_elevenlabs_voice_v1")
    scene_id = _safe_segment(task.scene_id or f"scene_{int(task.scene_number or 0):03d}", "scene_000")
    return root / "storyboard_runs" / rid / scene_id / "voice.mp3"


def _file_info(path: Path) -> Tuple[bool, Optional[int]]:
    try:
        if not path.is_file():
            return False, None
        return True, path.stat().st_size
    except OSError:
        return False, None


def _task_result(
    task: AssetGenerationTask,
    *,
    status: str,
    dest: Path,
    warnings: List[str],
    blocking_issues: Optional[List[str]] = None,
    output_exists: bool = False,
    file_size_bytes: Optional[int] = None,
    model: str = "eleven_multilingual_v2",
) -> AssetTaskExecutionResult:
    path = str(dest)
    return AssetTaskExecutionResult(
        task_id=task.task_id,
        asset_type=task.asset_type,
        provider_hint="elevenlabs",
        execution_status=status,  # type: ignore[arg-type]
        planned_output_path=path,
        output_path=path,
        output_exists=output_exists,
        file_size_bytes=file_size_bytes,
        scene_id=task.scene_id,
        scene_number=task.scene_number,
        provider="elevenlabs",
        model=model or "eleven_multilingual_v2",
        warnings=_dedupe(warnings),
        blocking_issues=blocking_issues or [],
    )


def run_elevenlabs_voice_live_to_mp3(
    text: str,
    dest_mp3: Path,
    *,
    api_key: str,
    voice_id: str,
    model_id: str = "eleven_multilingual_v2",
    timeout_seconds: float = 120.0,
) -> Tuple[bool, List[str], Dict[str, Any]]:
    """Call ElevenLabs and write an MP3. The caller owns safety gates and path setup."""
    warnings: List[str] = []
    if not _norm(api_key):
        return False, ["elevenlabs_api_key_missing"], {}
    if not _norm(voice_id):
        return False, ["elevenlabs_voice_id_missing"], {}
    body = json.dumps({"text": text, "model_id": model_id or "eleven_multilingual_v2"}).encode("utf-8")
    req = urlrequest.Request(
        f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}",
        data=body,
        headers={
            "xi-api-key": api_key,
            "accept": "audio/mpeg",
            "content-type": "application/json",
        },
        method="POST",
    )
    try:
        with urlrequest.urlopen(req, timeout=float(timeout_seconds)) as resp:
            audio = resp.read()
    except HTTPError as exc:
        return False, [f"elevenlabs_http_{int(exc.code)}"], {}
    except URLError as exc:
        return False, [f"elevenlabs_transport:{type(exc.reason).__name__}"], {}
    except Exception as exc:
        return False, [f"elevenlabs_request_failed:{type(exc).__name__}"], {}
    if not audio:
        return False, ["elevenlabs_empty_audio"], {}
    try:
        dest_mp3.write_bytes(audio)
    except OSError as exc:
        return False, [f"elevenlabs_write_failed:{type(exc).__name__}:path={dest_mp3}"], {}
    return True, warnings + ["elevenlabs_provider:elevenlabs"], {"bytes_written": len(audio)}


def execute_elevenlabs_voice_live_from_asset_plan(
    asset_generation_plan: AssetGenerationPlan,
    *,
    confirm_provider_costs: bool,
    max_live_voice_tasks: int = 10,
    run_id: str = "storyboard_elevenlabs_voice_v1",
    output_root: str = "output",
    elevenlabs_voice_id: str = "",
    elevenlabs_model_id: str = "eleven_multilingual_v2",
    elevenlabs_timeout_seconds: float = 120.0,
    runner: Optional[Callable[..., Tuple[bool, List[str], Dict[str, Any]]]] = None,
) -> AssetExecutionResult:
    """Execute ElevenLabs voice tasks with explicit provider-cost confirmation."""
    if asset_generation_plan.plan_status == "blocked":
        return AssetExecutionResult(
            execution_version="elevenlabs_voice_live_execution_v1",
            execution_status="failed",
            dry_run=False,
            warnings=_dedupe(asset_generation_plan.warnings),
            blocking_issues=_dedupe(asset_generation_plan.blocking_issues + ["elevenlabs_voice_live_blocked_by_asset_plan"]),
        )
    if not confirm_provider_costs:
        return AssetExecutionResult(
            execution_version="elevenlabs_voice_live_execution_v1",
            execution_status="failed",
            dry_run=False,
            warnings=["elevenlabs_voice_live_cost_confirmation_missing"],
            blocking_issues=["confirm_provider_costs_required_for_elevenlabs_voice_live"],
        )
    voice_id = (
        _norm(elevenlabs_voice_id)
        or _norm(os.environ.get("ELEVENLABS_VOICE_ID", ""))
        or _norm(os.environ.get("VOICE_ID", ""))
    )
    if not voice_id:
        return AssetExecutionResult(
            execution_version="elevenlabs_voice_live_execution_v1",
            execution_status="failed",
            dry_run=False,
            warnings=["elevenlabs_voice_id_missing"],
            blocking_issues=["elevenlabs_voice_id_required"],
        )
    api_key = _norm(os.environ.get("ELEVENLABS_API_KEY", ""))
    if not api_key and runner is None:
        return AssetExecutionResult(
            execution_version="elevenlabs_voice_live_execution_v1",
            execution_status="failed",
            dry_run=False,
            warnings=["elevenlabs_api_key_missing"],
            blocking_issues=["elevenlabs_api_key_required"],
        )
    if max_live_voice_tasks < 1:
        return AssetExecutionResult(
            execution_version="elevenlabs_voice_live_execution_v1",
            execution_status="skipped",
            dry_run=False,
            warnings=["elevenlabs_voice_live_max_tasks_zero"],
        )
    tasks = _voice_tasks(asset_generation_plan)
    if not tasks:
        return AssetExecutionResult(
            execution_version="elevenlabs_voice_live_execution_v1",
            execution_status="skipped",
            dry_run=False,
            warnings=["elevenlabs_voice_live_no_voice_tasks"],
        )

    limit = max(0, min(10, int(max_live_voice_tasks)))
    selected = tasks[:limit]
    skipped = tasks[limit:]
    run_voice = runner or run_elevenlabs_voice_live_to_mp3
    task_results: List[AssetTaskExecutionResult] = []
    warnings: List[str] = []
    blockers: List[str] = []
    outputs: List[str] = []
    provider_calls = 0

    for task in selected:
        tw = list(task.warnings or [])
        dest = _live_output_path(task, output_root=output_root, run_id=run_id)
        text = _norm(task.prompt)
        if not text:
            tw.append(f"{task.task_id}_voice_text_missing")
            blockers.append(f"{task.task_id}_execution_failed")
            task_results.append(
                _task_result(
                    task,
                    status="failed",
                    dest=dest,
                    warnings=tw,
                    blocking_issues=[f"{task.task_id}_execution_failed"],
                    model=elevenlabs_model_id,
                )
            )
            warnings.extend(tw)
            continue
        try:
            dest.parent.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            tw.append(f"elevenlabs_voice_live_mkdir_failed:{type(exc).__name__}:path={dest.parent}")
            blockers.append(f"{task.task_id}_execution_failed")
            task_results.append(
                _task_result(task, status="failed", dest=dest, warnings=tw, blocking_issues=[f"{task.task_id}_execution_failed"], model=elevenlabs_model_id)
            )
            warnings.extend(tw)
            continue
        try:
            provider_calls += 1
            ok, runner_warnings, _meta = run_voice(
                text,
                dest,
                api_key=api_key,
                voice_id=voice_id,
                model_id=elevenlabs_model_id or "eleven_multilingual_v2",
                timeout_seconds=float(elevenlabs_timeout_seconds),
            )
        except Exception as exc:
            ok = False
            runner_warnings = [f"elevenlabs_voice_live_write_failed:{type(exc).__name__}:path={dest}"]
        tw.extend(runner_warnings or [])
        output_exists, file_size_bytes = _file_info(dest)
        if ok and not output_exists:
            tw.append(f"elevenlabs_voice_live_output_missing:path={dest}")
            ok = False
        if ok and (file_size_bytes is None or file_size_bytes <= 0):
            tw.append(f"elevenlabs_voice_live_write_failed:EmptyOutput:path={dest}")
            ok = False
        if ok and output_exists:
            outputs.append(str(dest))
        else:
            blockers.append(f"{task.task_id}_execution_failed")
        task_results.append(
            _task_result(
                task,
                status="live_completed" if ok else "failed",
                dest=dest,
                warnings=tw,
                blocking_issues=[f"{task.task_id}_execution_failed"] if not ok else [],
                output_exists=output_exists,
                file_size_bytes=file_size_bytes,
                model=elevenlabs_model_id,
            )
        )
        warnings.extend(tw)

    for task in skipped:
        tw = [f"{task.task_id}_skipped_max_live_voice_tasks_{limit}"]
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
                model=elevenlabs_model_id,
            )
        )
        warnings.extend(tw)

    return AssetExecutionResult(
        execution_version="elevenlabs_voice_live_execution_v1",
        execution_status="failed" if blockers else "live_completed",  # type: ignore[arg-type]
        dry_run=False,
        task_results=task_results,
        warnings=_dedupe(warnings),
        blocking_issues=_dedupe(blockers),
        estimated_provider_calls=provider_calls,
        estimated_outputs=_dedupe(outputs),
    )


def execute_elevenlabs_voice_live_request(req: ElevenLabsVoiceLiveExecutionRequest) -> AssetExecutionResult:
    return execute_elevenlabs_voice_live_from_asset_plan(
        req.asset_generation_plan,
        confirm_provider_costs=req.confirm_provider_costs,
        max_live_voice_tasks=req.max_live_voice_tasks,
        run_id=req.run_id,
        output_root=req.output_root,
        elevenlabs_voice_id=req.elevenlabs_voice_id,
        elevenlabs_model_id=req.elevenlabs_model_id,
        elevenlabs_timeout_seconds=req.elevenlabs_timeout_seconds,
    )
