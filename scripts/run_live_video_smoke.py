#!/usr/bin/env python3
"""BA 32.56 — Automatisierter Live-Video-Smoke gegen laufenden FastAPI-Server (kein Server-Start).

- Sendet POST /founder/dashboard/video/generate mit raw_text (keine URL).
- Keine .env lesen; keine Secrets ausgeben.
- 8min/12min nur mit --allow-long-runs.
- Ohne --confirm-provider-costs: Abbruch.
"""

import argparse
import json
import re
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

_REPO_ROOT = Path(__file__).resolve().parents[1]
_REPORT_DIR = _REPO_ROOT / "output" / "live_smoke_reports"
_DEFAULT_BASE = "http://127.0.0.1:8020"
_LONG_PROFILES = frozenset({"8min", "12min"})

# Kurze DE-Textbausteine (keine URLs; redaktionell neutral).
_UNIT = (
    "Kurzer redaktioneller Absatz für einen VideoPipe-Live-Smoke. "
    "Es werden keine konkreten Zahlen oder Behauptungen erfunden; "
    "der Text dient nur der kontrollierten Skriptlänge. "
    "Thema bleibt allgemein: Zusammenhänge verständlich erklären. "
)


@dataclass(frozen=True)
class SmokeProfile:
    name: str
    duration_target_seconds: int
    max_scenes: int
    max_live_assets: int
    title: str
    raw_text: str


def _expand_raw_text(*, target_seconds: int, title: str) -> str:
    """Grobes Volumen für Ziel-Dauer (ca. 140 Wörter/Minute laut Projekt-Heuristik)."""
    words_target = max(80, int(round(target_seconds / 60.0 * 140)))
    parts: List[str] = [f"# {title}\n\n"]
    w = 0
    i = 0
    while w < words_target:
        chunk = f"{_UNIT}Abschnitt {i + 1}. "
        parts.append(chunk)
        w += len(chunk.split())
        i += 1
    return "".join(parts).strip()


def _profiles() -> Dict[str, SmokeProfile]:
    mini = SmokeProfile(
        name="mini",
        duration_target_seconds=60,
        max_scenes=3,
        max_live_assets=3,
        title="Live Smoke Mini (60s)",
        raw_text=_expand_raw_text(target_seconds=60, title="Live Smoke Mini"),
    )
    t3 = SmokeProfile(
        name="3min",
        duration_target_seconds=180,
        max_scenes=5,
        max_live_assets=5,
        title="Live Smoke 3 Minuten",
        raw_text=_expand_raw_text(target_seconds=180, title="Live Smoke 3 Minuten"),
    )
    m8 = SmokeProfile(
        name="8min",
        duration_target_seconds=480,
        max_scenes=18,
        max_live_assets=18,
        title="Live Smoke 8 Minuten",
        raw_text=_expand_raw_text(target_seconds=480, title="Live Smoke 8 Minuten"),
    )
    m12 = SmokeProfile(
        name="12min",
        duration_target_seconds=720,
        max_scenes=24,
        max_live_assets=24,
        title="Live Smoke 12 Minuten",
        raw_text=_expand_raw_text(target_seconds=720, title="Live Smoke 12 Minuten"),
    )
    return {p.name: p for p in (mini, t3, m8, m12)}


def _post_json(url: str, payload: Dict[str, Any], timeout: float = 30.0) -> Tuple[int, Dict[str, Any]]:
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = Request(
        url,
        data=data,
        method="POST",
        headers={"Content-Type": "application/json", "Accept": "application/json"},
    )
    try:
        with urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
            code = getattr(resp, "status", None) or resp.getcode()
            body = json.loads(raw) if raw.strip() else {}
            return int(code), body if isinstance(body, dict) else {"_non_json": raw[:2000]}
    except HTTPError as e:
        try:
            raw = (e.read() or b"").decode("utf-8", errors="replace")
            body = json.loads(raw) if raw.strip() else {"detail": raw[:800]}
        except Exception:
            body = {"http_error": str(e.code)}
        return int(e.code), body if isinstance(body, dict) else {"detail": str(body)}
    except (URLError, OSError, json.JSONDecodeError, TimeoutError) as e:
        return 0, {"error": type(e).__name__, "message": str(e)[:500]}


def _final_video_size_bytes(final_path: str) -> Optional[int]:
    if not final_path or not str(final_path).strip():
        return None
    p = Path(str(final_path).strip())
    try:
        if p.is_file():
            return int(p.stat().st_size)
    except OSError:
        return None
    return None


