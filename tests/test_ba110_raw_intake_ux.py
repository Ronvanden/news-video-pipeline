"""BA 11.0 — Rohtext-Headline/Summary-Heuristik (Spiegel der JS-Logik in founder_dashboard/html.py)."""

from __future__ import annotations

import re
import unittest


def build_raw_headline(raw: str, topic_opt: str = "") -> str:
    """Spiegel von buildRawHeadline im Dashboard-JS (Topic → Titelbasis, sonst erste Aussage ≤60)."""
    t_opt = (topic_opt or "").strip()
    if t_opt:
        return (t_opt[:69].rstrip() + "…") if len(t_opt) > 72 else t_opt
    t = str(raw or "")
    t = re.sub(r"^[\s\-–—•*#]+", "", t)
    t = re.sub(r"\s+", " ", t).strip()
    if not t:
        return "Rohtext"
    chunks = re.findall(r"[^.!?]{6,}?[.!?]+|[^.!?]{12,}$", t)
    first = chunks[0].strip() if chunks else t
    if len(first) < 10 and len(chunks) > 1:
        first = re.sub(r"\s+", " ", (chunks[0] + " " + chunks[1]).strip())
    if len(first) > 60:
        first = first[:57]
        sp = first.rfind(" ")
        if sp > 15:
            first = first[:sp]
        first = first.strip() + "…"
    c = (first[0].upper() + first[1:]).strip() if first else "Rohtext"
    return c or "Rohtext"


def build_raw_source_summary(raw: str) -> str:
    """Spiegel von buildRawSourceSummary (max. 3 Satz-/Fragment-Chunks, gekappt)."""
    t = re.sub(r"\s+", " ", str(raw or "").strip()).strip()
    if not t:
        return ""
    chunks = re.findall(r"[^.!?]{8,}?[.!?]+|[^.!?]{14,}$", t)
    if not chunks:
        chunks = [t]
    take = " ".join(chunks[:3]).strip()
    if len(take) > 480:
        take = take[:440]
        sp = take.rfind(" ")
        if sp > 80:
            take = take[:sp]
        take = take.strip() + " …"
    return take


class Ba110RawIntakeUxTests(unittest.TestCase):
    def test_topic_becomes_title_basis(self) -> None:
        raw = "irrelevant viel Text. Zweiter Satz geht weiter und weiter."
        self.assertEqual(build_raw_headline(raw, "  AfD im Vormarsch  "), "AfD im Vormarsch")

    def test_long_topic_truncated(self) -> None:
        long_topic = "x" * 80
        out = build_raw_headline("abc", long_topic)
        self.assertTrue(out.endswith("…"))
        self.assertLessEqual(len(out), 72)

    def test_headline_not_full_raw(self) -> None:
        raw = (
            "die situation eskaliert weiter in vielen regionen. "
            "experten warnen vor folgen. "
            "politiker reagieren zurückhaltend. "
            "bürger fragen nach perspektiven."
        )
        h = build_raw_headline(raw, "")
        self.assertNotEqual(h.strip(), raw.strip())
        self.assertLessEqual(len(h), 63)

    def test_summary_shorter_than_raw(self) -> None:
        raw = "Erster Satz mit genug Zeichen hier drin. " * 15
        raw += "Zweiter Satz ebenfalls lang genug für die Heuristik. " * 10
        raw += "Dritter Satz schließt ab."
        s = build_raw_source_summary(raw)
        self.assertLess(len(s), len(raw))
        self.assertGreater(len(s), 20)


if __name__ == "__main__":
    unittest.main()
