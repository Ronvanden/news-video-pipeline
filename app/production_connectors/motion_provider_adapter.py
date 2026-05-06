"""BA 28.0 — Motion provider adapter (dry-run only, no provider calls).

BA 32.1 — Ein optionaler Live-Motion-Request (``allow_live_motion``) wird nur annotiert;
echte Runway-Clip-Erzeugung in dieser Pipeline ist noch nicht implementiert
(siehe ``runway_live_readiness.RUNWAY_LIVE_CONNECTOR_IMPLEMENTED`` und
``scripts/runway_image_to_video_smoke.py`` für isolierte Einzelclip-Läufe).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional

from app.production_connectors.runway_live_readiness import RUNWAY_LIVE_CONNECTOR_IMPLEMENTED

MotionProvider = Literal["runway", "seedance"]


def _s(v: Any) -> str:
    return str(v or "").strip()


def _resolve_image_path(asset: Dict[str, Any], *, base_dir: Path) -> Optional[Path]:
    for k in ("selected_asset_path", "generated_image_path", "image_path"):
        p = _s(asset.get(k))
        if not p:
            continue
        pp = Path(p)
        if not pp.is_absolute():
            pp = (base_dir / pp).resolve()
        if pp.is_file():
            return pp
    return None


def _effective_motion_prompt(asset: Dict[str, Any]) -> str:
    for k in ("prompt_used_effective", "visual_prompt_effective", "visual_prompt"):
        t = _s(asset.get(k))
        if t:
            return t
    return ""


def _pick_provider(asset: Dict[str, Any], *, provider: str) -> MotionProvider:
    p = _s(provider).lower()
    if p in ("runway", "seedance"):
        return p  # type: ignore[return-value]
    # auto
    routed = _s(asset.get("routed_visual_provider") or asset.get("provider_used")).lower()
    if routed in ("seedance",):
        return "seedance"
    return "runway"


@dataclass(frozen=True)
class MotionClipResult:
    ok: bool
    provider: str
    dry_run: bool
    scene_number: int
    input_image_path: Optional[str]
    prompt_used_effective: str
    duration_seconds: int
    clip_path: Optional[str]
    provider_status: str
    reference_payload_used: Optional[Dict[str, Any]]
    no_live_upload: bool
    warnings: List[str]
    error_code: Optional[str]
    error_message: Optional[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "ok": bool(self.ok),
            "provider": self.provider,
            "dry_run": bool(self.dry_run),
            "scene_number": int(self.scene_number),
            "input_image_path": self.input_image_path,
            "prompt_used_effective": self.prompt_used_effective,
            "duration_seconds": int(self.duration_seconds),
            "clip_path": self.clip_path,
            "provider_status": self.provider_status,
            "reference_payload_used": self.reference_payload_used,
            "no_live_upload": True,
            "warnings": list(self.warnings or []),
            "error_code": self.error_code,
            "error_message": self.error_message,
        }


def _annotate_runway_live_stub_fields(
    result: Dict[str, Any],
    *,
    allow_live_motion: bool,
) -> Dict[str, Any]:
    """Additive Felder — keine Secrets; klare Kennzeichnung Stub vs. Live-Wunsch."""
    o = dict(result)
    o["runway_live_connector_implemented"] = bool(RUNWAY_LIVE_CONNECTOR_IMPLEMENTED)
    o["runway_live_requested"] = bool(allow_live_motion)
    if allow_live_motion:
        o["runway_live_connector_status"] = (
            "live_ready" if RUNWAY_LIVE_CONNECTOR_IMPLEMENTED else "not_implemented"
        )
        w = [str(x) for x in (o.get("warnings") or []) if str(x or "").strip()]
        for tag in (
            "runway_live_connector_not_implemented",
            "motion_provider_dry_run_only_no_clip_generated",
        ):
            if tag not in w:
                w.append(tag)
        o["warnings"] = w
    else:
        o["runway_live_connector_status"] = "dry_run_only"
    return o


def build_motion_clip_result(
    asset: Dict[str, Any],
    *,
    base_dir: Path,
    provider: str = "auto",
    duration_seconds: int = 5,
    dry_run: bool = True,
    allow_live_motion: bool = False,
    live_motion_clip_index: int = 0,
    max_live_motion_clips: Optional[int] = None,
) -> Dict[str, Any]:
    a = asset if isinstance(asset, dict) else {}
    warns: List[str] = []
    sn = int(a.get("scene_number") or a.get("scene_index") or 0) or 0
    prov = _pick_provider(a, provider=provider)
    img = _resolve_image_path(a, base_dir=base_dir)
    prompt = _effective_motion_prompt(a)

    ref_used = None
    rec = a.get("recommended_reference_provider_payload")
    if isinstance(rec, dict):
        ref_used = {
            "provider": rec.get("provider"),
            "supported_mode": rec.get("supported_mode"),
            "payload_format": rec.get("payload_format"),
            "no_live_upload": True,
        }

    if img is None:
        base = MotionClipResult(
            ok=False,
            provider=prov,
            dry_run=bool(dry_run),
            scene_number=int(sn or 0),
            input_image_path=None,
            prompt_used_effective=prompt,
            duration_seconds=int(duration_seconds),
            clip_path=None,
            provider_status="missing_input_image",
            reference_payload_used=ref_used,
            no_live_upload=True,
            warnings=["input_image_missing"],
            error_code="missing_input_image",
            error_message="No input image file found for motion clip generation.",
        ).to_dict()
        return _annotate_runway_live_stub_fields(base, allow_live_motion=allow_live_motion)

    budget_ok = True
    cap_i = int(max_live_motion_clips) if max_live_motion_clips is not None else 0
    if allow_live_motion and cap_i > 0 and live_motion_clip_index >= cap_i:
        budget_ok = False
        warns.append("live_motion_clip_budget_exceeded_stub_only")

    # dry-run only: no provider call, no output file is created
    clip_stub = str((base_dir / f"scene_{int(sn or 0):03d}_{prov}_dry_run.mp4").resolve())
    warns.append("motion_provider_dry_run_only_no_clip_generated")

    base_ok = MotionClipResult(
        ok=True,
        provider=prov,
        dry_run=bool(dry_run),
        scene_number=int(sn or 0),
        input_image_path=str(img),
        prompt_used_effective=prompt,
        duration_seconds=int(duration_seconds),
        clip_path=clip_stub,
        provider_status="dry_run_ready",
        reference_payload_used=ref_used,
        no_live_upload=True,
        warnings=warns,
        error_code=None,
        error_message=None,
    ).to_dict()
    out = _annotate_runway_live_stub_fields(base_ok, allow_live_motion=allow_live_motion)
    if not budget_ok:
        out["ok"] = False
        out["provider_status"] = "live_motion_budget_exceeded"
        ec = str(out.get("error_code") or "").strip()
        if not ec:
            out["error_code"] = "live_motion_clip_budget_exceeded"
    return out

