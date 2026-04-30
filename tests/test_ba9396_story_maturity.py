"""BA 9.3–9.6 Story Engine Maturity — Conformance-Level, Rhythm, Experiment-Registry, Story-Pack."""

from __future__ import annotations

import unittest

from fastapi.testclient import TestClient

from app.main import app
from app.models import Chapter, RhythmHintRequest
from app.story_engine.conformance import (
    apply_template_conformance,
    conformance_persistence_gate,
)
from app.story_engine.experiment_registry import (
    assign_hook_variant_and_experiment,
    public_experiment_registry,
)
from app.story_engine.rhythm_engine import rhythm_hints_v1
from app.story_engine.templates import definition_version_for_template
from app.watchlist.connector_export import build_story_pack_dict
from app.watchlist.models import GeneratedScript


class Ba93Conformance(unittest.TestCase):
    def test_off_skips_warnings(self):
        ws, gate = apply_template_conformance(
            template_conformance_level="off",
            template_id="mystery_explainer",
            hook="kurz",
            chapters=[{"title": "A", "content": "x"}],
            full_script="wort " * 10,
            duration_minutes=10,
        )
        self.assertEqual(ws, [])
        self.assertIsNone(gate)

    def test_strict_gate_failed_lists_extra_warning(self):
        ws, gate = apply_template_conformance(
            template_conformance_level="strict",
            template_id="mystery_explainer",
            hook="kurz",
            chapters=[{"title": "A", "content": "x"}],
            full_script="wort " * 10,
            duration_minutes=10,
        )
        self.assertEqual(gate, "failed")
        self.assertTrue(any("[template_strict:gate_failed]" in x for x in ws), ws)

    def test_definition_version_present(self):
        self.assertEqual(definition_version_for_template("true_crime"), "1")

    def test_generate_request_default_conformance(self):
        from app.models import GenerateScriptRequest

        g = GenerateScriptRequest(url="https://example.com/n")
        self.assertEqual(g.template_conformance_level, "warn")

    def test_persistence_gate_empty_when_not_strict(self):
        self.assertEqual(
            conformance_persistence_gate(
                template_conformance_level="warn",
                template_id="history_deep_dive",
                hook="x " * 20,
                chapters=[Chapter(title=f"K{i}", content="y " * 50) for i in range(6)],
                full_script="w " * 900,
                duration_minutes=10,
            ),
            "",
        )


class Ba94Rhythm(unittest.TestCase):
    def test_hints_have_beats(self):
        rhythm, warns = rhythm_hints_v1(
            video_template="mystery_explainer",
            duration_minutes=10,
            chapters=[
                Chapter(title="Einstieg", content="a " * 40),
                Chapter(title="Mitte", content="b " * 60),
                Chapter(title="Fazit", content="c " * 35),
            ],
            hook="Fragestellung und Problemrahmen " * 2,
        )
        self.assertGreaterEqual(len(rhythm.get("beats") or []), 3)
        self.assertIn("video_template", rhythm)


class Ba96Registry(unittest.TestCase):
    def test_assign_variant_stable(self):
        e, v = assign_hook_variant_and_experiment(
            video_template="true_crime", hook_type="shock_reveal"
        )
        self.assertEqual(e, "exp_hook_ab_v1")
        self.assertEqual(v, "hv_tension_arc_v1")

    def test_public_registry_lists_variants(self):
        d = public_experiment_registry()
        self.assertIn("variants", d)
        self.assertGreaterEqual(len(d["variants"]), 1)


class Ba95Exporter(unittest.TestCase):
    def test_story_pack_contains_hook_meta(self):
        gs = GeneratedScript(
            id="g_test",
            script_job_id="g_test",
            source_url="https://youtu.be/a",
            title="Testtitel",
            hook="Öffnung",
            full_script="Inhalt lang genug für Tests hier. " * 10,
            created_at="2026-05-01T10:00:00Z",
            hook_type="z_test",
            hook_score=8.5,
            video_template="generic",
            story_structure={"schema_version": "1"},
            rhythm_hints={"beats": []},
            experiment_id="exp_hook_ab_v1",
            hook_variant_id="hv_doc_led_v1",
        )
        sp = build_story_pack_dict(generated_script=gs)
        self.assertEqual(sp.get("hook_engine", {}).get("hook_type"), "z_test")
        self.assertEqual(sp.get("experiment_id"), "exp_hook_ab_v1")


class Ba93Http(unittest.TestCase):
    def test_rhythm_hint_endpoint(self):
        client = TestClient(app)
        body = RhythmHintRequest(
            video_template="generic",
            duration_minutes=8,
            hook="Kurzer Einstieg",
            chapters=[
                Chapter(title="A", content="Text " * 30),
                Chapter(title="B", content="Mehr " * 25),
            ],
        )
        r = client.post("/story-engine/rhythm-hint", json=body.model_dump())
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertIn("rhythm", data)
        self.assertIn("beats", data["rhythm"])

    def test_experiment_registry_endpoint(self):
        client = TestClient(app)
        r = client.get("/story-engine/experiment-registry")
        self.assertEqual(r.status_code, 200)
        self.assertIn("variants", r.json())


if __name__ == "__main__":
    unittest.main()
