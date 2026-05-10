"""BA 32.39 — Leonardo platform model discovery (gemocktes HTTP nur)."""

from __future__ import annotations

import importlib.util
import json
from io import BytesIO
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from urllib.error import HTTPError, URLError

_ROOT = Path(__file__).resolve().parents[1]
_SCRIPT = _ROOT / "scripts" / "list_leonardo_models.py"


@pytest.fixture(scope="module")
def lpm_mod():
    from app.production_connectors import leonardo_platform_models as m

    return m


@pytest.fixture(scope="module")
def list_script_mod():
    spec = importlib.util.spec_from_file_location("list_leonardo_models_ba339", _SCRIPT)
    assert spec and spec.loader
    sm = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(sm)
    return sm


class _Resp:
    __test__ = False

    def __init__(self, code: int, body: bytes):
        self._body = body
        self.status = code

    def __enter__(self):
        return self

    def __exit__(self, *_a):
        return False

    def read(self):
        return self._body

    def getcode(self):
        return self.status


def test_fetch_success_returns_safe_models(lpm_mod):
    payload = {
        "custom_models": [
            {
                "id": "aaaaaaaa-bbbb-4ccc-dddd-eeeeeeeeeeee",
                "name": "Test Model \u0394",
                "description": "short",
                "featured": True,
                "nsfw": False,
                "generated_image": {"id": "gggggggg-hhhh-4iii-jjjj-kkkkkkkkkkkk", "url": "https://cdn.example.com/x?token=SECRET"},
            },
            {"no": "id"},
        ]
    }
    raw = json.dumps(payload).encode("utf-8")

    with patch.object(lpm_mod, "urlopen", return_value=_Resp(200, raw)):
        ok, models, warns = lpm_mod.fetch_leonardo_platform_models_public(api_key="k")
    assert ok is True
    assert warns == []
    assert len(models) == 1
    m0 = models[0]
    assert m0["id"] == "aaaaaaaa-bbbb-4ccc-dddd-eeeeeeeeeeee"
    assert m0["name"] == "Test Model \u0394"
    assert m0["featured"] is True
    assert m0["nsfw"] is False
    assert m0["description_char_count"] == 5
    assert m0["has_preview_image"] is True
    blob = json.dumps(models)
    assert "SECRET" not in blob
    assert "token=" not in blob


@pytest.mark.parametrize(
    "code,expected_sub",
    [
        (401, "leonardo_models_http_401"),
        (403, "leonardo_models_http_403"),
        (500, "leonardo_models_http_5xx"),
    ],
)
def test_fetch_http_errors(lpm_mod, code, expected_sub):
    err = HTTPError(
        "https://cloud.leonardo.ai/api/rest/v1/platformModels",
        code,
        "err",
        {},
        BytesIO(b"{}"),
    )
    with patch.object(lpm_mod, "urlopen", side_effect=err):
        ok, models, warns = lpm_mod.fetch_leonardo_platform_models_public(api_key="k")
    assert ok is False
    assert models == []
    assert expected_sub in ";".join(warns)
    assert f"leonardo_models_http_error:{code}" in warns


def test_fetch_invalid_json(lpm_mod):
    with patch.object(lpm_mod, "urlopen", return_value=_Resp(200, b"not json")):
        ok, models, warns = lpm_mod.fetch_leonardo_platform_models_public(api_key="k")
    assert ok is False
    assert "leonardo_models_response_invalid" in warns


def test_fetch_missing_custom_models(lpm_mod):
    with patch.object(lpm_mod, "urlopen", return_value=_Resp(200, b"{}")):
        ok, models, warns = lpm_mod.fetch_leonardo_platform_models_public(api_key="k")
    assert ok is False
    assert models == []
    assert "leonardo_models_response_invalid" in warns


def test_fetch_missing_api_key(lpm_mod):
    ok, models, warns = lpm_mod.fetch_leonardo_platform_models_public(api_key="  ")
    assert ok is False
    assert warns == ["leonardo_models_api_key_missing"]


def test_fetch_url_error_diagnostic(lpm_mod):
    with patch.object(lpm_mod, "urlopen", side_effect=URLError("boom")):
        ok, _, warns = lpm_mod.fetch_leonardo_platform_models_public(api_key="k")
    assert ok is False
    assert any(w.startswith("leonardo_models_url_error:") for w in warns)


def test_script_stdout_has_no_api_key(list_script_mod, capsys):
    import sys

    fake_key = "LEON_SECRET_PLACEHOLDER_12345_xx"
    with patch.dict("os.environ", {"LEONARDO_API_KEY": fake_key}, clear=False):
        with patch.object(sys, "argv", ["list_leonardo_models.py"]):

            def _fake(**_kw):
                return (
                    True,
                    [
                        {
                            "id": "pub-uuid-00000000-0000-4000-8000-000000000001",
                            "name": "Pub",
                            "featured": False,
                            "nsfw": False,
                            "description_char_count": 0,
                            "has_preview_image": False,
                        }
                    ],
                    [],
                )

            with patch.object(list_script_mod, "fetch_leonardo_platform_models_public", side_effect=_fake):
                rc = list_script_mod.main()

    captured = capsys.readouterr()
    assert rc == 0
    assert fake_key not in captured.out
    assert fake_key not in captured.err
    assert "Bearer" not in captured.out
    assert "pub-uuid-00000000-0000-4000-8000-000000000001" in captured.out
