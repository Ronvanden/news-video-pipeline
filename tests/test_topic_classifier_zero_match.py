"""Topic classifier: Zero-keyword fallback → documentary / public_interest (nicht true_crime)."""

from app.prompt_engine.topic_classifier import TopicClassification, classify_topic


def test_zero_hits_prefers_documentary_when_loaded():
    templates = {
        "documentary": {"classifier_keywords": ["nachrichten"]},
        "true_crime": {"classifier_keywords": ["mord"]},
    }
    c = classify_topic("xyz_no_keyword_match_at_all", templates)
    assert isinstance(c, TopicClassification)
    assert c.template_type == "documentary"
    assert c.scores[0][1] == 0


def test_zero_hits_public_interest_if_documentary_missing():
    templates = {
        "public_interest": {"classifier_keywords": ["petition"]},
        "true_crime": {"classifier_keywords": ["mord"]},
    }
    c = classify_topic("abc", templates)
    assert c.template_type == "public_interest"


def test_positive_hits_still_win_true_crime():
    templates = {
        "documentary": {"classifier_keywords": ["nachrichten"]},
        "true_crime": {"classifier_keywords": ["mord", "polizei"]},
    }
    c = classify_topic("Polizei und Mord", templates)
    assert c.template_type == "true_crime"
    assert c.scores[0][1] >= 1
