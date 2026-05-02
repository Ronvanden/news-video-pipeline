"""Leonardo image URL ingest helper tests."""

import json
import subprocess
import sys

from app.production_connectors.leonardo_image_asset_ingest import ingest_leonardo_image_asset


def test_ingest_leonardo_image_url_returns_normalized_asset_and_manifest_record():
    result = ingest_leonardo_image_asset(
        "gen_123",
        "https://cdn.example.test/leonardo/image.png",
    )

    assert result.normalized_asset.provider_name == "Leonardo"
    assert result.normalized_asset.provider_type == "image"
    assert result.normalized_asset.asset_type == "image"
    assert result.normalized_asset.asset_url == "https://cdn.example.test/leonardo/image.png"
    assert result.normalized_asset.normalization_status == "normalized"
    assert result.normalized_asset.metadata["generation_id"] == "gen_123"
    assert result.manifest_record.provider_name == "Leonardo"
    assert result.manifest_record.asset_type == "image"
    assert result.manifest_record.asset_url == "https://cdn.example.test/leonardo/image.png"
    assert result.manifest_record.asset_id.startswith("asset_")
    assert result.manifest_record.source_status == "manual_ingested"
    assert result.manifest_record.scene_index == 0
    assert result.manifest_record.metadata["generation_id"] == "gen_123"
    assert result.manifest_status == "partial"
    assert result.warnings == []


def test_ingest_invalid_url_blocks_manifest_record_safely():
    result = ingest_leonardo_image_asset("gen_123", "not-a-url")

    assert result.normalized_asset.normalization_status == "partial"
    assert result.normalized_asset.asset_url is None
    assert result.manifest_record.asset_url is None
    assert result.manifest_record.source_status == "invalid"
    assert result.manifest_status == "blocked"
    assert result.warnings == ["image_url_invalid", "no_url_or_local_path"]


def test_ingest_missing_generation_id_warns_without_secret_or_network_dependency():
    result = ingest_leonardo_image_asset("", "https://cdn.example.test/leonardo/image.png")

    assert result.normalized_asset.asset_url == "https://cdn.example.test/leonardo/image.png"
    assert result.manifest_record.metadata["generation_id"] == ""
    assert result.warnings == ["generation_id_missing"]


def test_cli_outputs_safe_summary_only():
    completed = subprocess.run(
        [
            sys.executable,
            "scripts/ingest_leonardo_image_asset.py",
            "gen_cli_123",
            "https://cdn.example.test/leonardo/cli.png",
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    payload = json.loads(completed.stdout)
    assert sorted(payload.keys()) == [
        "asset_type",
        "asset_url",
        "manifest_asset_id",
        "manifest_status",
        "provider_name",
        "warnings",
    ]
    assert payload["asset_type"] == "image"
    assert payload["provider_name"] == "Leonardo"
    assert payload["asset_url"] == "https://cdn.example.test/leonardo/cli.png"
    assert payload["manifest_asset_id"].startswith("asset_")
    assert payload["manifest_status"] == "partial"
    assert payload["warnings"] == []
