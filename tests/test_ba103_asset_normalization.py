"""BA 10.3 — Asset return normalization."""

from app.production_connectors.asset_normalization import normalize_provider_asset_result


def test_invalid_raw_none():
    r = normalize_provider_asset_result("Leonardo", None)
    assert r.normalization_status == "invalid"
    assert r.warnings


def test_invalid_non_dict():
    r = normalize_provider_asset_result("Kling", "not-json")
    assert r.normalization_status == "invalid"


def test_normalized_with_url():
    r = normalize_provider_asset_result(
        "Leonardo",
        {"url": "https://cdn.example.com/a.png", "width": 1024},
    )
    assert r.normalization_status == "normalized"
    assert r.asset_url == "https://cdn.example.com/a.png"
    assert r.asset_type == "image"
    assert "width" in r.metadata or r.metadata.get("width") == 1024


def test_partial_without_url():
    r = normalize_provider_asset_result("Kling", {"job_id": "x"})
    assert r.normalization_status == "partial"
