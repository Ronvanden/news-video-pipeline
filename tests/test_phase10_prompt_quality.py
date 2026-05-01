"""BA 10.1 — Prompt Quality Layer (Unit, ohne Route)."""

from __future__ import annotations

import unittest

from app.models import (
    SceneBlueprintContract,
    SceneBlueprintPlanResponse,
    SceneBlueprintPromptPack,
    SceneExpandedPrompt,
)
from app.visual_plan.prompt_quality import (
    CHK_BLUEPRINT_DRAFT,
    CHK_NO_SCENES,
    CHK_POSITIVE_SHORT,
    CHK_SPARSE_CHAPTER,
    build_prompt_quality,
)


class PromptQualityTests(unittest.TestCase):
    def test_no_scenes_global(self):
        plan = SceneBlueprintPlanResponse(
            policy_profile="x",
            plan_version=1,
            status="draft",
            scenes=[],
            warnings=[],
        )
        r = build_prompt_quality(plan, [], continuity_lock=False)
        self.assertIn(CHK_NO_SCENES, r.global_checks)
        self.assertIn(CHK_BLUEPRINT_DRAFT, r.global_checks)
        self.assertEqual(len(r.scenes), 0)

    def test_blueprint_draft_flag(self):
        plan = SceneBlueprintPlanResponse(
            policy_profile="x",
            plan_version=1,
            status="draft",
            scenes=[
                SceneBlueprintContract(
                    scene_number=1,
                    prompt_pack=SceneBlueprintPromptPack(image_primary="x" * 200),
                )
            ],
            warnings=[],
        )
        scenes = [
            SceneExpandedPrompt(
                scene_number=1,
                positive_expanded="Provider_stub OpenAI " + "word " * 40,
                negative_prompt="a; b; c; d; e",
            )
        ]
        r = build_prompt_quality(plan, scenes, continuity_lock=False)
        self.assertIn(CHK_BLUEPRINT_DRAFT, r.global_checks)

    def test_sparse_and_short_positive(self):
        plan = SceneBlueprintPlanResponse(
            policy_profile="x",
            plan_version=1,
            status="ready",
            scenes=[
                SceneBlueprintContract(
                    scene_number=1,
                    risk_flags=["sparse_chapter"],
                    prompt_pack=SceneBlueprintPromptPack(image_primary="short"),
                )
            ],
            warnings=[],
        )
        scenes = [
            SceneExpandedPrompt(
                scene_number=1,
                positive_expanded="short",
                negative_prompt="only_one",
            )
        ]
        r = build_prompt_quality(plan, scenes, continuity_lock=False)
        self.assertEqual(len(r.scenes), 1)
        codes = set(r.scenes[0].checks)
        self.assertIn(CHK_SPARSE_CHAPTER, codes)
        self.assertIn(CHK_POSITIVE_SHORT, codes)


if __name__ == "__main__":
    unittest.main()
