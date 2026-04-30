"""BA 9.8 — Story Intelligence Layer (read-only Hinweise)."""

from __future__ import annotations

from __future__ import annotations

import unittest

from app.story_engine.story_intelligence_layer import build_story_engine_intelligence_summary
from app.story_engine.template_optimization_aggregate import (
    build_story_engine_template_optimization_summary,
)
from app.watchlist.models import GeneratedScript


def _fixture_rows(n: int = 14) -> list[GeneratedScript]:
    rows = []
    for i in range(n):
        tpl = "true_crime" if i % 2 == 0 else "generic"
        rows.append(
            GeneratedScript(
                id=f"id{i}",
                script_job_id=f"sj{i}",
                source_url="https://youtu.be/x",
                title="T",
                hook="H",
                full_script=("word " * 40),
                created_at=f"2026-05-01T12:{i:02d}:00Z",
                video_template=tpl,
                template_definition_version="1",
                hook_score=float(7 + (i % 4)),
                experiment_id=("exp_demo" if i == 0 else ""),
                hook_variant_id=("hv1" if i == 1 else ""),
            )
        )
    return rows


class Ba98StoryIntelligence(unittest.TestCase):
    def test_readiness_contains_no_closed_loop(self):
        rows = _fixture_rows(14)
        opt = build_story_engine_template_optimization_summary(rows)
        intel = build_story_engine_intelligence_summary(rows, opt)
        notes = intel.self_learning_readiness_notes
        self.assertTrue(
            any("[story_intelligence:readiness_no_closed_loop]" in x for x in notes)
        )

    def test_cross_template_summary_populated_when_sample_met(self):
        rows = _fixture_rows(14)
        opt = build_story_engine_template_optimization_summary(rows)
        self.assertTrue(opt.min_statistics_sample_met)
        intel = build_story_engine_intelligence_summary(rows, opt)
        self.assertTrue(any("template_distribution" in x for x in intel.cross_template_summary))


if __name__ == "__main__":
    unittest.main()
