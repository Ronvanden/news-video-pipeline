"""BA 20.8 — Validator für Produktions-Output-Bundles (Render/Subtitle/Burn-in)."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List, Optional


def _read_manifest(path: Path, warnings: List[str], blocking: List[str], strict: bool) -> Optional[Dict[str, Any]]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        msg = f"manifest_parse_failed:{path}"
        warnings.append(msg)
        if strict:
            blocking.append(msg)
        return None


def _ensure_file(path_value: str, *, label: str, checked_files: List[str], missing_files: List[str]) -> bool:
    p = (path_value or "").strip()
    if not p:
        return False
    checked_files.append(p)
    exists = Path(p).is_file()
    if not exists:
        missing_files.append(p)
    return exists


def validate_bundle(
    *,
    render_manifest: Optional[Path],
    subtitle_manifest: Optional[Path],
    burnin_manifest: Optional[Path],
    strict: bool = False,
) -> Dict[str, Any]:
    warnings: List[str] = []
    blocking: List[str] = []
    checked_manifests: List[str] = []
    checked_files: List[str] = []
    missing_files: List[str] = []

    manifests = {
        "render": render_manifest,
        "subtitle": subtitle_manifest,
        "burnin": burnin_manifest,
    }
    docs: Dict[str, Optional[Dict[str, Any]]] = {"render": None, "subtitle": None, "burnin": None}

    for name, mpath in manifests.items():
        if mpath is None:
            msg = f"manifest_missing:{name}"
            warnings.append(msg)
            if strict:
                blocking.append(msg)
            continue
        p = Path(mpath).resolve()
        checked_manifests.append(str(p))
        if not p.is_file():
            msg = f"manifest_not_found:{name}:{p}"
            warnings.append(msg)
            if strict:
                blocking.append(msg)
            continue
        docs[name] = _read_manifest(p, warnings, blocking, strict)

    rd = docs["render"] or {}
    sd = docs["subtitle"] or {}
    bd = docs["burnin"] or {}

    delivery = str(rd.get("subtitle_delivery_mode") or bd.get("subtitle_delivery_mode") or "none")
    style = str(rd.get("subtitle_style") or sd.get("subtitle_style") or bd.get("subtitle_style") or "none")
    renderer = str(rd.get("renderer_used") or bd.get("renderer_used") or "none")

    clean_video_path = str(rd.get("clean_video_path") or "")
    burnin_video_path = str(rd.get("subtitle_burnin_video_path") or bd.get("subtitle_burnin_video_path") or "")
    sidecar_srt = str(rd.get("subtitle_sidecar_srt_path") or "")
    sidecar_ass = str(rd.get("subtitle_sidecar_ass_path") or bd.get("ass_subtitle_path") or "")

    # 1) Referenzierte Dateien
    has_clean = _ensure_file(clean_video_path, label="clean_video_path", checked_files=checked_files, missing_files=missing_files)
    has_burnin = _ensure_file(burnin_video_path, label="subtitle_burnin_video_path", checked_files=checked_files, missing_files=missing_files)
    has_srt = _ensure_file(sidecar_srt, label="subtitle_sidecar_srt_path", checked_files=checked_files, missing_files=missing_files)
    has_ass = _ensure_file(sidecar_ass, label="subtitle_sidecar_ass_path", checked_files=checked_files, missing_files=missing_files)

    # 2) Rollen/Delivery-Konsistenz
    if delivery in ("burn_in", "both") and style != "none" and not burnin_video_path:
        msg = "delivery_requires_burnin_video_path"
        warnings.append(msg)
        if strict:
            blocking.append(msg)

    if delivery in ("sidecar_srt", "both") and not sidecar_srt:
        msg = "delivery_requires_sidecar_srt_path"
        warnings.append(msg)
        if strict:
            blocking.append(msg)

    # 3) clean_video_path gesetzt wenn Render-Manifest vorhanden
    if docs["render"] is not None and not clean_video_path:
        msg = "clean_video_path_missing_in_render_manifest"
        warnings.append(msg)
        if strict:
            blocking.append(msg)

    # 4) subtitle_delivery_mode konsistent
    burnin_delivery = str(bd.get("subtitle_delivery_mode") or "")
    if docs["render"] is not None and docs["burnin"] is not None and burnin_delivery and delivery:
        if burnin_delivery == "none" and delivery in ("burn_in", "both"):
            msg = "delivery_mode_inconsistent_render_vs_burnin"
            warnings.append(msg)
            if strict:
                blocking.append(msg)

    # 5) burn_in aktiv
    if delivery in ("burn_in", "both") and style != "none":
        if not has_burnin:
            msg = "subtitle_burnin_video_missing"
            warnings.append(msg)
            blocking.append(msg)
        cip = str(bd.get("clean_input_video_path") or "")
        cr = bool(bd.get("clean_video_required")) if docs["burnin"] is not None else None
        if docs["burnin"] is not None:
            if not _ensure_file(cip, label="clean_input_video_path", checked_files=checked_files, missing_files=missing_files):
                msg = "clean_input_video_missing"
                warnings.append(msg)
                if strict:
                    blocking.append(msg)
            if cr is not True:
                msg = "clean_video_required_not_true"
                warnings.append(msg)
                if strict:
                    blocking.append(msg)

    # 6) typewriter
    if style == "typewriter":
        if renderer != "ass_typewriter":
            msg = "typewriter_renderer_should_be_ass_typewriter"
            warnings.append(msg)
            if strict:
                blocking.append(msg)
        if delivery in ("burn_in", "both") and not has_ass:
            msg = "typewriter_ass_subtitle_missing"
            warnings.append(msg)
            if strict:
                blocking.append(msg)

    # 7) sidecar_srt
    if sidecar_srt and not has_srt:
        msg = "subtitle_sidecar_srt_missing"
        warnings.append(msg)
        if strict:
            blocking.append(msg)

    # 8) subtitle_style none
    if style == "none":
        if delivery not in ("none", "sidecar_srt"):
            warnings.append("subtitle_style_none_with_non_none_delivery")

    if missing_files and strict:
        blocking.extend([f"missing_file:{p}" for p in missing_files if f"missing_file:{p}" not in blocking])

    status = "pass"
    if blocking:
        status = "fail"
    elif warnings:
        status = "warning"

    out = {
        "ok": status != "fail",
        "status": status,
        "checked_manifests": checked_manifests,
        "checked_files": checked_files,
        "missing_files": missing_files,
        "warnings": warnings,
        "blocking_reasons": blocking,
        "summary": {
            "has_clean_video": has_clean,
            "has_burnin_video": has_burnin,
            "has_sidecar_srt": has_srt,
            "has_sidecar_ass": has_ass,
            "subtitle_delivery_mode": delivery,
            "renderer_used": renderer,
        },
    }
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description="BA 20.8 — Validate production output bundle manifests")
    parser.add_argument("--render-manifest", type=Path)
    parser.add_argument("--subtitle-manifest", type=Path)
    parser.add_argument("--burnin-manifest", type=Path)
    parser.add_argument("--output-json", type=Path)
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()

    result = validate_bundle(
        render_manifest=args.render_manifest,
        subtitle_manifest=args.subtitle_manifest,
        burnin_manifest=args.burnin_manifest,
        strict=bool(args.strict),
    )

    if args.output_json is not None:
        args.output_json.parent.mkdir(parents=True, exist_ok=True)
        args.output_json.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
