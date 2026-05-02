"""BA 14.0 — KPI Ingest Contract."""

from app.performance_feedback.kpi_ingest_contract import build_kpi_ingest_contract
from app.prompt_engine.pipeline import build_production_prompt_plan
from app.prompt_engine.schema import PromptPlanRequest


def test_manual_kpi_input_imports_core_metrics():
    plan = build_production_prompt_plan(
        PromptPlanRequest(
            topic="Polizei und Mord",
            kpi_source_type="manual",
            external_kpi_metrics={
                "views": 1000,
                "impressions": 20000,
                "ctr": 0.05,
                "avg_view_duration": 180,
                "watch_time": 3000,
                "subscribers_gained": 12,
                "revenue_optional": 4.5,
            },
        )
    )
    res = plan.kpi_ingest_contract_result
    assert res.ingest_status == "ready"
    assert res.source_type == "manual"
    assert not res.missing_metrics


def test_csv_stub_warns_without_file_io():
    plan = build_production_prompt_plan(PromptPlanRequest(topic="Polizei und Mord"))
    res = build_kpi_ingest_contract(plan, {"views": 100}, source_type="csv")
    assert res.ingest_status == "partial"
    assert res.source_type == "csv"
    assert "csv_import_contract_only_no_file_io" in res.warnings
