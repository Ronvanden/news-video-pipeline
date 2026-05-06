"""BA 14.1 — KPI Normalization."""

from app.performance_feedback.kpi_normalization import normalize_kpi_metrics


def test_kpi_normalization_derives_ctr_and_rpm():
    res = normalize_kpi_metrics(
        {
            "views": 10000,
            "impressions": 200000,
            "avg_view_duration": 240,
            "watch_time": 40000,
            "subscribers_gained": 50,
            "revenue_optional": 30,
        }
    )
    assert res.normalized_status == "ready"
    assert res.normalized_ctr == 0.05
    assert res.normalized_retention > 0
    assert res.normalized_rpm == 3.0
    assert res.normalized_growth > 0


def test_kpi_normalization_handles_empty_data():
    res = normalize_kpi_metrics({})
    assert res.normalized_status == "insufficient_data"
    assert "no_normalizable_kpi_metrics" in res.warnings