def _extract_eval_fields(payload: Dict[str, Any]) -> Dict[str, Any]:
    aa = payload.get("asset_artifact") if isinstance(payload.get("asset_artifact"), dict) else {}
    gate = aa.get("asset_quality_gate") if isinstance(aa.get("asset_quality_gate"), dict) else {}
    va = payload.get("voice_artifact") if isinstance(payload.get("voice_artifact"), dict) else {}
    ra = payload.get("readiness_audit") if isinstance(payload.get("readiness_audit"), dict) else {}
    ta = payload.get("timing_audit") if isinstance(payload.get("timing_audit"), dict) else {}
    fvp = str(payload.get("final_video_path") or "").strip()
    return {
        "ok": bool(payload.get("ok")),
        "run_id": str(payload.get("run_id") or ""),
        "warnings": list(payload.get("warnings") or []),
        "blocking_reasons": list(payload.get("blocking_reasons") or []),
        "asset_quality_status": gate.get("status"),
        "real_asset_file_count": aa.get("real_asset_file_count"),
        "placeholder_asset_count": aa.get("placeholder_asset_count"),
        "asset_manifest_file_count": aa.get("asset_manifest_file_count"),
        "generation_modes": aa.get("generation_modes"),
        "voice_ready": va.get("voice_ready"),
        "is_dummy": va.get("is_dummy"),
        "voice_file_path": va.get("voice_file_path"),
        "timing_gap_status": ta.get("timing_gap_status"),
        "fit_strategy": ta.get("fit_strategy"),
        "render_used_placeholders": ra.get("render_used_placeholders"),
        "voice_file_ready": ra.get("voice_file_ready"),
        "asset_strict_ready": ra.get("asset_strict_ready"),
        "provider_blockers": list(ra.get("provider_blockers") or []),
        "final_video_path": fvp,
        "final_video_size_bytes": _final_video_size_bytes(fvp),
    }


def classify_smoke(eval_fields: Dict[str, Any]) -> Tuple[str, List[str]]:
    """PASS | WARN | FAIL mit kurzen Gründen."""
    reasons: List[str] = []
    ok = bool(eval_fields.get("ok"))
    block = list(eval_fields.get("blocking_reasons") or [])
    aq = str(eval_fields.get("asset_quality_status") or "")
    ph_raw = eval_fields.get("placeholder_asset_count")
    ph = int(ph_raw) if ph_raw is not None else -1
    vr = eval_fields.get("voice_ready")
    dummy = eval_fields.get("is_dummy")
    rup = eval_fields.get("render_used_placeholders")
    tgs = str(eval_fields.get("timing_gap_status") or "")
    fsize = eval_fields.get("final_video_size_bytes")
    pblock = [str(x) for x in (eval_fields.get("provider_blockers") or [])]

    def _fail(msg: str) -> Tuple[str, List[str]]:
        return "FAIL", reasons + [msg]

    if not ok:
        reasons.append("ok_false")
    if block:
        reasons.append("blocking_reasons_present")
    if aq in ("placeholder_only", "missing_assets", ""):
        if aq in ("placeholder_only", "missing_assets"):
            reasons.append(f"asset_gate:{aq}")
    if vr is not True:
        reasons.append("voice_not_ready")
    if dummy is True:
        reasons.append("voice_is_dummy")
    if rup is True:
        reasons.append("render_used_placeholders")
    if fsize is None or int(fsize or 0) <= 0:
        reasons.append("final_video_missing_or_empty")

    hard_fail = (
        (not ok)
        or bool(block)
        or aq in ("placeholder_only", "missing_assets")
        or vr is not True
        or dummy is True
        or rup is True
        or fsize is None
        or int(fsize or 0) <= 0
    )
    if hard_fail:
        return "FAIL", reasons

    pass_core = (
        ok
        and aq == "production_ready"
        and ph == 0
        and vr is True
        and dummy is False
        and rup is False
        and tgs in ("ok", "minor_gap")
        and fsize is not None
        and int(fsize) > 0
    )
    if pass_core:
        return "PASS", ["criteria_met"]

    warn_reasons: List[str] = []
    if aq == "mixed_assets":
        warn_reasons.append("mixed_assets")
    if tgs == "major_gap":
        warn_reasons.append("timing_major_gap")
    pb_set = set(pblock)
    if pb_set and pb_set <= {"live_motion_not_available"}:
        warn_reasons.append("only_live_motion_blocker")
    if not warn_reasons:
        warn_reasons.append("partial_criteria")

    return "WARN", warn_reasons


