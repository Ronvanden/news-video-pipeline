"""Phase 8.2 — Prompt Engine V1 (ohne Bildprovider, ohne Persistenz)."""

from __future__ import annotations

import unittest

from fastapi.testclient import TestClient

from app.main import app
from app.models import Chapter, ScenePromptsRequest
from app.visual_plan.policy import SAFETY_NEGATIVE_SEGMENTS_V1
from app.visual_plan.prompt_engine import build_scene_prompts_v1
from app.visual_plan import warning_codes as vw


def _chapter(title: str, content: str) -> Chapter:
    return Chapter(title=title, content=content)


class Phase82Engine(unittest.TestCase):
    def test_determinism(self):
        req = ScenePromptsRequest(
            provider_profile="openai",
            continuity_lock=True,
            chapters=[_chapter("Eins", "Inhalt genug für Szene. " * 8)],
        )
        a = build_scene_prompts_v1(req).model_dump()
        b = build_scene_prompts_v1(req).model_dump()
        self.assertEqual(a, b)
        self.assertIsNotNone(a.get("prompt_quality"))
        self.assertTrue(a["prompt_quality"]["policy_profile"])

    def test_provider_prefix_differs(self):
        base_kw = {
            "chapters": [_chapter("A", "Text genug. " * 10), _chapter("B", "Auch genug. " * 10)],
            "continuity_lock": False,
        }
        o = build_scene_prompts_v1(ScenePromptsRequest(provider_profile="openai", **base_kw))
        l = build_scene_prompts_v1(ScenePromptsRequest(provider_profile="leonardo", **base_kw))
        self.assertTrue(o.scenes[0].positive_expanded.startswith("Provider_stub OpenAI"))
        self.assertTrue(l.scenes[0].positive_expanded.startswith("Provider_stub Leonardo"))
        self.assertIn("oversaturated_hdr", o.scenes[0].negative_prompt)
        self.assertIn("style_bleed", l.scenes[0].negative_prompt)

    def test_continuity_lock_second_scene(self):
        ch = [_chapter("Erste", "Hier ist Berlin und genug Wörter. " * 6), _chapter("Zweite", "Weiter. " * 20)]
        on = build_scene_prompts_v1(
            ScenePromptsRequest(provider_profile="kling", continuity_lock=True, chapters=ch)
        )
        off = build_scene_prompts_v1(
            ScenePromptsRequest(provider_profile="kling", continuity_lock=False, chapters=ch)
        )
        self.assertIn("Continuity_lock:", on.scenes[1].positive_expanded)
        self.assertNotIn("Continuity_lock:", off.scenes[1].positive_expanded)
        self.assertEqual(on.continuity_anchor, on.scenes[0].continuity_token)
        self.assertEqual(off.continuity_anchor, "")
        self.assertEqual(off.scenes[0].continuity_token, "")

    def test_safety_negatives_merged(self):
        req = ScenePromptsRequest(
            provider_profile="openai",
            chapters=[_chapter("X", "Y " * 40)],
        )
        out = build_scene_prompts_v1(req)
        neg = out.scenes[0].negative_prompt
        for seg in SAFETY_NEGATIVE_SEGMENTS_V1:
            self.assertIn(seg, neg)

    def test_empty_chapters_no_scenes_warns(self):
        req = ScenePromptsRequest(chapters=[])
        out = build_scene_prompts_v1(req)
        self.assertFalse(out.scenes)
        joined = "\n".join(out.warnings)
        self.assertIn(vw.W_PROMPT_NO_SCENES, joined)
        self.assertEqual(out.blueprint_status, "draft")

    def test_placeholder_warning_always_present(self):
        req = ScenePromptsRequest(chapters=[_chapter("T", "C " * 40)])
        out = build_scene_prompts_v1(req)
        self.assertTrue(any(vw.W_PROMPT_PROVIDER_PLACEHOLDER in w for w in out.warnings))


class Phase82Route(unittest.TestCase):
    def test_scene_prompts_route(self):
        client = TestClient(app)
        r = client.post(
            "/story-engine/scene-prompts",
            json={
                "provider_profile": "openai",
                "continuity_lock": True,
                "video_template": "generic",
                "chapters": [{"title": "Eins", "content": "Abc " * 30}],
            },
        )
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertIn("scenes", data)
        self.assertEqual(len(data["scenes"]), 1)
        self.assertIn("negative_prompt", data["scenes"][0])
        self.assertIn("warnings", data)


if __name__ == "__main__":
    unittest.main()
