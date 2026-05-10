"""BA 32.37 — Leonardo Prompt/Payload Safety + Safe Diagnostics (no live HTTP)."""

from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError
from io import BytesIO

import pytest

from app.founder_dashboard.ba323_video_generate import build_asset_artifact
from app.production_connectors.leonardo_live_connector import (
    DEFAULT_LEONARDO_MODEL_ID,
    DEFAULT_LEONARDO_MODEL_PUBLIC_LABEL,
    _build_leonardo_generation_payload,
)

_ROOT = Path(__file__).resolve().parents[1]
_SCRIPT = _ROOT / "scripts" / "run_asset_runner.py"


@pytest.fixture(scope="module")
def ar_mod():
    spec = importlib.util.spec_from_file_location("run_asset_runner_ba337", _SCRIPT)
    assert spec and spec.loader
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def test_mini_smoke_payload_forces_repo_default_model():
    """LEONARDO_MODEL_ID aus ENV darf bei profile=mini_smoke den POST nicht verwässern."""
    custom = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
    with patch.dict(os.environ, {"LEONARDO_MODEL_ID": custom}, clear=False):
        body = _build_leonardo_generation_payload({"prompts": ["x"]}, profile="mini_smoke")
        body_std = _build_leonardo_generation_payload({"prompts": ["x"]}, profile="standard")
    assert body["modelId"] == DEFAULT_LEONARDO_MODEL_ID
    assert body_std["modelId"] == custom


def test_sanitize_trim_warns_character_counts_only(ar_mod):
    long = ("word_" * 900).strip()
    assert len(long) > ar_mod._LEONARDO_PROMPT_CHARS_MAX_MINI_SMOKE
    trimmed, warns = ar_mod._sanitize_leonardo_visual_prompt(
        long,
        max_chars=ar_mod._LEONARDO_PROMPT_CHARS_MAX_MINI_SMOKE,
    )
    assert len(trimmed) <= ar_mod._LEONARDO_PROMPT_CHARS_MAX_MINI_SMOKE + 24
    assert any(str(w).startswith("leonardo_prompt_trim_chars:") for w in warns)
    tw = [w for w in warns if str(w).startswith("leonardo_prompt_trim_chars:")][0]
    parts = str(tw).split(":")
    assert int(parts[1]) > int(parts[2])
    joined = "\n".join(warns)
    assert long[3000:3100] not in joined


def test_sanitize_empty_uses_fallback_warning(ar_mod):
    s, warns = ar_mod._sanitize_leonardo_visual_prompt("  \t  ", max_chars=500)
    assert s.strip()
    assert "leonardo_prompt_fallback_used" in warns


class _Resp200:
    __test__ = False

    def __init__(self, payload: dict):
        import json as _json

        self._raw = _json.dumps(payload).encode("utf-8")
        self.status = 200

    def __enter__(self):
        return self

    def __exit__(self, *_a):
        return False

    def read(self):
        return self._raw

    def getcode(self):
        return 200


def test_http_500_still_retries_and_keeps_diag_codes(ar_mod, tmp_path):
    dest = tmp_path / "o.png"
    err500 = HTTPError(
        "https://cloud.leonardo.ai/api/rest/v1/generations",
        500,
        "Server Error",
        {"Content-Type": "application/json"},
        BytesIO(b"{}"),
    )
    ok_body = {"url": "https://cdn.example.com/i.png"}
    with patch.object(ar_mod.time, "sleep"):
        with patch.object(ar_mod, "_download_leonardo_image_url", return_value=(True, [])):
            with patch.object(
                ar_mod,
                "urlopen",
                side_effect=[err500, _Resp200(ok_body)],
            ):
                meta: dict = {}
                ok, warns = ar_mod.leonardo_generate_image_to_path(
                    "short ",
                    dest,
                    api_key="k",
                    endpoint="https://cloud.leonardo.ai/api/rest/v1/generations",
                    meta_out=meta,
                )
    blob = " ".join(warns)
    assert ok is True
    assert "leonardo_retry_1_after:leonardo_http_5xx" in blob
    assert "leonardo_prompt_chars:" in blob
    assert "leonardo_payload_profile:standard" in blob
    assert meta.get("prompt_chars") == len("short")


def test_asset_provider_codes_include_trim_and_diag(ar_mod, tmp_path):
    gen_dir = tmp_path / "g"
    gen_dir.mkdir()
    man = gen_dir / "asset_manifest.json"
    man.write_text(
        json.dumps(
            {
                "warnings": [
                    "leonardo_prompt_trim_chars:900:895",
                    "leonardo_prompt_chars:895",
                    "leonardo_model_class:repo_default",
                    "leonardo_http_500",
                ],
                "assets": [],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    aa = build_asset_artifact(asset_manifest_path=str(man))
    codes = aa.get("asset_provider_warning_codes") or []
    assert any("leonardo_prompt_trim_chars" in c for c in codes)
    assert any("leonardo_prompt_chars:" in str(c) for c in codes)


def test_manifest_leonardo_safe_meta_v1_when_live_single(ar_mod, tmp_path):
    """Bei max_assets_live=1 enthält asset_manifest.json strukturierte Safe-Meta (ohne Prompt)."""
    pack = tmp_path / "scene_asset_pack.json"
    pack.write_text(
        json.dumps(
            {
                "scene_expansion": {
                    "expanded_scene_assets": [
                        {
                            "chapter_index": 0,
                            "beat_index": 0,
                            "visual_prompt": "test",
                            "asset_type": "image",
                        }
                    ]
                }
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    def _stub(_vp, outp, **kwargs):
        mo = kwargs.get("meta_out")
        if mo is not None:
            ar_mod._fill_leonardo_meta_out(
                mo,
                prompt_chars=4,
                prompt_words=1,
                width=512,
                height=512,
                payload_profile="mini_smoke_safe",
                body_model_id=str(DEFAULT_LEONARDO_MODEL_ID),
            )
        outp.write_bytes(b"\x89PNG\r\n\x1a\n")
        return True, ["leonardo_prompt_chars:4"]

    with patch.dict(os.environ, {"LEONARDO_API_KEY": "present"}, clear=False):
        with patch.object(ar_mod, "leonardo_generate_image_to_path", side_effect=_stub):
            out = ar_mod.run_local_asset_runner(
                pack_path=pack,
                out_root=tmp_path,
                run_id="ba337_meta",
                mode="live",
                max_assets_live=1,
            )
    mp = Path(str(out.get("manifest_path") or ""))
    blob = mp.read_text(encoding="utf-8")
    loaded = json.loads(blob)
    snap = loaded.get("leonardo_safe_request_meta_v1") or {}
    assert snap.get("prompt_chars") == 4
    assert snap.get("payload_profile") == "mini_smoke_safe"
    assert snap.get("model_id") == DEFAULT_LEONARDO_MODEL_ID
    assert snap.get("model_public_label") == DEFAULT_LEONARDO_MODEL_PUBLIC_LABEL
    assert "prompt" not in snap
