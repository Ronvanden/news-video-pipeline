"""BA 10.8 — Provider-Job-Runner Mock (keine Netzwerk-Calls)."""

from __future__ import annotations

from datetime import datetime, timezone

from app.production_connectors.result_store_schema import (
    ProviderExecutionRecord,
    ProviderExecutionRecordStatus,
)
from app.production_connectors.schema import (
    JobRunnerFinalStatus,
    JobRunnerJobOutcome,
    ProviderJobRunnerMockResult,
)
def _utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _map_final(queue_status: str) -> JobRunnerFinalStatus:
    if queue_status == "queued":
        return "simulated_success"
    if queue_status == "blocked":
        return "blocked"
    if queue_status == "invalid":
        return "skipped"
    return "skipped"


def simulate_provider_job_run(plan: object) -> ProviderJobRunnerMockResult:
    queue = plan.provider_execution_queue_result
    if queue is None or queue.queue_status == "blocked" or not queue.jobs:
        return ProviderJobRunnerMockResult(
            runner_status="blocked",
            job_outcomes=[],
            connector_execution_records=[],
            summary="Keine ausführbare Queue — Runner blockiert.",
        )

    outcomes: list[JobRunnerJobOutcome] = []
    records: list[ProviderExecutionRecord] = []
    for j in queue.jobs:
        fin = _map_final(j.queue_status)
        outcomes.append(
            JobRunnerJobOutcome(
                job_id=j.job_id,
                provider_name=j.provider_name,
                provider_type=j.provider_type,
                final_status=fin,
                notes=f"mock_from_queue_status:{j.queue_status}",
            )
        )
        ex_stat: ProviderExecutionRecordStatus
        if fin == "simulated_success":
            ex_stat = "simulated_success"
        elif fin == "blocked":
            ex_stat = "blocked"
        elif fin == "skipped":
            ex_stat = "skipped"
        else:
            ex_stat = "pending"
        records.append(
            ProviderExecutionRecord(
                execution_id=f"ex_{j.job_id}",
                provider_name=j.provider_name,
                provider_type=j.provider_type,
                request_snapshot=dict(j.payload or {}),
                response_snapshot={"mock": True, "final_status": fin},
                execution_mode="dry_run",
                execution_status=ex_stat,
                created_at=_utc_iso(),
                warnings=list(j.warnings or []),
            )
        )

    if all(o.final_status == "simulated_success" for o in outcomes):
        rstat = "complete"
    elif any(o.final_status == "blocked" for o in outcomes):
        rstat = "blocked"
    else:
        rstat = "partial"

    return ProviderJobRunnerMockResult(
        runner_status=rstat,
        job_outcomes=outcomes,
        connector_execution_records=records,
        summary=f"Mock abgeschlossen: {len(outcomes)} Jobs, Status {rstat}.",
    )
