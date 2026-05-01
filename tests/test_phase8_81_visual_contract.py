"""Phase 8.1 — Scene Blueprint Contract (deterministisch, ohne Bildprovider)."""

from __future__ import annotations

import unittest

from fastapi.testclient import TestClient

from app.main import app
from app.models import Chapter, StorySceneBlueprintRequest
from app.visual_plan.builder import build_scene_blueprint_plan
from app.visual_plan.policy import VISUAL_POLICY_PROFILE_V1


def _chapter(title: str, content: str) -> Chapter:
    return Chapter(title=title, content=content)


class Phase81Builder(unittest.TestCase):
    def test_empty_chapters_draft_no_scenes(self):
        r = build_scene_blueprint_plan(StorySceneBlueprintRequest(chapters=[]))
        self.assertEqual(r.status, "draft")
        self.assertFalse(r.scenes)
        joined = "\n".join(r.warnings)
        self.assertIn("no_chapters", joined)

    def test_determinism_same_input(self):
        req = StorySceneBlueprintRequest(
            video_template="true_crime",
            title="Fall X",
            hook="Einbruch geklärt?",
            chapters=[
                _chapter("Einleitung", "Die Polizei ermittelt in Berlin."),
                _chapter("Hintergrund", "Zeugen hatten wenig zu berichten."),
            ],
        )
        a = build_scene_blueprint_plan(req).model_dump()
        b = build_scene_blueprint_plan(req).model_dump()
        self.assertEqual(a, b)

    def test_sparse_chapter_risk_flag(self):
        req = StorySceneBlueprintRequest(
            chapters=[_chapter("Kurz", "Zu kurz.")]
        )
        out = build_scene_blueprint_plan(req)
        self.assertEqual(len(out.scenes), 1)
        self.assertIn("sparse_chapter", out.scenes[0].risk_flags)
        self.assertTrue(any("sparse_chapter" in w for w in out.warnings))

    def test_story_structure_read_only_warning(self):
        req = StorySceneBlueprintRequest(
            chapters=[_chapter("A", "Hier ist genügend Fließtext. " * 12)],
            story_structure={"acts": [{"n": 1}]},
        )
        out = build_scene_blueprint_plan(req)
        joined = "\n".join(out.warnings)
        self.assertIn("visual_story_meta", joined)

    def test_rhythm_beats_augment_intent(self):
        req = StorySceneBlueprintRequest(
            chapters=[_chapter("Öffnung", "Viel Inhalt sodass nicht sparse. " * 8)],
            rhythm_hints={
                "beats": [
                    {"index": 0, "label": "open"},
                ]
            },
        )
        out = build_scene_blueprint_plan(req)
        self.assertIn("pacing_hint:open", out.scenes[0].intent)

    def test_full_script_drift_warning(self):
        fs = ("word ") * 2000
        req = StorySceneBlueprintRequest(
            chapters=[_chapter("Eins", "nur wenig.")],
            full_script=fs,
        )
        out = build_scene_blueprint_plan(req)
        self.assertTrue(any("full_script_drift" in w for w in out.warnings))

    def test_policy_profile_constant(self):
        req = StorySceneBlueprintRequest(chapters=[_chapter("X", "Y " * 40)])
        self.assertEqual(build_scene_blueprint_plan(req).policy_profile, VISUAL_POLICY_PROFILE_V1)


class Phase81Route(unittest.TestCase):
    def test_route_returns_json_contract(self):
        client = TestClient(app)
        r = client.post(
            "/story-engine/scene-plan",
            json={
                "video_template": "generic",
                "title": "T",
                "chapters": [{"title": "Eins", "content": "Abc " * 30}],
            },
        )
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertIn("scenes", data)
        self.assertIn("warnings", data)
        self.assertEqual(len(data["scenes"]), 1)


if __name__ == "__main__":
    unittest.main()
