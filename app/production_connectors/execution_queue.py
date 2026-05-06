"""BA 10.2 — Provider Execution Queue (deterministisch, kein Backend)."""

from __future__ import annotations

import hashlib
from typing import List

from app.production_connectors.registry import get_connector
from app.production_connectors.schema import (
    ExecutionQueueJob,
    ExecutionQueueJobStatus,
    ProviderExecutionQueueResult,
    ProviderExecutionQueueStatus,
)
from app.prompt_engine.schema import ProductionPromptPlan


def _job_id(bundle_id: str, role: str, order: int) -> str:
    seed = f"{bundle_id}|{role}|{order}"
    return f"q_{hashlib.sha256(seed.encode('utf-8')).hexdigest()[:12]}"


def _job_status_from_package(pkg) -> ExecutionQueueJobStatus:
    if pkg.package_status == "blocked":
        return "blocked"
    if pkg.package_status == "incomplete":
        return "invalid"
    return "queued"


def build_provider_execution_queue(plan: ProductionPromptPlan) -> ProviderExecutionQueueResult:
    bundle = plan.provider_export_bundle_result
    if bundle is None:
        return ProviderExecutionQueueResult(
            queue_status="blocked",
            jobs=[],
            total_jobs=0,
            execution_order_summary="Kein Export-Bundle — Queue leer.",
            blocking_reasons=["missing_provider_export_bundle"],
        )

    if bundle.bundle_status == "blocked":
        jobs: List[ExecutionQueueJob] = []
        for role, order in (
            ("thumbnail", 0),
            ("image", 10),
            ("voice", 10),
            ("video", 20),
            ("render", 30),
        ):
            pkg = getattr(bundle.providers, f"{role}_package")
            jobs.append(
                ExecutionQueueJob(
                    job_id=_job_id(bundle.bundle_id or "na", role, order),
                    provider_name=pkg.provider_name,
                    provider_type=pkg.provider_type,
                    queue_status="blocked",
                    dependency_order=order,
                    payload={},
                    warnings=list(pkg.warnings or []),
                )
            )
        return ProviderExecutionQueueResult(
            queue_status="blocked",
            jobs=jobs,
            total_jobs=len(jobs),
            execution_order_summary="thumbnail(0) → image+voice(10) → video(20) → render(30) — Bundle blockiert.",
            blocking_reasons=["bundle_status_blocked"],
        )

    # Thumbnail früh, Image vor Video, Voice parallel zur Image-Welle (gleiche dependency_order), Render zuletzt.
    ordering: List[tuple[str, int]] = [
        ("thumbnail", 0),
        ("image", 10),
        ("voice", 10),
        ("video", 20),
        ("render", 30),
    ]
    jobs = []
    for role, dep in ordering:
        pkg = getattr(bundle.providers, f"{role}_package")
        st = _job_status_from_package(pkg)
        conn = get_connector(pkg.provider_type) or get_connector(pkg.provider_name)
        if conn is None:
            st = "invalid"
        payload = dict(pkg.payload or {})
        jobs.append(
            ExecutionQueueJob(
                job_id=_job_id(bundle.bundle_id or "na", role, dep),
                provider_name=pkg.provider_name,
                provider_type=pkg.provider_type,
                queue_status=st,
                dependency_order=dep,
                payload=payload,
                warnings=list(pkg.warnings or []),
            )
        )

    qstat: ProviderExecutionQueueStatus
    if any(j.queue_status == "blocked" for j in jobs):
        qstat = "blocked"
    elif any(j.queue_status == "invalid" for j in jobs):
        qstat = "partial"
    elif all(j.queue_status == "queued" for j in jobs):
        qstat = "ready"
    else:
        qstat = "partial"

    br: List[str] = []
    if qstat == "blocked":
        br.append("at_least_one_job_blocked")
    elif qstat == "partial":
        br.append("at_least_one_job_invalid_or_incomplete")

    summary = (
        "Reihenfolge: Thumbnail → Image & Voice (parallel) → Video → Render — "
        "deterministische dependency_order-Werte 0/10/20/30."
    )

    return ProviderExecutionQueueResult(
        queue_status=qstat,
        jobs=jobs,
        total_jobs=len(jobs),
        execution_order_summary=summary,
        blocking_reasons=br,
    )
