"""BA 32.75 — Thumbnail Text Overlay V1 (local, no providers).

Goals:
- Render controlled thumbnail text overlay locally on existing PNG/JPG.
- Keep image generation and typography separate (no text-in-image via OpenAI).
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


_OV_VERSION = "ba32_75_v1"

_STYLE_PRESETS = ("clean_bold", "impact_youtube", "urgent_mystery", "documentary_poster")


def _clean(s: Optional[str]) -> str:
    return (s or "").strip()


def _sanitize_warning(w: str) -> str:
    s = str(w or "").strip()
    if not s:
        return ""
    low = s.lower()
    if "bearer " in low or "authorization" in low or "sk-" in low:
        return "thumbnail_overlay_warning_sanitized"
    if len(s) > 260:
        return (s[:240] + "…").strip()
    return s


def sanitize_warnings(warnings: Any) -> List[str]:
    out: List[str] = []
    if not isinstance(warnings, list):
        return out
    for x in warnings:
        s = _sanitize_warning(str(x or ""))
        if s and s not in out:
            out.append(s)
    return out


def _upper_de(s: str) -> str:
    # keep German umlauts etc. Python upper handles Unicode reasonably.
    return (s or "").strip().upper()


def build_thumbnail_text_variants_v1(
    *,
    title: str,
    summary: Optional[str] = None,
    language: str = "de",
    max_variants: int = 3,
) -> Dict[str, Any]:
    """
    Produces up to 3 short hooky variants, max 2 lines each.
    No invented facts: only recombine title/summary wording + safe generic hooks.
    """
    warns: List[str] = []
    lang = (_clean(language) or "de").lower()
    t = _clean(title)
    s = _clean(summary)
    mv = int(max_variants or 0)
    if mv <= 0:
        mv = 3
        warns.append("thumbnail_overlay_max_variants_defaulted")
    if mv > 3:
        mv = 3
        warns.append("thumbnail_overlay_max_variants_capped_3")

    if not t:
        warns.append("thumbnail_overlay_missing_title")

    # Heuristics for German: pick strong nouns/verbs from title, avoid long sentences.
    # Extract meaningful words (letters incl. umlauts) and keep order.
    words = re.findall(r"[A-Za-zÄÖÜäöüß]+", t)
    words_up = [_upper_de(w) for w in words if w]

    def _mk(line1: str, line2: str, rid: str, rationale: str) -> Dict[str, Any]:
        l1 = _upper_de(line1)
        l2 = _upper_de(line2) if line2 else ""
        full = (l1 + ("\n" + l2 if l2 else "")).strip()
        return {
            "variant_id": rid,
            "line_1": l1,
            "line_2": l2 or None,
            "full_text": full,
            "rationale": rationale,
            "warnings": [],
        }

    variants: List[Dict[str, Any]] = []
    if lang == "de":
        # Special-case common hook: "DER MANN" + "VERSCHWAND" style if words exist
        # Try to detect "MANN" and a disappearance verb.
        wset = set(words_up)
        if "MANN" in wset:
            # stärkere, klickigere Hooks bevorzugen
            variants.append(_mk("SPURLOS", "WEG", "text_a", "Ultra-kurzer Mystery-Hook; stark, aber ohne neue Fakten."))
            variants.append(_mk("NIEMAND", "FAND IHN", "text_b", "Klickstark: offene Spannung, ohne Fakten zu erfinden."))
            variants.append(_mk("ER WAR", "EINFACH WEG", "text_c", "Emotionaler Impact-Hook (kurz, plakativ)."))
        else:
            # generic: split first 2–4 words into line1, rest into line2 (cap length)
            if words_up:
                l1 = " ".join(words_up[: min(3, len(words_up))])
                l2 = " ".join(words_up[min(3, len(words_up)) : min(6, len(words_up))])
                variants.append(_mk(l1, l2, "text_a", "Titel-Kernaussage, zweizeilig gekürzt."))
            variants.append(_mk("WAS", "PASSIERTE?", "text_b", "Generischer Mystery-Hook ohne Faktenbehauptung."))
            variants.append(_mk("DIE WAHRHEIT", "DAHINTER", "text_c", "Dokumentarischer Hook, ohne konkrete Behauptung."))
    else:
        # minimal English fallback
        if words_up:
            variants.append(_mk(" ".join(words_up[:3]), " ".join(words_up[3:6]), "text_a", "Short title-derived hook."))
        variants.append(_mk("WHAT", "HAPPENED?", "text_b", "Generic curiosity hook."))
        variants.append(_mk("THE TRUTH", "BEHIND IT", "text_c", "Documentary framing."))

    # Enforce max 2 lines and 2–5 words guideline (best-effort: don't hard fail)
    final: List[Dict[str, Any]] = []
    for v in variants:
        if len(final) >= mv:
            break
        l1 = _clean(str(v.get("line_1") or ""))
        l2 = _clean(str(v.get("line_2") or ""))
        if not l1:
            continue
        # keep short-ish
        if len(l1.split()) > 6:
            v["warnings"].append("thumbnail_overlay_line1_too_long")
        if l2 and len(l2.split()) > 6:
            v["warnings"].append("thumbnail_overlay_line2_too_long")
        v["warnings"] = sanitize_warnings(v.get("warnings") or [])
        final.append(v)

    return {
        "thumbnail_overlay_version": _OV_VERSION,
        "language": lang,
        "text_variants": final,
        "warnings": sanitize_warnings(warns),
    }


def _fit_cover(im, target_w: int, target_h: int):
    # PIL import locally (keeps module import cheap)
    from PIL import Image

    src_w, src_h = im.size
    if src_w <= 0 or src_h <= 0:
        return im.resize((target_w, target_h), resample=Image.BICUBIC)
    src_ratio = src_w / float(src_h)
    tgt_ratio = target_w / float(target_h)
    if src_ratio > tgt_ratio:
        # wider -> crop left/right
        new_h = target_h
        new_w = int(round(target_h * src_ratio))
    else:
        # taller -> crop top/bottom
        new_w = target_w
        new_h = int(round(target_w / src_ratio))
    resized = im.resize((new_w, new_h), resample=Image.BICUBIC)
    left = max(0, (new_w - target_w) // 2)
    top = max(0, (new_h - target_h) // 2)
    return resized.crop((left, top, left + target_w, top + target_h))


def _load_font(size_px: int):
    from PIL import ImageFont

    # Try common fonts; fall back to PIL default.
    candidates = [
        "arialbd.ttf",
        "Arial Bold.ttf",
        "Arial.ttf",
        "DejaVuSans-Bold.ttf",
        "DejaVuSans.ttf",
    ]
    for name in candidates:
        try:
            return ImageFont.truetype(name, size_px)
        except Exception:
            continue
    try:
        return ImageFont.load_default()
    except Exception:
        return None


def _measure(draw, font, text: str) -> Tuple[int, int]:
    # robust across Pillow versions
    try:
        bbox = draw.textbbox((0, 0), text, font=font, stroke_width=0)
        return (bbox[2] - bbox[0], bbox[3] - bbox[1])
    except Exception:
        try:
            return draw.textsize(text, font=font)
        except Exception:
            return (len(text) * 10, 20)


def render_thumbnail_overlay_v1(
    *,
    image_path: str | Path,
    output_path: str | Path,
    line_1: str,
    line_2: Optional[str] = None,
    position: str = "auto_right",
    canvas_size: Tuple[int, int] = (1280, 720),
    style_preset: str = "clean_bold",
) -> Dict[str, Any]:
    """
    Local render: fit/crop to 1280x720 and overlay bold text with outline.
    """
    from PIL import Image, ImageDraw

    warns: List[str] = []
    in_path = Path(image_path).resolve()
    out_path = Path(output_path).resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    if not in_path.is_file():
        return {
            "ok": False,
            "input_path": str(in_path),
            "output_path": str(out_path),
            "canvas_size": list(canvas_size),
            "text_lines": [],
            "position": position,
            "bytes_written": 0,
            "warnings": ["thumbnail_overlay_input_missing"],
        }

    im0 = Image.open(in_path).convert("RGBA")
    tw, th = int(canvas_size[0]), int(canvas_size[1])
    im = _fit_cover(im0, tw, th)

    draw = ImageDraw.Draw(im)
    l1 = _upper_de(line_1)
    l2 = _upper_de(line_2) if line_2 else ""
    lines = [l for l in [l1, l2] if _clean(l)]
    if not lines:
        warns.append("thumbnail_overlay_no_text_lines")

    sp = _clean(style_preset).lower() or "clean_bold"
    if sp not in _STYLE_PRESETS:
        sp = "clean_bold"
        warns.append("thumbnail_overlay_style_preset_invalid_fallback_clean_bold")

    # determine font size by trying to fit within text box width
    pad_x = int(tw * 0.06)
    pad_y = int(th * 0.08)
    box_w = int(tw * 0.46)  # right/left panel area
    if position in ("right", "auto_right"):
        x0 = tw - pad_x - box_w
        y0 = pad_y
    else:
        x0 = pad_x
        y0 = pad_y

    # preset tuning
    if sp == "impact_youtube":
        size_px = int(th * 0.16)
        stroke_mul = 0.14
        box_alpha = 90
        rotate_deg = -3.0
        gap_mul = 0.22
    elif sp == "urgent_mystery":
        size_px = int(th * 0.14)
        stroke_mul = 0.13
        box_alpha = 150
        rotate_deg = 0.0
        gap_mul = 0.26
    elif sp == "documentary_poster":
        size_px = int(th * 0.13)
        stroke_mul = 0.11
        box_alpha = 120
        rotate_deg = 0.0
        gap_mul = 0.26
    else:  # clean_bold
        size_px = int(th * 0.12)
        stroke_mul = 0.10
        box_alpha = 120
        rotate_deg = 0.0
        gap_mul = 0.28

    font = _load_font(size_px)
    if font is None:
        warns.append("thumbnail_overlay_font_missing_fallback")

    def _fits(font_try) -> bool:
        max_w = 0
        total_h = 0
        for line in lines:
            w, h = _measure(draw, font_try, line)
            max_w = max(max_w, w)
            total_h += h
        total_h += int(size_px * 0.35) * (len(lines) - 1 if len(lines) > 1 else 0)
        return max_w <= box_w and total_h <= int(th * 0.80)

    # reduce font until fits
    cur = size_px
    font_use = font
    while font_use is not None and cur > 18 and not _fits(font_use):
        cur = int(cur * 0.92)
        font_use = _load_font(cur)

    if font_use is None:
        font_use = _load_font(24)

    stroke_w = max(2, int(cur * float(stroke_mul)))
    fill = (245, 245, 245, 255)
    stroke = (10, 10, 10, 255)

    # draw semi-transparent backing box (optional but improves readability)
    try:
        # measure block
        max_w = 0
        heights = []
        for line in lines:
            w, h = _measure(draw, font_use, line)
            max_w = max(max_w, w)
            heights.append(h)
        gap = int(cur * float(gap_mul))
        block_h = sum(heights) + gap * (len(lines) - 1 if len(lines) > 1 else 0)
        bx0 = x0 - int(cur * 0.18)
        by0 = y0 - int(cur * 0.18)
        bx1 = x0 + min(box_w, max_w + int(cur * 0.36))
        by1 = y0 + block_h + int(cur * 0.22)
        overlay = Image.new("RGBA", im.size, (0, 0, 0, 0))
        od = ImageDraw.Draw(overlay)
        od.rounded_rectangle([bx0, by0, bx1, by1], radius=int(cur * 0.22), fill=(0, 0, 0, int(box_alpha)))
        im = Image.alpha_composite(im, overlay)
        draw = ImageDraw.Draw(im)
    except Exception:
        warns.append("thumbnail_overlay_backing_box_skipped")

    # draw lines (optionally rotated for impact preset)
    try:
        if abs(float(rotate_deg)) >= 1.0:
            # render text into its own layer then rotate and paste (keeps implementation simple)
            max_w = 0
            heights = []
            for line in lines:
                w, h = _measure(draw, font_use, line)
                max_w = max(max_w, w)
                heights.append(h)
            gap = int(cur * float(gap_mul))
            block_h = sum(heights) + gap * (len(lines) - 1 if len(lines) > 1 else 0)
            layer_w = min(box_w, max_w + int(cur * 0.6))
            layer_h = block_h + int(cur * 0.4)
            text_layer = Image.new("RGBA", (layer_w, layer_h), (0, 0, 0, 0))
            td = ImageDraw.Draw(text_layer)
            y = int(cur * 0.1)
            for line in lines:
                td.text((0, y), line, font=font_use, fill=fill, stroke_width=stroke_w, stroke_fill=stroke)
                _, h = _measure(td, font_use, line)
                y += h + gap
            rot = text_layer.rotate(float(rotate_deg), resample=Image.BICUBIC, expand=True)
            im.alpha_composite(rot, dest=(x0, y0))
            draw = ImageDraw.Draw(im)
        else:
            y = y0
            gap = int(cur * float(gap_mul))
            for line in lines:
                draw.text((x0, y), line, font=font_use, fill=fill, stroke_width=stroke_w, stroke_fill=stroke)
                _, h = _measure(draw, font_use, line)
                y += h + gap
    except Exception:
        # fallback without rotation
        y = y0
        gap = int(cur * float(gap_mul))
        for line in lines:
            draw.text((x0, y), line, font=font_use, fill=fill, stroke_width=stroke_w, stroke_fill=stroke)
            _, h = _measure(draw, font_use, line)
            y += h + gap

    # Save as PNG
    im.convert("RGBA").save(out_path, format="PNG")
    bw = int(out_path.stat().st_size) if out_path.is_file() else 0
    return {
        "ok": True,
        "input_path": str(in_path),
        "output_path": str(out_path),
        "canvas_size": [tw, th],
        "text_lines": lines,
        "position": position,
        "style_preset": sp,
        "bytes_written": bw,
        "warnings": sanitize_warnings(warns),
    }


@dataclass(frozen=True)
class ThumbnailOverlayResult:
    ok: bool
    selected_text_variant: Dict[str, Any]
    output_path: str
    bytes_written: int
    text_variants: List[Dict[str, Any]]
    warnings: List[str]
    thumbnail_overlay_version: str
    result_path: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "ok": bool(self.ok),
            "selected_text_variant": dict(self.selected_text_variant or {}),
            "output_path": self.output_path,
            "bytes_written": int(self.bytes_written),
            "text_variants": list(self.text_variants or []),
            "warnings": list(self.warnings or []),
            "thumbnail_overlay_version": self.thumbnail_overlay_version,
            "result_path": self.result_path,
        }


def _parse_text_override(s: Optional[str]) -> Optional[Tuple[str, Optional[str]]]:
    raw = _clean(s)
    if not raw:
        return None
    if "|" in raw:
        a, b = raw.split("|", 1)
        return (_clean(a), _clean(b) or None)
    return (raw, None)


def run_thumbnail_overlay_v1(
    *,
    image_path: str | Path,
    title: str,
    summary: Optional[str] = None,
    text_variant: Optional[str] = None,
    output_dir: str | Path,
    position: str = "auto_right",
    language: str = "de",
    style_preset: str = "impact_youtube",
) -> Dict[str, Any]:
    out_dir = Path(output_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    tv = build_thumbnail_text_variants_v1(title=title, summary=summary, language=language, max_variants=3)
    variants = tv.get("text_variants") if isinstance(tv.get("text_variants"), list) else []
    warns: List[str] = list(tv.get("warnings") or [])

    override = _parse_text_override(text_variant)
    if override is not None:
        sel = {
            "variant_id": "text_override",
            "line_1": _upper_de(override[0]),
            "line_2": _upper_de(override[1]) if override[1] else None,
            "full_text": _upper_de(override[0]) + (("\n" + _upper_de(override[1])) if override[1] else ""),
            "rationale": "CLI override",
            "warnings": [],
        }
    else:
        sel = variants[0] if variants else {"variant_id": "text_a", "line_1": "", "line_2": None, "full_text": ""}
        if not variants:
            warns.append("thumbnail_overlay_no_variants")

    out_png = out_dir / "thumbnail_final.png"
    rr = render_thumbnail_overlay_v1(
        image_path=image_path,
        output_path=out_png,
        line_1=str(sel.get("line_1") or ""),
        line_2=str(sel.get("line_2") or "") if sel.get("line_2") else None,
        position=position,
        canvas_size=(1280, 720),
        style_preset=style_preset,
    )
    warns.extend(list(rr.get("warnings") or []))
    ok = bool(rr.get("ok"))

    result = ThumbnailOverlayResult(
        ok=ok,
        selected_text_variant=sel,
        output_path=str(out_png.resolve()),
        bytes_written=int(rr.get("bytes_written") or 0),
        text_variants=variants,
        warnings=sanitize_warnings(warns),
        thumbnail_overlay_version=_OV_VERSION,
        result_path=str((out_dir / "thumbnail_overlay_result.json").resolve()),
    )
    rp = Path(result.result_path)
    rp.write_text(json.dumps(result.to_dict(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return result.to_dict()

