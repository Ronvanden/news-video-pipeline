"""BA 8.5: Input-Quality-Guard (Transkript-/Eingangsklassifikation)."""

from __future__ import annotations

import unittest

from app.watchlist.input_quality_guard import (
    build_input_quality_decision,
    classify_transcript_failure,
    normalize_input_quality_status,
)


class Ba85InputQuality(unittest.TestCase):
    def test_classify_missing(self):
        self.assertEqual(
            classify_transcript_failure(
                error_code="transcript_not_available",
                warnings=[],
            ),
            "transcript_missing",
        )

    def test_classify_blocked(self):
        self.assertEqual(
            classify_transcript_failure(
                error_code="transcript_check_failed",
                warnings=[],
            ),
            "transcript_blocked",
        )

    def test_classify_from_warnings(self):
        self.assertEqual(
            classify_transcript_failure(
                error_code="",
                warnings=["Transcript not available for this video."],
            ),
            "transcript_missing",
        )

    def test_normalize_legacy(self):
        c, s = normalize_input_quality_status("transcript_not_available")
        self.assertEqual(c, "transcript_missing")
        self.assertEqual(s, "transcript_missing")

    def test_decision_escalation_blocked(self):
        d = build_input_quality_decision(
            skip_reason="transcript_check_failed",
            warnings=[],
        )
        self.assertEqual(d["input_quality_status"], "transcript_blocked")
        self.assertTrue(d["should_escalate"])
        self.assertIn("fallback_hooks", d)


if __name__ == "__main__":
    unittest.main()
