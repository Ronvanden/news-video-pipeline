"""BA 10.7 — Result store schema."""

from app.production_connectors.result_store_schema import ProductionRunRecord, ProviderExecutionRecord


def test_provider_execution_record_fields():
    r = ProviderExecutionRecord(
        execution_id="e1",
        provider_name="Leonardo",
        provider_type="image",
        request_snapshot={"a": 1},
        response_snapshot={"mock": True},
        execution_mode="dry_run",
        execution_status="simulated_success",
        created_at="2026-01-01T00:00:00Z",
        warnings=[],
    )
    assert r.execution_id == "e1"


def test_production_run_record_aggregate():
    run = ProductionRunRecord(
        run_id="run-1",
        run_status="simulated",
        connector_records=[],
        estimated_cost=12.0,
        total_jobs=5,
        summary="ok",
    )
    assert run.total_jobs == 5
