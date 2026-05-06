"""BA 0.0 — Prompt Operating System docs."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def test_ppos_docs_exist():
    assert (ROOT / "docs" / "PROMPT_OPERATING_SYSTEM.md").exists()
    assert (ROOT / "docs" / "PROMPT_PATTERNS.md").exists()
    assert (ROOT / "docs" / "TOKEN_EFFICIENCY_GUIDE.md").exists()


def test_prompt_operating_system_core_sections_and_macros():
    text = _read("docs/PROMPT_OPERATING_SYSTEM.md")
    for section in (
        "Global Prompt Ruleset V1",
        "Prompt Execution Hierarchy",
        "Prompt Compression Model",
        "PPOS_GLOBAL_V1",
        "PPOS_FULL_SUITE",
        "PPOS_STANDARD_BA",
        "PPOS_CONNECTOR",
        "PPOS_ASSEMBLY",
        "PPOS_PUBLISHING",
    ):
        assert section in text
    assert "GenerateScriptResponse" in text
    assert "python -m compileall app" in text
    assert "python -m pytest" in text


def test_prompt_patterns_include_standard_contracts():
    text = _read("docs/PROMPT_PATTERNS.md")
    for section in (
        "Standard BA Module Contract",
        "Full Suite Contract",
        "Connector Pattern",
        "Assembly Pattern",
        "Publishing Pattern",
    ):
        assert section in text
    for required in ("Modul", "Kernfunktion", "Schema", "Integration", "Tests", "Doku", "Checks"):
        assert required in text


def test_pipeline_plan_mentions_ba000_meta_layer():
    text = _read("PIPELINE_PLAN.md")
    assert "BA 0.0 — Prompt Operating System (PPOS) V1" in text
    assert "Nicht Teil der Produktionsausführung" in text
