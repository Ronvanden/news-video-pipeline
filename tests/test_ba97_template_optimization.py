"""BA 9.7 — Adaptive Template Optimization (Drift/Scores/refinement ohne Generate-Vertrag)."""

from __future__ import annotations

import unittest
from typing import List, Optional

from fastapi.testclient import TestClient

from app.main import app
from app.watchlist.models import GeneratedScript
from app.story_engine.template_optimization_aggregate import (
    build_story_engine_template_optimization_summary,
)


def _script(
    tid: str = "generic",
    *,
    v: str = "1",
    warnings: Optional[List[str]] = None,
    gate: str = "",
    hook_score: float = 7.0,
) -> GeneratedScript:
    return GeneratedScript(
        id="gsx",
        script_job_id="sj",
        source_url="https://youtu.be/a",
        title="t",
        hook="h",
        full_script="w " * 30,
        created_at="2026-05-01T12:00:00Z",
        video_template=tid,
        template_definition_version=v,
        template_conformance_gate=gate,
        hook_score=hook_score,
        warnings=list(warnings or []),
    )


class Ba97TemplateOptimization(unittest.TestCase):
    def test_scores_and_drift_per_template_normalized(self):
        rows = [
            _script("mystery_explainer", v="1"),
            _script("MYSTERY-EXPLAINER", v="1", hook_score=8.0),
            _script(
                "mystery_explainer",
                v="9",
                warnings=["[template_conformance:chapter_count] Zu wenig"],
            ),
        ]
        out = build_story_engine_template_optimization_summary(rows)
        self.assertEqual(out.sample_scripts, 3)
        self.assertGreaterEqual(len(out.drift_rows), 1)
        row = next(d for d in out.drift_rows if d.template_id == "mystery_explainer")
        self.assertEqual(row.script_count, 3)
        self.assertGreaterEqual(row.distinct_nonempty_template_definition_versions, 2)
        scores = {s.template_id: s.internal_performance_score_0_to_100 for s in out.scores}
        self.assertIn("mystery_explainer", scores)

    def test_empty_sample_stable(self):
        out = build_story_engine_template_optimization_summary([])
        self.assertEqual(out.sample_scripts, 0)
        self.assertFalse(out.min_statistics_sample_met)
        self.assertTrue(out.warnings)

    def test_health_endpoint_requires_firestore_but_route_registered(self):
        client = TestClient(app)
        r = client.get("/health")
        self.assertEqual(r.status_code, 200)
        r2 = client.get("/story-engine/template-health")
        self.assertIn(r2.status_code, (503, 200))


if __name__ == "__main__":
    unittest.main()
