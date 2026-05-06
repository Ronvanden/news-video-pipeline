from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.runway_image_to_video_smoke import (
    EXIT_BLOCKED,
    EXIT_FAILED,
    EXIT_INTERRUPTED,
    EXIT_INVALID,
    EXIT_OK,
    EXIT_TIMEOUT,
    RESULT_FILENAME,
    RESULT_SCHEMA,
    run_runway_image_to_video_smoke,
)


@pytest.fixture
def tiny_png(tmp_path: Path) -> Path:
    p = tmp_path / "in.png"
    p.write_bytes(
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
        b"\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x05"
        b"\x18\xd8N\x12\x00\x00\x00\x00IEND\xaeB`\x82"
    )
    return p


def test_runway_smoke_blocked_without_api_key(tmp_path: Path, tiny_png: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("RUNWAY_API_KEY", raising=False)
    out = tmp_path / "output"
    res = run_runway_image_to_video_smoke(
        image_path=tiny_png,
        prompt="test prompt",
        run_id="rid1",
        out_root=out,
        duration_seconds=5,
    )
    assert res["ok"] is False
    assert res["status"] == "blocked"
    assert res["exit_code"] == EXIT_BLOCKED
    assert "runway_api_key_missing" in res["blocking_reasons"]
    assert res["schema_version"] == RESULT_SCHEMA
    rfile = out / "runway_smoke_rid1" / RESULT_FILENAME
    assert rfile.is_file()
    disk = json.loads(rfile.read_text(encoding="utf-8"))
    assert "exit_code" not in disk
    assert disk["status"] == "blocked"


def test_runway_smoke_key_not_in_result_or_logs(tmp_path: Path, tiny_png: Path, capsys: pytest.CaptureFixture, monkeypatch: pytest.MonkeyPatch):
    secret = "runway_test_secret_value_xyz"
    monkeypatch.setenv("RUNWAY_API_KEY", secret)

    def post_ok(url, headers, body):
        assert secret not in url
        assert secret not in json.dumps(body)
        auth = headers.get("Authorization", "")
        assert auth.startswith("Bearer ")
        assert secret in auth  # Header muss Key tragen; darf nicht in Logs/Result landen
        return 200, {"id": "task-abc"}

    poll = {"n": 0}

    def get_ok(url, headers):
        assert secret not in url
        assert headers.get("Authorization", "").startswith("Bearer ")
        poll["n"] += 1
        if poll["n"] < 2:
            return 200, {"status": "PENDING"}
        return 200, {"status": "SUCCEEDED", "output": ["https://cdn.example.test/out.mp4"]}

    def save_ok(url, dest: Path):
        assert url == "https://cdn.example.test/out.mp4"
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(b"\x00\x00\x00\x18ftypmp42")
        return True, []

    res = run_runway_image_to_video_smoke(
        image_path=tiny_png,
        prompt="cinematic",
        run_id="rid2",
        out_root=tmp_path / "o",
        duration_seconds=5,
        post_json=post_ok,
        get_json=get_ok,
        save_video=save_ok,
    )
    assert res["ok"] is True
    assert res["exit_code"] == EXIT_OK
    assert res["metadata"].get("task_url", "").endswith("/v1/tasks/task-abc")
    assert res["metadata"].get("task_id") == "task-abc"
    dumped = json.dumps(res)
    assert secret not in dumped
    cap = capsys.readouterr()
    assert secret not in cap.out and secret not in cap.err


def test_runway_smoke_create_http_error(tmp_path: Path, tiny_png: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("RUNWAY_API_KEY", "k")

    def post_fail(url, headers, body):
        return 401, {"_http_error": True, "message": "http_status=401"}

    res = run_runway_image_to_video_smoke(
        image_path=tiny_png,
        prompt="x",
        run_id="rid3",
        out_root=tmp_path / "o",
        post_json=post_fail,
        get_json=lambda *a, **k: (200, {}),
    )
    assert res["ok"] is False
    assert res["exit_code"] == EXIT_FAILED
    assert "runway_create_failed" in res["blocking_reasons"]


def test_runway_smoke_missing_image(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("RUNWAY_API_KEY", "k")
    res = run_runway_image_to_video_smoke(
        image_path=tmp_path / "nope.png",
        prompt="x",
        run_id="rid4",
        out_root=tmp_path / "o",
        post_json=lambda *a, **k: (200, {"id": "x"}),
        get_json=lambda *a, **k: (200, {"status": "SUCCEEDED", "output": []}),
    )
    assert res["ok"] is False
    assert "image_path_missing" in res["blocking_reasons"]


def test_runway_smoke_invalid_run_id(tmp_path: Path, tiny_png: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("RUNWAY_API_KEY", "k")
    res = run_runway_image_to_video_smoke(
        image_path=tiny_png,
        prompt="x",
        run_id="bad/id",
        out_root=tmp_path / "o",
    )
    assert res["exit_code"] == EXIT_INVALID


def test_runway_smoke_task_failed_terminal(tmp_path: Path, tiny_png: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("RUNWAY_API_KEY", "k")

    def post_ok(url, headers, body):
        return 200, {"id": "t1"}

    def get_fail(url, headers):
        return 200, {"status": "FAILED", "failure": "content_policy"}

    res = run_runway_image_to_video_smoke(
        image_path=tiny_png,
        prompt="x",
        run_id="rid5",
        out_root=tmp_path / "o",
        post_json=post_ok,
        get_json=get_fail,
    )
    assert res["ok"] is False
    assert "runway_task_failed" in res["blocking_reasons"]


def test_runway_smoke_no_network_in_default_path_import():
    """Sicherstellen, dass Modulimport keine Requests auslöst."""
    import scripts.runway_image_to_video_smoke as m

    assert m.RESULT_SCHEMA == RESULT_SCHEMA


def test_duration_clamped(tmp_path: Path, tiny_png: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("RUNWAY_API_KEY", "k")
    captured = {}

    def post_ok(url, headers, body):
        captured["duration"] = body.get("duration")
        return 200, {"id": "t2"}

    def get_ok(url, headers):
        return 200, {"status": "SUCCEEDED", "output": ["https://x/u.mp4"]}

    run_runway_image_to_video_smoke(
        image_path=tiny_png,
        prompt="x",
        run_id="rid6",
        out_root=tmp_path / "o",
        duration_seconds=999,
        post_json=post_ok,
        get_json=get_ok,
        save_video=lambda url, dest: (True, []),
    )
    assert captured["duration"] == 10


def test_runway_smoke_poll_timeout_no_traceback(tmp_path: Path, tiny_png: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("RUNWAY_API_KEY", "k")

    def post_ok(url, headers, body):
        return 200, {"id": "t-timeout"}

    def get_pending(url, headers):
        return 200, {"status": "PENDING"}

    res = run_runway_image_to_video_smoke(
        image_path=tiny_png,
        prompt="x",
        run_id="rid_timeout",
        out_root=tmp_path / "o",
        post_json=post_ok,
        get_json=get_pending,
        poll_timeout_seconds=0.12,
        poll_interval_seconds=0.05,
    )
    assert res["ok"] is False
    assert res["status"] == "timeout"
    assert res["exit_code"] == EXIT_TIMEOUT
    assert "runway_task_poll_timeout" in res["warnings"]
    assert res["blocking_reasons"] == []
    assert res["metadata"]["task_id"] == "t-timeout"
    assert "/v1/tasks/t-timeout" in res["metadata"]["task_url"]
    assert res.get("message")
    assert res.get("recommended_action")
    rfile = tmp_path / "o" / "runway_smoke_rid_timeout" / RESULT_FILENAME
    text = rfile.read_text(encoding="utf-8")
    assert "Traceback" not in text


def test_runway_smoke_keyboard_interrupt_during_poll(
    tmp_path: Path, tiny_png: Path, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.setenv("RUNWAY_API_KEY", "k")
    n = {"c": 0}

    def post_ok(url, headers, body):
        return 200, {"id": "t-intr"}

    def get_intr(url, headers):
        n["c"] += 1
        if n["c"] >= 2:
            raise KeyboardInterrupt()
        return 200, {"status": "PENDING"}

    res = run_runway_image_to_video_smoke(
        image_path=tiny_png,
        prompt="x",
        run_id="rid_intr",
        out_root=tmp_path / "o",
        post_json=post_ok,
        get_json=get_intr,
        poll_timeout_seconds=30.0,
        poll_interval_seconds=0.01,
    )
    assert res["status"] == "interrupted"
    assert res["ok"] is False
    assert res["exit_code"] == EXIT_INTERRUPTED
    assert "runway_poll_interrupted" in res["warnings"]
    assert res["metadata"]["task_id"] == "t-intr"
    assert "/v1/tasks/t-intr" in res["metadata"]["task_url"]
    rfile = tmp_path / "o" / "runway_smoke_rid_intr" / RESULT_FILENAME
    assert "Traceback" not in rfile.read_text(encoding="utf-8")


def test_runway_smoke_no_wait_skips_poll(tmp_path: Path, tiny_png: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("RUNWAY_API_KEY", "k")
    calls = {"get": 0}

    def post_ok(url, headers, body):
        return 200, {"id": "nw1"}

    def get_never(url, headers):
        calls["get"] += 1
        return 200, {"status": "SUCCEEDED", "output": ["https://x/y.mp4"]}

    res = run_runway_image_to_video_smoke(
        image_path=tiny_png,
        prompt="x",
        run_id="rid_nw",
        out_root=tmp_path / "o",
        post_json=post_ok,
        get_json=get_never,
        no_wait=True,
    )
    assert res["ok"] is True
    assert res["status"] == "pending"
    assert calls["get"] == 0
    assert res["metadata"]["task_id"] == "nw1"


def test_runway_smoke_poll_transient_then_success(
    tmp_path: Path, tiny_png: Path, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.setenv("RUNWAY_API_KEY", "k")
    n = {"n": 0}

    def post_ok(url, headers, body):
        return 200, {"id": "t-flaky"}

    def get_flaky(url, headers):
        n["n"] += 1
        if n["n"] < 3:
            return 0, {"_url_error": True, "message": "temporary"}
        return 200, {"status": "SUCCEEDED", "output": ["https://cdn.example.test/out.mp4"]}

    res = run_runway_image_to_video_smoke(
        image_path=tiny_png,
        prompt="x",
        run_id="rid_flaky",
        out_root=tmp_path / "o",
        post_json=post_ok,
        get_json=get_flaky,
        save_video=lambda url, dest: (True, []),
        poll_timeout_seconds=5.0,
        poll_interval_seconds=0.05,
    )
    assert res["ok"] is True
    assert "runway_poll_transient" in res["warnings"]


def test_runway_smoke_resume_task_id_only(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("RUNWAY_API_KEY", "k")

    def post_never(*a, **k):
        raise AssertionError("POST should not run in resume mode")

    def get_ok(url, headers):
        assert "resume-task" in url
        return 200, {"status": "SUCCEEDED", "output": ["https://cdn.example.test/r.mp4"]}

    res = run_runway_image_to_video_smoke(
        image_path=None,
        prompt="",
        run_id="rid_resume",
        out_root=tmp_path / "o",
        post_json=post_never,
        get_json=get_ok,
        save_video=lambda url, dest: (True, []),
        existing_task_id="resume-task",
        poll_timeout_seconds=2.0,
        poll_interval_seconds=0.05,
    )
    assert res["ok"] is True
    assert res["metadata"]["task_id"] == "resume-task"
