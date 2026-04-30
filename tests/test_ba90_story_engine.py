"""BA 9.0–9.2: Story Engine / Video-Templates (ohne Live-OpenAI)."""

from __future__ import annotations

import unittest
import unittest.mock

from app.story_engine.conformance import conformance_warnings_for_template
from app.story_engine.templates import (
    normalize_story_template_id,
    story_template_prompt_addon_de,
    style_profile_for_template,
    voice_profile_for_template,
)
from app.utils import ScriptGenerator


class Ba90Templates(unittest.TestCase):
    def test_unknown_template_warns(self):
        tid, ws = normalize_story_template_id("not_a_real_template")
        self.assertEqual(tid, "generic")
        self.assertTrue(ws)

    def test_true_crime_addon_nonempty(self):
        self.assertIn("TRUE CRIME", story_template_prompt_addon_de("true_crime"))

    def test_style_voice_mapping(self):
        self.assertEqual(style_profile_for_template("true_crime"), "true_crime")
        self.assertEqual(voice_profile_for_template("mystery_explainer"), "soft")


class Ba90Conformance(unittest.TestCase):
    def test_generic_no_extra(self):
        self.assertEqual(
            conformance_warnings_for_template(
                template_id="generic",
                hook="x" * 20,
                chapters=[1, 2, 3, 4],
                full_script="word " * 400,
                duration_minutes=10,
            ),
            [],
        )

    def test_short_hook_warns_for_format(self):
        w = conformance_warnings_for_template(
            template_id="true_crime",
            hook="kurz",
            chapters=[{"t": 1}, {"t": 2}, {"t": 3}, {"t": 4}],
            full_script="a " * 200,
            duration_minutes=10,
        )
        self.assertTrue(
            any("[template_conformance:hook_length]" in x for x in w),
            w,
        )


class Ba90FallbackGenerator(unittest.TestCase):
    def test_fallback_respects_template_hook_flavor(self):
        g = ScriptGenerator()
        with unittest.mock.patch("app.utils._effective_openai_api_key", return_value=""):
            t, hook, ch, full, mode, reason = g.generate_script(
                "Testfall Berlin",
                [
                    "Erster Satz mit genug Zeichen für einen Key Point hier.",
                    "Zweiter Satz ebenfalls lang genug für die Heuristik.",
                ],
                10,
                500,
                video_template="true_crime",
            )
        self.assertEqual(mode, "fallback")
        self.assertIn("Faktenlage", hook)
        self.assertTrue(len(ch) >= 1)


if __name__ == "__main__":
    unittest.main()
