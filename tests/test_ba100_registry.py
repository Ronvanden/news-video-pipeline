"""BA 10.0 — Connector registry."""

from app.production_connectors.registry import get_connector, list_available_connectors


def test_list_available_connectors_returns_five_roles():
    lst = list_available_connectors()
    types = {x["provider_type"] for x in lst}
    assert types == {"image", "video", "voice", "thumbnail", "render"}


def test_get_connector_by_type_and_alias():
    assert get_connector("image") is not None
    assert get_connector("Leonardo") is not None
    assert get_connector("kling") is not None
    assert get_connector("") is None