_SECRET_PATTERNS = (
    re.compile(r"sk-[A-Za-z0-9]{10,}", re.I),
    re.compile(r"AIza[0-9A-Za-z_-]{20,}"),
    re.compile(r"Bearer\s+[A-Za-z0-9._-]{20,}", re.I),
)


def redact_secrets_text(s: str) -> str:
    out = s or ""
    for pat in _SECRET_PATTERNS:
        out = pat.sub("[REDACTED]", out)
    return out


def redact_payload_for_report(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {k: redact_payload_for_report(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [redact_payload_for_report(x) for x in obj]
    if isinstance(obj, str):
        return redact_secrets_text(obj)
    return obj


def build_markdown(
    *,
    profile: str,
    outcome: str,
    eval_fields: Dict[str, Any],
    http_status: int,
    recommendation: str,
) -> str:
    lines = [
        f"# Live Smoke Report — {profile}",
        "",
        f"- **Ergebnis:** {outcome}",
        f"- **HTTP:** {http_status}",
        f"- **run_id:** `{eval_fields.get('run_id') or '—'}`",
        "",
        "## Asset",
        "",
        f"- status: `{eval_fields.get('asset_quality_status')}`",
        f"- real_asset_file_count: `{eval_fields.get('real_asset_file_count')}`",
        f"- placeholder_asset_count: `{eval_fields.get('placeholder_asset_count')}`",
        f"- generation_modes: `{eval_fields.get('generation_modes')}`",
        "",
        "## Voice",
        "",
        f"- voice_ready: `{eval_fields.get('voice_ready')}`",
        f"- is_dummy: `{eval_fields.get('is_dummy')}`",
        f"- voice_file_path: `{eval_fields.get('voice_file_path') or '—'}`",
        "",
        "## Timing",
        "",
        f"- timing_gap_status: `{eval_fields.get('timing_gap_status')}`",
        f"- fit_strategy: `{eval_fields.get('fit_strategy')}`",
        "",
        "## Readiness",
        "",
        f"- render_used_placeholders: `{eval_fields.get('render_used_placeholders')}`",
        f"- voice_file_ready: `{eval_fields.get('voice_file_ready')}`",
        f"- asset_strict_ready: `{eval_fields.get('asset_strict_ready')}`",
        f"- provider_blockers: `{eval_fields.get('provider_blockers')}`",
        "",
        "## Output",
        "",
        f"- final_video_path: `{eval_fields.get('final_video_path') or '—'}`",
        f"- final_video_size_bytes: `{eval_fields.get('final_video_size_bytes')}`",
        "",
        "## Warnings",
        "",
    ]
    for w in eval_fields.get("warnings") or []:
        lines.append(f"- {redact_secrets_text(str(w))}")
    if not eval_fields.get("warnings"):
        lines.append("- —")
    lines.extend(
        [
            "",
            "## Blocking",
            "",
        ]
    )
    for b in eval_fields.get("blocking_reasons") or []:
        lines.append(f"- {redact_secrets_text(str(b))}")
    if not eval_fields.get("blocking_reasons"):
        lines.append("- —")
    lines.extend(["", "## Empfehlung", "", recommendation, ""])
    return "\n".join(lines)


def run_profile(
    *,
    profile: SmokeProfile,
    base_url: str,
    confirm_provider_costs: bool,
    post_json: Optional[Callable[[str, Dict[str, Any], float], Tuple[int, Dict[str, Any]]]] = None,
    request_timeout: float = 3600.0,
) -> Dict[str, Any]:
    post_fn = post_json if post_json is not None else _post_json
    base = (base_url or _DEFAULT_BASE).rstrip("/")
    url = f"{base}/founder/dashboard/video/generate"
    body = {
        "raw_text": profile.raw_text,
        "title": profile.title,
        "duration_target_seconds": int(profile.duration_target_seconds),
        "max_scenes": int(profile.max_scenes),
        "max_live_assets": int(profile.max_live_assets),
        "allow_live_assets": True,
        "confirm_provider_costs": bool(confirm_provider_costs),
        "voice_mode": "elevenlabs",
        "motion_mode": "static",
        "max_motion_clips": 0,
        "motion_clip_every_seconds": 60,
        "motion_clip_duration_seconds": 10,
        "allow_live_motion": False,
    }
    http_status, payload = post_fn(url, body, timeout=request_timeout)
    base_payload = payload if isinstance(payload, dict) else {}
    eval_fields = _extract_eval_fields(base_payload)
    if http_status != 200:
        eval_fields["ok"] = False
        safe_tail = json.dumps(redact_payload_for_report(base_payload), ensure_ascii=False)[:800]
        eval_fields["warnings"] = list(eval_fields.get("warnings") or []) + [
            f"http_non_200:{http_status}",
            safe_tail,
        ]
    outcome, reasons = classify_smoke(eval_fields)
    return {
        "profile": profile.name,
        "http_status": http_status,
        "outcome": outcome,
        "outcome_reasons": reasons,
        "request": {k: v for k, v in body.items() if k != "raw_text"},
        "raw_text_chars": len(profile.raw_text),
        "eval": eval_fields,
        "response_redacted": redact_payload_for_report(payload if http_status == 200 else payload),
    }


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="BA 32.56 — Live Video Smoke Runner (HTTP gegen FastAPI)")
    parser.add_argument("--base-url", default=_DEFAULT_BASE, help=f"Default: {_DEFAULT_BASE}")
    parser.add_argument(
        "--profile",
        required=True,
        choices=["mini", "3min", "8min", "12min", "all"],
        help="Smoke-Profil oder all (mini+3min; mit --allow-long-runs zusätzlich 8min+12min)",
    )
    parser.add_argument(
        "--confirm-provider-costs",
        action="store_true",
        help="Pflicht: ohne dieses Flag wird nichts ausgeführt.",
    )
    parser.add_argument(
        "--allow-long-runs",
        action="store_true",
        help="Erforderlich für 8min/12min und für all mit Langläufern.",
    )
    parser.add_argument(
        "--timeout-seconds",
        type=float,
        default=3600.0,
        help="HTTP-Timeout pro Request (Default 3600)",
    )
    args = parser.parse_args(argv)

    if not args.confirm_provider_costs:
        print("Abbruch: --confirm-provider-costs ist Pflicht für Live-Smokes.", file=sys.stderr)
        return 2

    profs = _profiles()
    to_run: List[str]
    if args.profile == "all":
        to_run = ["mini", "3min"]
        if args.allow_long_runs:
            to_run.extend(["8min", "12min"])
    else:
        if args.profile in _LONG_PROFILES and not args.allow_long_runs:
            print(
                "Abbruch: Profile 8min/12min erfordern --allow-long-runs.",
                file=sys.stderr,
            )
            return 2
        to_run = [args.profile]

    _REPORT_DIR.mkdir(parents=True, exist_ok=True)
    ts = int(time.time() * 1000)
    exit_code = 0

    for name in to_run:
        p = profs[name]
        print(f"=== Live Smoke: {name} ===", flush=True)
        result = run_profile(
            profile=p,
            base_url=args.base_url,
            confirm_provider_costs=True,
            request_timeout=float(args.timeout_seconds),
        )
        outcome = result["outcome"]
        if outcome == "FAIL":
            exit_code = 1
        elif outcome == "WARN" and exit_code == 0:
            exit_code = 3

        eval_fields = result["eval"]
        rec = (
            "Alle Kernkriterien erfüllt."
            if outcome == "PASS"
            else (
                "Ergebnis prüfen: Asset-Gate, Voice-Datei, Timing; Logs ohne Secrets einsehen."
                if outcome == "WARN"
                else "Smoke fehlgeschlagen: blocking_reasons, Provider-Keys und Pfade prüfen."
            )
        )
        md = build_markdown(
            profile=name,
            outcome=outcome,
            eval_fields=eval_fields,
            http_status=int(result["http_status"]),
            recommendation=rec,
        )
        json_path = _REPORT_DIR / f"live_smoke_{ts}_{name}.json"
        md_path = _REPORT_DIR / f"live_smoke_{ts}_{name}.md"
        report_doc = redact_payload_for_report({**result, "recommendation": rec})
        json_path.write_text(json.dumps(report_doc, ensure_ascii=False, indent=2), encoding="utf-8")
        md_path.write_text(md, encoding="utf-8")
        print(f"Report: {json_path}", flush=True)
        print(f"Report: {md_path}", flush=True)
        print(f"Outcome {name}: {outcome} ({', '.join(result['outcome_reasons'])})", flush=True)

    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
