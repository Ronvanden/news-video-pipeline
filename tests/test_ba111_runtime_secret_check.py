"""BA 11.1 — Runtime Secret Check."""

from app.prompt_engine.pipeline import build_production_prompt_plan
from app.prompt_engine.schema import PromptPlanRequest
from app.production_connectors.runtime_secret_check import build_runtime_secret_check


def test_secret_configured_when_env_present(monkeypatch):
    monkeypatch.setenv("LEONARDO_API_KEY", "test-key-placeholder")
    monkeypatch.setenv("VOICE_API_KEY", "test-voice-placeholder")
    plan = build_production_prompt_plan(PromptPlanRequest(topic="Polizei und Mord", title="", source_summary=""))
    r = build_runtime_secret_check(plan)
    assert r.runtime_status == "ready"
    assert any(p.provider_name == "Leonardo" and p.secret_status == "configured" for p in r.provider_secrets)
    assert any("Voice" in p.provider_name and p.secret_status == "configured" for p in r.provider_secrets)


def test_missing_secret_marks_provider(monkeypatch):
    monkeypatch.delenv("LEONARDO_API_KEY", raising=False)
    monkeypatch.delenv("VOICE_API_KEY", raising=False)
    plan = build_production_prompt_plan(PromptPlanRequest(topic="Polizei und Mord", title="", source_summary=""))
    r = build_runtime_secret_check(plan)
    assert r.runtime_status == "blocked"
    assert r.missing_required_secrets
    assert any(p.secret_status == "missing" for p in r.provider_secrets)


def test_never_logs_values(monkeypatch, capsys):
    monkeypatch.setenv("LEONARDO_API_KEY", "super-secret-value-never-log")
    plan = build_production_prompt_plan(PromptPlanRequest(topic="Polizei und Mord", title="", source_summary=""))
    build_runtime_secret_check(plan)
    out = capsys.readouterr().out + capsys.readouterr().err
    assert "super-secret-value-never-log" not in out
