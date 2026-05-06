"""BA 19.0 / BA 20.2 / BA 26.3 — Local Asset Runner: scene_asset_pack.json → lokale Bilder/Video + asset_manifest.json."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import time
import uuid
from io import BytesIO
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.production_connectors.leonardo_generation_result import (
    _extract_image_urls,
    fetch_leonardo_generation_result,
)
from app.founder_calibration.ba203_presets import apply_visual_style_to_prompt, resolve_visual_style_preset
from app.visual_plan.visual_policy_report import (
    build_visual_policy_fields,
    ensure_effective_prompt,
)
from app.production_connectors.openai_images_adapter import generate_openai_image_from_prompt
from app.config import settings
from app.production_connectors.leonardo_live_connector import _build_leonardo_generation_payload
from app.production_connectors.scene_pack_local_video import (
    beat_duration_seconds,
    pick_local_video_from_beat,
)

DEFAULT_LEONARDO_GENERATIONS_URL = "https://cloud.leonardo.ai/api/rest/v1/generations"
DEFAULT_MAX_ASSETS_LIVE = 3

# Browser-ähnliche Header helfen bei CDN / signierten URLs (403 ohne UA).
LEONARDO_IMAGE_DOWNLOAD_UA = (
    "Mozilla/5.0 (compatible; news-to-video-pipeline/1.0; +https://github.com/) "
    "LeonardoAssetRunner/1.0"
)


def _sorted_beats(scene_expansion: Dict[str, Any]) -> List[Dict[str, Any]]:
    raw = scene_expansion.get("expanded_scene_assets") or []
    if not isinstance(raw, list) or not raw:
        return []
    return sorted(raw, key=lambda b: (int(b.get("chapter_index", 0)), int(b.get("beat_index", 0))))


def load_scene_asset_pack(path: Path) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    if not path.is_file():
        raise FileNotFoundError(f"scene_asset_pack not found: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    se = data.get("scene_expansion")
    if not isinstance(se, dict):
        raise ValueError("scene_asset_pack.json missing object 'scene_expansion'")
    beats = _sorted_beats(se)
    if not beats:
        raise ValueError("scene_expansion.expanded_scene_assets empty or missing")
    return data, beats


def _live_env_ready() -> bool:
    return bool((os.environ.get("LEONARDO_API_KEY") or "").strip())


def _resolve_leonardo_endpoint() -> str:
    return (os.environ.get("LEONARDO_API_ENDPOINT") or "").strip() or DEFAULT_LEONARDO_GENERATIONS_URL


def _draw_placeholder_png(
    out_path: Path,
    *,
    scene_number: int,
    chapter_index: int,
    beat_index: int,
    snippet: str,
    asset_type: str = "image",
    camera_motion_hint: str = "",
) -> None:
    """
    BA 20.2b — bewusster Draft-Look: dunkler Verlauf, klare Szene, Kapitel/Beat, Prompt-Snippet, Typ-Badge.
    Kein Leonardo-Call; 960×540 bleibt kompatibel mit ffmpeg-Scale im Render.
    """
    from PIL import Image, ImageDraw, ImageFont

    w, h = 960, 540
    img = Image.new("RGB", (w, h), color=(10, 12, 18))
    draw = ImageDraw.Draw(img)

    # Vertikaler Kino-Verlauf (oben etwas heller, unten tiefer)
    for y in range(h):
        t = y / max(h - 1, 1)
        r = int(22 + (6 - 22) * t)
        g = int(26 + (8 - 26) * t)
        b = int(38 + (14 - 38) * t)
        draw.line([(0, y), (w, y)], fill=(r, g, b))

    try:
        font_title = ImageFont.truetype("arial.ttf", 36)
        font_sub = ImageFont.truetype("arial.ttf", 20)
        font_body = ImageFont.truetype("arial.ttf", 17)
        font_badge = ImageFont.truetype("arial.ttf", 14)
        font_foot = ImageFont.truetype("arial.ttf", 14)
    except OSError:
        font_title = font_sub = font_body = font_badge = font_foot = ImageFont.load_default()

    # Dezente obere Akzentlinie
    draw.rectangle([0, 0, w, 4], fill=(180, 145, 70))

    ch_label = f"Chapter {int(chapter_index) + 1}"
    beat_label = f"Beat {int(beat_index) + 1}"
    scene_line = f"SCENE {scene_number:03d}"
    meta_line = f"{ch_label}  ·  {beat_label}"

    # Schlagschatten + heller Titel
    tx, ty = 36, 52
    for ox, oy in ((3, 3), (2, 2), (1, 1)):
        draw.text((tx + ox, ty + oy), scene_line, fill=(0, 0, 0), font=font_title)
    draw.text((tx, ty), scene_line, fill=(245, 242, 235), font=font_title)

    draw.text((36, 102), meta_line, fill=(190, 198, 215), font=font_sub)

    # Asset-Typ-Badge (oben rechts)
    badge = (asset_type or "image").strip().upper()[:18] or "IMAGE"
    bbox = draw.textbbox((0, 0), badge, font=font_badge)
    bw = bbox[2] - bbox[0] + 28
    bh = bbox[3] - bbox[1] + 18
    bx0, by0 = w - bw - 28, 28
    bx1, by1 = bx0 + bw, by0 + bh
    try:
        draw.rounded_rectangle([bx0, by0, bx1, by1], radius=8, fill=(32, 36, 48), outline=(140, 125, 85), width=1)
    except AttributeError:
        draw.rectangle([bx0, by0, bx1, by1], fill=(32, 36, 48), outline=(140, 125, 85))
    draw.text((bx0 + 14, by0 + 8), badge, fill=(220, 210, 175), font=font_badge)

    y0 = 148
    snip = (snippet or "").replace("\n", " ").strip()
    if not snip:
        snip = f"({asset_type} — no visual prompt text)"
    for line in _wrap_text(snip[:420], width=54):
        draw.text((36, y0), line, fill=(205, 210, 225), font=font_body)
        y0 += 24
        if y0 > h - 120:
            break

    cam = (camera_motion_hint or "").strip()
    if cam:
        cam_line = f"Camera: {cam[:96]}"
        draw.text((36, min(y0 + 8, h - 100)), cam_line, fill=(150, 165, 190), font=font_foot)

    foot = "DRAFT PLACEHOLDER — not generated with Leonardo for this beat"
    draw.text((36, h - 42), foot, fill=(120, 128, 145), font=font_foot)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path, format="PNG")


def _wrap_text(text: str, width: int) -> List[str]:
    words = text.split()
    lines: List[str] = []
    cur: List[str] = []
    for w in words:
        test = (" ".join(cur + [w])) if cur else w
        if len(test) <= width:
            cur.append(w)
        else:
            if cur:
                lines.append(" ".join(cur))
            cur = [w]
    if cur:
        lines.append(" ".join(cur))
    return lines or [""]


def _generation_id_from_dict(data: Any) -> str:
    if not isinstance(data, dict):
        return ""
    for key in ("generationId", "generation_id", "id"):
        v = data.get(key)
        if isinstance(v, str) and v.strip():
            return v.strip()
    for nest in ("sdGenerationJob", "generate", "generation", "generations_by_pk"):
        sub = data.get(nest)
        if isinstance(sub, dict):
            gid = _generation_id_from_dict(sub)
            if gid:
                return gid
    return ""


def _redacted_download_hint(url: str) -> str:
    """Nur Host + kurzer Pfad-Prefix ohne Query/Fragment — keine signierten Token."""
    try:
        p = urlparse(url)
        host = (p.netloc or "unknown_host")[:200]
        path = (p.path or "")[:48]
        return f"{host}{path}"
    except Exception:
        return "invalid_url"


def _download_leonardo_image_url(url: str, dest_png: Path, timeout: float) -> Tuple[bool, List[str]]:
    """
    Lädt Bild-URL (Leonardo CDN / signiert) und schreibt PNG nach dest_png.
    Rückgabe: (ok, warnings) — Warnungen/Fehler niemals mit voller URL oder Query.
    """
    warns: List[str] = []
    hint = _redacted_download_hint(url)
    headers = {
        "User-Agent": LEONARDO_IMAGE_DOWNLOAD_UA,
        "Accept": "image/avif,image/webp,image/apng,image/jpeg,image/png,image/*,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        # Manche CDNs erwarten Referer von der Leonardo-Domain
        "Referer": "https://app.leonardo.ai/",
    }
    req = Request(url, headers=headers, method="GET")
    try:
        with urlopen(req, timeout=timeout) as resp:
            code = int(getattr(resp, "status", None) or resp.getcode() or 0)
            raw_ct = ""
            if resp.headers:
                raw_ct = resp.headers.get("Content-Type") or resp.headers.get("content-type") or ""
            content_type = raw_ct.split(";")[0].strip().lower() if raw_ct else ""
            data = resp.read()
    except HTTPError as exc:
        code = int(exc.code)
        reason = str(getattr(exc, "reason", "") or "")[:120]
        return False, [f"leonardo_image_download_http:status={code}:reason={reason}:target={hint}"]
    except URLError as exc:
        reason = str(getattr(exc, "reason", exc) or "")[:120]
        return False, [f"leonardo_image_download_urlerror:reason={reason}:target={hint}"]
    except (OSError, ValueError) as exc:
        return False, [f"leonardo_image_download_os:reason={type(exc).__name__}:target={hint}"]

    if code and code != 200:
        return False, [f"leonardo_image_download_http:status={code}:target={hint}"]

    if not data:
        return False, [f"leonardo_image_download_empty:target={hint}:content_type={content_type or 'unknown'}"]

    is_image_ct = bool(content_type) and content_type.startswith("image/")
    if content_type and not is_image_ct and "application/octet-stream" not in content_type:
        warns.append(f"leonardo_image_download_unexpected_content_type:{content_type[:80]}:target={hint}")

    dest_png.parent.mkdir(parents=True, exist_ok=True)

    # Raster → einheitlich PNG (Pipeline / ffmpeg erwarten konsistente Bitmap-Pfade)
    try:
        from PIL import Image

        im = Image.open(BytesIO(data))
        im.load()
        if im.mode in ("RGBA", "P", "LA"):
            im = im.convert("RGBA")
        else:
            im = im.convert("RGB")
        im.save(dest_png, format="PNG")
        return True, warns
    except Exception as exc:
        if data[:8] == b"\x89PNG\r\n\x1a\n":
            dest_png.write_bytes(data)
            return True, warns
        return False, [
            f"leonardo_image_download_decode_failed:type={type(exc).__name__}:target={hint}:content_type={content_type or 'unknown'}"
        ]


def _http_post_json(url: str, headers: Dict[str, str], body: Dict[str, Any], timeout: float) -> Tuple[int, Dict[str, Any]]:
    req = Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        method="POST",
        headers=headers,
    )
    with urlopen(req, timeout=timeout) as resp:
        raw = resp.read()
        code = getattr(resp, "status", None) or resp.getcode()
    try:
        parsed = json.loads(raw.decode("utf-8", errors="replace"))
    except json.JSONDecodeError:
        return int(code) if code is not None else 0, {"raw_text": raw[:2048].decode("utf-8", errors="replace")}
    return int(code) if code is not None else 0, parsed if isinstance(parsed, dict) else {"value": parsed}


def _leonardo_terminal_status(status: Optional[str]) -> bool:
    if not status:
        return False
    s = status.strip().upper()
    return s in ("FAILED", "ERROR", "CANCELED", "CANCELLED", "REJECTED")


def _leonardo_success_status(status: Optional[str]) -> bool:
    if not status:
        return False
    s = status.strip().upper()
    return s in ("COMPLETE", "COMPLETED", "SUCCEEDED", "SUCCESS")


def leonardo_generate_image_to_path(
    visual_prompt: str,
    dest_png: Path,
    *,
    api_key: str,
    endpoint: str,
    timeout_post: float = 60.0,
    timeout_poll: float = 45.0,
    max_polls: int = 24,
    poll_sleep: float = 4.0,
) -> Tuple[bool, List[str]]:
    """
    Ein Leonardo-Image: POST generations → optional Poll GET → Download erste URL.
    Keine Secrets in Rückgabe-Strings.
    """
    warns: List[str] = []
    body = _build_leonardo_generation_payload(
        {"prompts": [visual_prompt or " "], "style_profile": "scene_asset_pack"}
    )
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
        "accept": "application/json",
    }
    try:
        code, parsed = _http_post_json(endpoint, headers, body, timeout_post)
    except (HTTPError, URLError, OSError, ValueError) as exc:
        return False, [f"leonardo_post_failed:{type(exc).__name__}"]

    if code != 200:
        return False, [f"leonardo_post_http_{code}"]

    urls_post = _extract_image_urls(parsed)
    if urls_post:
        ok_dl, dl_warns = _download_leonardo_image_url(urls_post[0], dest_png, timeout_poll)
        warns.extend(dl_warns)
        if ok_dl:
            return True, warns
        return False, warns

    gen_id = _generation_id_from_dict(parsed)
    if not gen_id:
        return False, ["leonardo_create_missing_generation_id"]

    for poll in range(max(1, max_polls)):
        fres = fetch_leonardo_generation_result(
            gen_id,
            timeout_seconds=timeout_poll,
            max_attempts=1,
            retry_sleep_seconds=0.0,
        )
        if fres.warnings and poll == 0:
            warns.extend([w for w in fres.warnings if w not in warns])
        st = fres.generation_status
        if fres.image_urls:
            ok_dl, dl_warns = _download_leonardo_image_url(fres.image_urls[0], dest_png, timeout_poll)
            warns.extend(dl_warns)
            if ok_dl:
                return True, warns
            warns.append("leonardo_image_url_present_but_download_failed")
            return False, warns
        if _leonardo_terminal_status(st):
            return False, warns + [f"leonardo_generation_terminal:{st or 'unknown'}"]
        if _leonardo_success_status(st) and not fres.image_urls:
            warns.append("leonardo_complete_but_no_image_urls_yet")
        time.sleep(poll_sleep)

    return False, warns + ["leonardo_poll_timeout_no_image"]


def run_local_asset_runner(
    pack_path: Path,
    out_root: Path,
    *,
    run_id: str,
    mode: str,
    max_assets_live: Optional[int] = None,
    visual_style_preset: Optional[str] = None,
    leonardo_beat_fn: Optional[Callable[[str, Path], Tuple[bool, List[str]]]] = None,
    openai_images_live: bool = False,
) -> Dict[str, Any]:
    """
    Schreibt output/generated_assets_<run_id>/ und gibt Metadaten zurück.

    mode: placeholder | live
    live: LEONARDO_API_KEY; optional LEONARDO_API_ENDPOINT (Default cloud generations-URL).
    max_assets_live: nur im live-Modus — max. Anzahl Leonardo-Versuche (Default 3); Rest Placeholder.
    """
    pack_path = pack_path.resolve()
    data, beats = load_scene_asset_pack(pack_path)
    out_dir = Path(out_root).resolve() / f"generated_assets_{run_id}"
    out_dir.mkdir(parents=True, exist_ok=True)

    warnings: List[str] = []
    assets: List[Dict[str, Any]] = []
    mode_l = (mode or "placeholder").strip().lower()

    visual_style_preset_requested = (visual_style_preset or "").strip()
    visual_style_preset_effective, vs_warns = resolve_visual_style_preset(
        visual_style_preset_requested or None
    )
    warnings.extend(vs_warns)

    live_attempt_cap: Optional[int] = None
    if mode_l == "live":
        cap = DEFAULT_MAX_ASSETS_LIVE if max_assets_live is None else int(max_assets_live)
        live_attempt_cap = max(0, cap)

    env_live = _live_env_ready()
    full_live_fallback = mode_l == "live" and not env_live
    if full_live_fallback:
        warnings.append("leonardo_env_missing_fallback_placeholder")

    any_leonardo_ok = False
    beat_live_failed = False
    local_video_scene_count = 0

    for i, b in enumerate(beats, start=1):
        ch = int(b.get("chapter_index", 0))
        bi = int(b.get("beat_index", 0))
        vp = str(b.get("visual_prompt") or "")
        vp_raw = str(b.get("visual_prompt_raw") or vp)
        ov_int = b.get("overlay_intent") if isinstance(b.get("overlay_intent"), list) else []
        ts = bool(b.get("text_sensitive"))
        asset_kind = str(b.get("visual_asset_kind") or "")
        routed_v = str(b.get("routed_visual_provider") or b.get("image_provider_routed") or "")
        routed_img = str(b.get("routed_image_provider") or b.get("image_base_provider_routed") or "")
        cam = str(b.get("camera_motion_hint") or "")
        atype = str(b.get("asset_type") or "image")
        fname = f"scene_{i:03d}.png"
        fpath = out_dir / fname
        snippet = vp[:180] if vp else f"{atype} beat"
        beat_dur = beat_duration_seconds(b)

        gen_mode = "placeholder"
        vid_src, vid_warns = pick_local_video_from_beat(b, pack_path)
        warnings.extend(vid_warns)

        if vid_src is not None:
            dest_vid = out_dir / f"scene_{i:03d}{vid_src.suffix.lower()}"
            try:
                shutil.copy2(vid_src, dest_vid)
            except OSError as exc:
                warnings.append(f"local_video_copy_failed:{type(exc).__name__}:{i}")
                vid_src = None

        if vid_src is not None:
            local_video_scene_count += 1
            _draw_placeholder_png(
                fpath,
                scene_number=i,
                chapter_index=ch,
                beat_index=bi,
                snippet=snippet,
                asset_type=atype,
                camera_motion_hint=cam,
            )
            gen_mode = "local_video_ingest"
            eff_vp, _ = ensure_effective_prompt(str(b.get("visual_prompt_effective") or vp))
            asset_row: Dict[str, Any] = {
                "scene_number": i,
                "chapter_index": ch,
                "beat_index": bi,
                "asset_type": "video",
                "image_path": fname,
                "video_path": dest_vid.name,
                "visual_prompt": vp,
                "camera_motion_hint": cam,
                "generation_mode": gen_mode,
                **build_visual_policy_fields(
                    visual_prompt_raw=vp_raw,
                    visual_prompt_effective=eff_vp,
                    overlay_intent=ov_int,
                    text_sensitive=ts,
                    visual_asset_kind=asset_kind,
                    routed_visual_provider=(str(b.get("video_provider_routed") or "") or "runway"),
                    routed_image_provider=routed_img,
                ),
                "overlay_intent": ov_int,
                "text_sensitive": ts,
                "visual_asset_kind": asset_kind,
                "routed_visual_provider": (str(b.get("video_provider_routed") or "") or "runway"),
                "routed_image_provider": routed_img,
            }
            if beat_dur is not None:
                asset_row["duration_seconds"] = beat_dur
                asset_row["estimated_duration_seconds"] = beat_dur
            assets.append(asset_row)
            continue

        # BA 26.5 — OpenAI Images Provider Integration V1 (safe default: dry-run)
        routed_key = (routed_v or "").strip().lower()
        routed_img_key = (routed_img or "").strip().lower()
        wants_openai = routed_key == "openai_images" or routed_img_key == "openai_images"
        wants_render_layer = routed_key == "render_layer"
        if wants_openai or (wants_render_layer and routed_img_key == "openai_images"):
            eff_prompt, _ = ensure_effective_prompt(str(b.get("visual_prompt_effective") or vp))
            dry = True
            if mode_l == "live" and bool(openai_images_live or getattr(settings, "enable_openai_images_live", False)):
                dry = False
            res = generate_openai_image_from_prompt(
                eff_prompt,
                fpath,
                dry_run=dry,
                size=getattr(settings, "openai_image_size", "1024x1024"),
                model=getattr(settings, "openai_image_model", "gpt-image-1"),
            )
            warnings.extend(list(res.warnings or []))
            if res.ok:
                gen_mode = "openai_images_live" if not res.dry_run else "openai_images_dry_run"
                asset_row_oai: Dict[str, Any] = {
                    "scene_number": i,
                    "chapter_index": ch,
                    "beat_index": bi,
                    "asset_type": atype,
                    "image_path": fname,
                    "visual_prompt": vp,
                    "camera_motion_hint": cam,
                    "generation_mode": gen_mode,
                    "provider_used": "openai_images",
                    "provider_status": "ok" if not res.dry_run else "dry_run_ready",
                    "generated_image_path": fname,
                    "prompt_used_effective": res.prompt_used,
                    "openai_image_result": res.to_dict(),
                }
                asset_row_oai.update(
                    build_visual_policy_fields(
                        visual_prompt_raw=vp_raw,
                        visual_prompt_effective=eff_prompt,
                        overlay_intent=ov_int,
                        text_sensitive=ts,
                        visual_asset_kind=asset_kind,
                        routed_visual_provider="openai_images",
                        routed_image_provider=routed_img,
                    )
                )
                asset_row_oai["overlay_intent"] = ov_int
                asset_row_oai["text_sensitive"] = ts
                asset_row_oai["visual_asset_kind"] = asset_kind
                asset_row_oai["routed_visual_provider"] = "openai_images"
                asset_row_oai["routed_image_provider"] = routed_img
                if beat_dur is not None:
                    asset_row_oai["duration_seconds"] = beat_dur
                    asset_row_oai["estimated_duration_seconds"] = beat_dur
                assets.append(asset_row_oai)
                continue

            gen_mode = "openai_images_failed_fallback_placeholder"
            warnings.append(f"openai_images_failed_fallback_placeholder:{i}:{res.error_code or 'error'}")
            _draw_placeholder_png(
                fpath,
                scene_number=i,
                chapter_index=ch,
                beat_index=bi,
                snippet=snippet,
                asset_type=atype,
                camera_motion_hint=cam,
            )

        use_leonardo = (
            mode_l == "live"
            and env_live
            and live_attempt_cap is not None
            and (i <= live_attempt_cap)
        )
        if mode_l == "live" and env_live and live_attempt_cap is not None and i > live_attempt_cap:
            warnings.append(f"leonardo_live_max_assets_cap:{live_attempt_cap}")

        if use_leonardo:
            if visual_style_preset_effective != "default":
                vp_for_leonardo, style_warns = apply_visual_style_to_prompt(vp, visual_style_preset_requested)
                warnings.extend(style_warns)
            else:
                vp_for_leonardo = vp
            eff_vp = vp_for_leonardo
            if leonardo_beat_fn is not None:
                ok_live, lw = leonardo_beat_fn(vp_for_leonardo, fpath)
                warnings.extend(lw)
            else:
                ok_live, lw = leonardo_generate_image_to_path(
                    vp_for_leonardo,
                    fpath,
                    api_key=(os.environ.get("LEONARDO_API_KEY") or "").strip(),
                    endpoint=_resolve_leonardo_endpoint(),
                )
                warnings.extend(lw)
            if ok_live:
                gen_mode = "leonardo_live"
                any_leonardo_ok = True
            else:
                gen_mode = "leonardo_fallback_placeholder"
                beat_live_failed = True
                warnings.append(f"leonardo_live_beat_failed_fallback_placeholder:{i}")
                _draw_placeholder_png(
                    fpath,
                    scene_number=i,
                    chapter_index=ch,
                    beat_index=bi,
                    snippet=snippet,
                    asset_type=atype,
                    camera_motion_hint=cam,
                )
        else:
            _draw_placeholder_png(
                fpath,
                scene_number=i,
                chapter_index=ch,
                beat_index=bi,
                snippet=snippet,
                asset_type=atype,
                camera_motion_hint=cam,
            )
            if full_live_fallback:
                gen_mode = "leonardo_fallback_placeholder"
            else:
                gen_mode = "placeholder"

        eff_vp_local = ""
        if use_leonardo:
            eff_vp_local = str(locals().get("eff_vp") or "")
        asset_row2: Dict[str, Any] = {
            "scene_number": i,
            "chapter_index": ch,
            "beat_index": bi,
            "asset_type": atype,
            "image_path": fname,
            "visual_prompt": vp,
            "camera_motion_hint": cam,
            "generation_mode": gen_mode,
        }
        eff_vp2, _ = ensure_effective_prompt(
            str(
                eff_vp_local
                or b.get("visual_prompt_effective")
                or vp
            )
        )
        asset_row2.update(
            build_visual_policy_fields(
                visual_prompt_raw=vp_raw,
                visual_prompt_effective=eff_vp2,
                overlay_intent=ov_int,
                text_sensitive=ts,
                visual_asset_kind=asset_kind,
                routed_visual_provider=routed_v,
                routed_image_provider=routed_img,
            )
        )
        asset_row2["overlay_intent"] = ov_int
        asset_row2["text_sensitive"] = ts
        asset_row2["visual_asset_kind"] = asset_kind
        asset_row2["routed_visual_provider"] = routed_v
        asset_row2["routed_image_provider"] = routed_img
        if beat_dur is not None:
            asset_row2["duration_seconds"] = beat_dur
            asset_row2["estimated_duration_seconds"] = beat_dur
        assets.append(asset_row2)

    if mode_l == "live" and env_live:
        if any_leonardo_ok and not beat_live_failed:
            top_mode = "leonardo_live"
        else:
            top_mode = "leonardo_fallback_placeholder"
    elif full_live_fallback:
        top_mode = "leonardo_fallback_placeholder"
    else:
        top_mode = "placeholder"

    manifest = {
        "run_id": run_id,
        "source_pack": str(pack_path),
        "asset_count": len(assets),
        "generation_mode": top_mode,
        "local_video_scene_count": local_video_scene_count,
        "warnings": warnings,
        "assets": assets,
    }
    (out_dir / "asset_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return {
        "ok": True,
        "output_dir": str(out_dir),
        "asset_count": len(assets),
        "visual_style_preset_requested": visual_style_preset_requested or None,
        "visual_style_preset_effective": visual_style_preset_effective,
        "warnings": warnings,
        "manifest_path": str(out_dir / "asset_manifest.json"),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="BA 19.0/20.2 — Scene pack → lokale Bilder + asset_manifest.json")
    parser.add_argument(
        "--scene-asset-pack",
        type=Path,
        required=True,
        dest="scene_asset_pack",
        help="Pfad zu scene_asset_pack.json (BA 18.2 Export)",
    )
    parser.add_argument("--out-root", type=Path, default=ROOT / "output", dest="out_root")
    parser.add_argument("--run-id", default="", dest="run_id", help="Optional; sonst UUID")
    parser.add_argument(
        "--mode",
        choices=("placeholder", "live"),
        default="placeholder",
        help="placeholder (Default) oder live (Leonardo mit LEONARDO_API_KEY)",
    )
    parser.add_argument(
        "--max-assets",
        type=int,
        default=None,
        dest="max_assets",
        help="Nur live: max. Leonardo-Generierungen (Default 3); Placeholder für übrige Beats.",
    )
    parser.add_argument(
        "--visual-style-preset",
        default="",
        dest="visual_style_preset",
        help="BA 20.3 optional: documentary_news | cinematic_explainer | social_media_policy (nur Leonardo-Prompt)",
    )
    parser.add_argument(
        "--openai-images-live",
        action="store_true",
        dest="openai_images_live",
        help="BA 26.5: OpenAI Images live calls aktivieren (Default: dry-run placeholder, auch im --mode live).",
    )
    args = parser.parse_args()

    run_id = (args.run_id or "").strip() or str(uuid.uuid4())
    try:
        meta = run_local_asset_runner(
            args.scene_asset_pack,
            args.out_root,
            run_id=run_id,
            mode=args.mode,
            max_assets_live=args.max_assets,
            visual_style_preset=(args.visual_style_preset or "").strip() or None,
            openai_images_live=bool(args.openai_images_live),
        )
    except (OSError, ValueError, FileNotFoundError, json.JSONDecodeError) as e:
        err = {"ok": False, "error": type(e).__name__, "message": str(e), "run_id": run_id}
        print(json.dumps(err, ensure_ascii=False, indent=2))
        return 2

    print(json.dumps(meta, ensure_ascii=False, indent=2))
    return 0 if meta.get("ok") else 3


if __name__ == "__main__":
    raise SystemExit(main())
