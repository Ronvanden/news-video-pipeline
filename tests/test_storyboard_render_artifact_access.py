from __future__ import annotations

import shutil
from pathlib import Path

from fastapi.testclient import TestClient

from app.founder_dashboard.storyboard_render_artifact_access import (
    resolve_storyboard_render_artifact_path,
    storyboard_render_artifact_media_type,
)
from app.main import app


def test_resolver_allows_storyboard_render_video_under_run(tmp_path: Path) -> None:
    root = tmp_path / "output"
    video = root / "storyboard_runs" / "run_001" / "render" / "final_video.mp4"
    video.parent.mkdir(parents=True)
    video.write_bytes(b"\0\0\0 ftypisom")

    resolved, reason = resolve_storyboard_render_artifact_path(root, "run_001", "render/final_video.mp4")

    assert reason == "ok"
    assert resolved == video.resolve()
    assert storyboard_render_artifact_media_type(resolved) == "video/mp4"


def test_resolver_blocks_path_traversal(tmp_path: Path) -> None:
    root = tmp_path / "output"
    outside = root / "secret.json"
    outside.parent.mkdir(parents=True)
    outside.write_text("{}", encoding="utf-8")

    resolved, reason = resolve_storyboard_render_artifact_path(root, "run_001", "../secret.json")

    assert resolved is None
    assert reason == "forbidden"


def test_dashboard_storyboard_render_file_route_serves_mp4() -> None:
    output_run = Path(__file__).resolve().parents[1] / "output" / "storyboard_runs" / "pytest_storyboard_artifact_access"
    try:
        video = output_run / "render" / "final_video.mp4"
        video.parent.mkdir(parents=True, exist_ok=True)
        video.write_bytes(b"\0\0\0 ftypisom")

        client = TestClient(app)
        response = client.get(
            "/founder/dashboard/storyboard-render/file/pytest_storyboard_artifact_access/render/final_video.mp4"
        )

        assert response.status_code == 200
        assert "video/mp4" in (response.headers.get("content-type") or "")
        assert response.content
    finally:
        shutil.rmtree(output_run, ignore_errors=True)
