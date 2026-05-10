"""BA 32.63 — Minimaler Runway Image-to-Video-Connector für Motion-Slots (kein Logging von Secrets/Bodies)."""

from __future__ import annotations

import importlib.util
import os
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional


ROOT = Path(__file__).resolve().parents[2]


def _load_runway_smoke_module():
    """Lädt ``scripts/runway_image_to_video_smoke.py`` ohne Package-Zirkel."""
    name = "runway_image_to_video_smoke_ba3263"
    path = ROOT / "scripts" / "runway_image_to_video_smoke.py"
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError("runway_image_to_video_smoke module not loadable")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


RunwaySmokeRunner = Callable[..., Dict[str, Any]]

_DEFAULT_PROMPT_FALLBACK = (
    "cinematic documentary video clip, realistic, grounded, natural light"
)


@dataclass
class RunwayMotionClipResult:
    ok: bool
    output_path: Optional[Path] = None
    warnings: List[str] = field(default_factory=list)
    generation_mode: str = "runway_video_live"
    provider_used: str = "runway"
    safe_failure_reason: str = ""


def run_runway_motion_clip_live(
    *,
    prompt: str,
    duration_seconds: int,
    image_path: Path,
    output_path: Path,
    run_id: str,
    smoke_runner: Optional[RunwaySmokeRunner] = None,
) -> RunwayMotionClipResult:
    """
    Erzeugt einen kurzen MP4 via Runway Image-to-Video (ENV ``RUNWAY_API_KEY``).

    ``smoke_runner`` optional für Tests (Mock); Signatur wie ``run_runway_image_to_video_smoke``.
    """
    warns: List[str] = []
    out = Path(output_path).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    img = Path(image_path).resolve()

    if smoke_runner is None and not (os.environ.get("RUNWAY_API_KEY") or "").strip():
        return RunwayMotionClipResult(
            ok=False,
            output_path=None,
            warnings=warns,
            safe_failure_reason="no_api_key",
        )
    if not img.is_file():
        return RunwayMotionClipResult(
            ok=False,
            output_path=None,
            warnings=warns + ["runway_motion_image_missing"],
            safe_failure_reason="image_missing",
        )

    rid = (run_id or "").strip() or "motion_slot"
    run_fn = smoke_runner
    if run_fn is None:
        mod = _load_runway_smoke_module()
        run_fn = mod.run_runway_image_to_video_smoke

    # Smoke schreibt nach ``out_root/runway_smoke_{rid}/runway_clip.mp4``.
    out_root = out.parent
    try:
        payload = run_fn(
            image_path=img,
            prompt=(prompt or "").strip() or _DEFAULT_PROMPT_FALLBACK,
            run_id=rid,
            out_root=out_root,
            duration_seconds=int(duration_seconds),
        )
    except Exception as exc:
        reason = (type(exc).__name__ or "error").strip()[:80]
        return RunwayMotionClipResult(
            ok=False,
            output_path=None,
            warnings=warns + [f"runway_video_generation_failed:{reason}"],
            safe_failure_reason=reason,
        )

    if not isinstance(payload, dict):
        return RunwayMotionClipResult(
            ok=False,
            output_path=None,
            warnings=warns + ["runway_video_generation_failed:invalid_payload"],
            safe_failure_reason="invalid_payload",
        )

    for w in list(payload.get("warnings") or []):
        s = str(w or "").strip()
        if s and s not in warns:
            warns.append(s)

    if not payload.get("ok"):
        tag = "runway_video_generation_failed:smoke_not_ok"
        for b in list(payload.get("blocking_reasons") or []):
            sb = str(b or "").strip()[:80]
            if sb:
                tag = f"runway_video_generation_failed:{sb}"
                break
        return RunwayMotionClipResult(
            ok=False,
            output_path=None,
            warnings=warns + [tag],
            safe_failure_reason=tag.split(":", 1)[-1][:80],
        )

    src_s = str(payload.get("output_video_path") or "").strip()
    if not src_s:
        return RunwayMotionClipResult(
            ok=False,
            output_path=None,
            warnings=warns + ["runway_video_generation_failed:no_output_path"],
            safe_failure_reason="no_output_path",
        )
    src = Path(src_s).resolve()
    if not src.is_file():
        return RunwayMotionClipResult(
            ok=False,
            output_path=None,
            warnings=warns + ["runway_video_generation_failed:output_file_missing"],
            safe_failure_reason="output_file_missing",
        )
    try:
        shutil.copy2(src, out)
    except OSError as exc:
        reason = type(exc).__name__
        return RunwayMotionClipResult(
            ok=False,
            output_path=None,
            warnings=warns + [f"runway_video_generation_failed:{reason}"],
            safe_failure_reason=reason,
        )

    return RunwayMotionClipResult(
        ok=True,
        output_path=out,
        warnings=warns,
    )
