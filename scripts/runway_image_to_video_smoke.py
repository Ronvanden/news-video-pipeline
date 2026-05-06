"""BA 26.2 / 26.2b — Runway Image-to-Video Smoke (ein Testclip, keine Pipeline-Integration).

Liest ``RUNWAY_API_KEY`` ausschließlich aus der Umgebung. Ein Live-Lauf erzeugt
optional einen kurzen MP4-Clip aus einem lokalen Bild (offizielle REST-API:
``POST /v1/image_to_video``, Polling ``GET /v1/tasks/{id}``).

Polling: konfigurierbares Timeout, transiente HTTP-/Netzfehler werden bis zum
Timeout nur als Warnung gezählt; Abbruch per Ctrl+C schreibt ``interrupted`` ohne
Traceback. Kein Dashboard, kein Upload, kein Publishing. Keine Secrets in Logs/JSON.
"""

from __future__ import annotations

import argparse
import base64
import json
import mimetypes
import os
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.visual_plan.visual_no_text import append_no_text_guard  # noqa: E402

RESULT_SCHEMA = "runway_image_to_video_smoke_v1"
RESULT_FILENAME = "runway_smoke_result.json"
CLIP_FILENAME = "runway_clip.mp4"

DEFAULT_API_BASE = "https://api.dev.runwayml.com"
API_VERSION_HEADER = "2024-11-06"
DEFAULT_MODEL = "gen4.5"
DEFAULT_RATIO = "1280:720"

MIN_DURATION = 5
MAX_DURATION = 10
DEFAULT_POLL_TIMEOUT_SEC = 300.0
DEFAULT_POLL_INTERVAL_SEC = 5.0

_RUN_ID_RE = re.compile(r"^[A-Za-z0-9_-]{1,80}$")

EXIT_OK = 0
EXIT_FAILED = 1
EXIT_BLOCKED = 2
EXIT_INVALID = 3
EXIT_TIMEOUT = 2  # bewusst identisch zu BLOCKED (Operator-Exit 2)
EXIT_INTERRUPTED = 130

_TIMEOUT_USER_MESSAGE = (
    "Runway task may still be processing. Re-run status check later."
)


def _validate_run_id(run_id: str) -> bool:
    s = (run_id or "").strip()
    if not s or ".." in s or "/" in s or "\\" in s:
        return False
    return bool(_RUN_ID_RE.fullmatch(s))


def _write_smoke_result(out_dir: Path, payload: Dict[str, Any]) -> None:
    result_path = out_dir / RESULT_FILENAME
    result_path.parent.mkdir(parents=True, exist_ok=True)
    safe = {k: v for k, v in payload.items() if k != "exit_code"}
    result_path.write_text(json.dumps(safe, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _clamp_duration(seconds: int) -> int:
    return max(MIN_DURATION, min(MAX_DURATION, int(seconds)))


def _image_to_data_uri(image_path: Path) -> Tuple[str, str]:
    mime, _ = mimetypes.guess_type(str(image_path))
    if not mime or not mime.startswith("image/"):
        mime = "image/png"
    raw = image_path.read_bytes()
    b64 = base64.b64encode(raw).decode("ascii")
    return f"data:{mime};base64,{b64}", mime


def _headers(api_key: str) -> Dict[str, str]:
    return {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
        "X-Runway-Version": API_VERSION_HEADER,
        "Accept": "application/json",
    }


def _safe_http_error_message(exc: urllib.error.HTTPError) -> str:
    code = int(exc.code)
    # Kein Response-Body in Meldungen (könnte sensible Daten enthalten).
    return f"http_status={code}"


def _read_json_response(resp: Any) -> Tuple[int, Any]:
    code = int(getattr(resp, "status", None) or resp.getcode() or 0)
    raw = resp.read()
    try:
        data = json.loads(raw.decode("utf-8", errors="replace"))
    except json.JSONDecodeError:
        return code, {"_parse_error": True, "raw_len": len(raw)}
    return code, data


def _http_post_json(
    url: str,
    headers: Dict[str, str],
    body: Dict[str, Any],
    *,
    timeout: float = 120.0,
) -> Tuple[int, Any]:
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(url, data=data, method="POST", headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return _read_json_response(resp)
    except urllib.error.HTTPError as e:
        msg = _safe_http_error_message(e)
        return int(e.code), {"_http_error": True, "message": msg}
    except urllib.error.URLError as e:
        return 0, {"_url_error": True, "message": str(e.reason or e)[:200]}


def _http_get_json(url: str, headers: Dict[str, str], *, timeout: float = 60.0) -> Tuple[int, Any]:
    req = urllib.request.Request(url, method="GET", headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return _read_json_response(resp)
    except urllib.error.HTTPError as e:
        msg = _safe_http_error_message(e)
        return int(e.code), {"_http_error": True, "message": msg}
    except urllib.error.URLError as e:
        return 0, {"_url_error": True, "message": str(e.reason or e)[:200]}


def _download_binary(url: str, dest: Path, *, timeout: float = 300.0) -> Tuple[bool, List[str]]:
    warns: List[str] = []
    req = urllib.request.Request(url, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = resp.read()
    except urllib.error.HTTPError as e:
        return False, [f"runway_download_http:{int(e.code)}"]
    except urllib.error.URLError as e:
        return False, [f"runway_download_urlerror:{str(e.reason or e)[:120]}"]
    except OSError as e:
        return False, [f"runway_download_os:{type(e).__name__}"]
    if not data:
        return False, ["runway_download_empty"]
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(data)
    return True, warns


def _as_task_dict(data: Any) -> Dict[str, Any]:
    if not isinstance(data, dict):
        return {}
    inner = data.get("task")
    if isinstance(inner, dict):
        return inner
    return data


def _task_id_from_poll_url(task_url: str) -> str:
    if not task_url or not isinstance(task_url, str):
        return ""
    m = re.search(r"/tasks/([^/?#]+)", task_url.strip())
    return m.group(1).strip() if m else ""


def _task_id_from_create(data: Any) -> str:
    if not isinstance(data, dict):
        return ""
    tid = data.get("id") or data.get("taskId") or data.get("task_id")
    if isinstance(tid, str) and tid.strip():
        return tid.strip()
    task = data.get("task")
    if isinstance(task, dict):
        tid = task.get("id")
        if isinstance(tid, str) and tid.strip():
            return tid.strip()
    return ""


def _normalize_status(raw: Any) -> str:
    if raw is None:
        return ""
    return str(raw).strip().upper()


def _extract_output_video_urls(task: Dict[str, Any]) -> List[str]:
    out: List[str] = []
    o = task.get("output")
    if isinstance(o, list):
        for x in o:
            if isinstance(x, str) and x.startswith("http"):
                out.append(x)
            elif isinstance(x, dict):
                u = x.get("url") or x.get("uri")
                if isinstance(u, str) and u.startswith("http"):
                    out.append(u)
    elif isinstance(o, str) and o.startswith("http"):
        out.append(o)
    elif isinstance(o, dict):
        for k in ("video", "url", "uri", "videos", "urls"):
            v = o.get(k)
            if isinstance(v, str) and v.startswith("http"):
                out.append(v)
            elif isinstance(v, list):
                for item in v:
                    if isinstance(item, str) and item.startswith("http"):
                        out.append(item)
    return out


def run_runway_image_to_video_smoke(
    *,
    image_path: Optional[Path],
    prompt: str,
    run_id: str,
    out_root: Path,
    duration_seconds: int = 5,
    api_base: Optional[str] = None,
    post_json: Optional[Callable[..., Tuple[int, Any]]] = None,
    get_json: Optional[Callable[..., Tuple[int, Any]]] = None,
    save_video: Optional[Callable[[str, Path], Tuple[bool, List[str]]]] = None,
    poll_timeout_seconds: float = DEFAULT_POLL_TIMEOUT_SEC,
    poll_interval_seconds: float = DEFAULT_POLL_INTERVAL_SEC,
    no_wait: bool = False,
    existing_task_id: Optional[str] = None,
    existing_task_url: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Programm-Einstieg für CLI und Tests. ``post_json``/``get_json`` optional injizierbar (Mocks).

    Mit ``existing_task_id`` / ``existing_task_url`` wird kein Image-to-Video-POST ausgeführt,
    nur abgefragt (Resume). ``no_wait`` beendet nach erfolgreichem Create mit Status ``pending``.
    """
    prompt = append_no_text_guard((prompt or "").strip())
    rid = (run_id or "").strip()
    warnings: List[str] = []
    blocking: List[str] = []
    img_display = ""
    resume_tid = (existing_task_id or "").strip()
    resume_turl = (existing_task_url or "").strip()
    resume_mode = bool(resume_tid or resume_turl)

    api_key = (os.environ.get("RUNWAY_API_KEY") or "").strip()
    base = (api_base or DEFAULT_API_BASE).rstrip("/")
    post_fn = post_json or _http_post_json
    get_fn = get_json or _http_get_json
    save_fn = save_video or _download_binary

    poll_timeout = max(0.05, float(poll_timeout_seconds))
    poll_interval = max(0.05, float(poll_interval_seconds))

    out_dir = Path(out_root).resolve() / f"runway_smoke_{rid}"
    clip_path = out_dir / CLIP_FILENAME

    if not _validate_run_id(rid):
        blocking.append("invalid_run_id")
        payload = {
            "schema_version": RESULT_SCHEMA,
            "run_id": rid,
            "ok": False,
            "status": "failed",
            "image_path": img_display,
            "prompt": (prompt or "").strip(),
            "output_video_path": "",
            "warnings": warnings,
            "blocking_reasons": blocking,
            "metadata": {"provider": "runway", "duration_seconds": _clamp_duration(duration_seconds)},
            "exit_code": EXIT_INVALID,
        }
        _write_smoke_result(out_dir, payload)
        return payload

    dur = _clamp_duration(duration_seconds)

    if not resume_mode:
        if not image_path:
            blocking.append("image_path_missing")
            payload = {
                "schema_version": RESULT_SCHEMA,
                "run_id": rid,
                "ok": False,
                "status": "failed",
                "image_path": "",
                "prompt": (prompt or "").strip(),
                "output_video_path": "",
                "warnings": warnings,
                "blocking_reasons": blocking,
                "metadata": {"provider": "runway", "duration_seconds": dur},
                "exit_code": EXIT_FAILED,
            }
            _write_smoke_result(out_dir, payload)
            return payload
        img = Path(image_path).resolve()
        img_display = str(img)
        if not img.is_file():
            blocking.append("image_path_missing")
            payload = {
                "schema_version": RESULT_SCHEMA,
                "run_id": rid,
                "ok": False,
                "status": "failed",
                "image_path": img_display,
                "prompt": (prompt or "").strip(),
                "output_video_path": "",
                "warnings": warnings,
                "blocking_reasons": blocking,
                "metadata": {"provider": "runway", "duration_seconds": dur},
                "exit_code": EXIT_FAILED,
            }
            _write_smoke_result(out_dir, payload)
            return payload
    else:
        img = Path(image_path).resolve() if image_path else Path()
        img_display = str(img) if image_path and img.is_file() else (str(image_path) if image_path else "")

    if not api_key:
        warnings.append("runway_api_key_missing")
        blocking.append("runway_api_key_missing")
        payload = {
            "schema_version": RESULT_SCHEMA,
            "run_id": rid,
            "ok": False,
            "status": "blocked",
            "image_path": img_display,
            "prompt": (prompt or "").strip(),
            "output_video_path": "",
            "warnings": warnings,
            "blocking_reasons": blocking,
            "metadata": {"provider": "runway", "duration_seconds": dur},
            "exit_code": EXIT_BLOCKED,
        }
        _write_smoke_result(out_dir, payload)
        return payload

    hdrs = _headers(api_key)
    task_id = ""
    task_url = ""

    if resume_mode:
        if resume_turl:
            task_url = resume_turl
            task_id = resume_tid or _task_id_from_poll_url(task_url)
        else:
            task_id = resume_tid
            task_url = f"{base}/v1/tasks/{task_id}"
    else:
        try:
            data_uri, _mime = _image_to_data_uri(img)
        except OSError:
            blocking.append("image_read_failed")
            payload = {
                "schema_version": RESULT_SCHEMA,
                "run_id": rid,
                "ok": False,
                "status": "failed",
                "image_path": img_display,
                "prompt": (prompt or "").strip(),
                "output_video_path": "",
                "warnings": warnings,
                "blocking_reasons": blocking,
                "metadata": {"provider": "runway", "duration_seconds": dur},
                "exit_code": EXIT_FAILED,
            }
            _write_smoke_result(out_dir, payload)
            return payload

        body = {
            "promptImage": data_uri,
            "promptText": (prompt or " ").strip() or " ",
            "model": DEFAULT_MODEL,
            "ratio": DEFAULT_RATIO,
            "duration": dur,
        }
        create_url = f"{base}/v1/image_to_video"
        code, resp = post_fn(create_url, hdrs, body)

        if not isinstance(resp, dict) or int(code) >= 400 or resp.get("_http_error") or resp.get("_url_error"):
            blocking.append("runway_create_failed")
            if isinstance(resp, dict) and resp.get("_http_error"):
                warnings.append(f"runway_api_error:{resp.get('message', 'http')[:200]}")
            elif isinstance(resp, dict) and resp.get("_url_error"):
                warnings.append(f"runway_network:{resp.get('message', '')[:200]}")
            else:
                warnings.append(f"runway_create_http:{code}")
            payload = {
                "schema_version": RESULT_SCHEMA,
                "run_id": rid,
                "ok": False,
                "status": "failed",
                "image_path": img_display,
                "prompt": (prompt or "").strip(),
                "output_video_path": "",
                "warnings": warnings,
                "blocking_reasons": blocking,
                "metadata": {"provider": "runway", "duration_seconds": dur},
                "exit_code": EXIT_FAILED,
            }
            _write_smoke_result(out_dir, payload)
            return payload

        task_id = _task_id_from_create(resp)
        if not task_id:
            blocking.append("runway_task_id_missing")
            warnings.append("runway_create_response_unexpected")
            payload = {
                "schema_version": RESULT_SCHEMA,
                "run_id": rid,
                "ok": False,
                "status": "failed",
                "image_path": img_display,
                "prompt": (prompt or "").strip(),
                "output_video_path": "",
                "warnings": warnings,
                "blocking_reasons": blocking,
                "metadata": {"provider": "runway", "duration_seconds": dur},
                "exit_code": EXIT_FAILED,
            }
            _write_smoke_result(out_dir, payload)
            return payload

        task_url = f"{base}/v1/tasks/{task_id}"

    meta_base: Dict[str, Any] = {
        "provider": "runway",
        "duration_seconds": dur,
        "task_id": task_id,
        "task_url": task_url,
    }

    if no_wait:
        payload = {
            "schema_version": RESULT_SCHEMA,
            "run_id": rid,
            "ok": True,
            "status": "pending",
            "image_path": img_display,
            "prompt": (prompt or "").strip(),
            "output_video_path": "",
            "warnings": warnings,
            "blocking_reasons": [],
            "metadata": meta_base,
            "exit_code": EXIT_OK,
        }
        _write_smoke_result(out_dir, payload)
        return payload

    final_task: Optional[Dict[str, Any]] = None
    interrupted = False
    deadline = time.monotonic() + poll_timeout
    first_poll = True

    try:
        while True:
            if time.monotonic() >= deadline:
                break
            try:
                if not first_poll:
                    remaining = deadline - time.monotonic()
                    if remaining <= 0:
                        break
                    time.sleep(min(poll_interval, remaining))
                first_poll = False

                if time.monotonic() >= deadline:
                    break

                gc, gdata = get_fn(task_url, hdrs)
            except KeyboardInterrupt:
                interrupted = True
                break

            if not isinstance(gdata, dict) or int(gc) >= 400 or gdata.get("_http_error") or gdata.get("_url_error"):
                if "runway_poll_transient" not in warnings:
                    warnings.append("runway_poll_transient")
                continue

            task_d = _as_task_dict(gdata)
            st = _normalize_status(task_d.get("status"))
            if st in ("SUCCEEDED", "SUCCESS", "COMPLETED"):
                final_task = task_d
                break
            if st in ("FAILED", "CANCELED", "CANCELLED", "ERROR"):
                blocking.append("runway_task_failed")
                detail = task_d.get("failure") or task_d.get("error") or task_d.get("failureCode")
                if detail:
                    warnings.append(f"runway_task_terminal:{str(detail)[:200]}")
                payload = {
                    "schema_version": RESULT_SCHEMA,
                    "run_id": rid,
                    "ok": False,
                    "status": "failed",
                    "image_path": img_display,
                    "prompt": (prompt or "").strip(),
                    "output_video_path": "",
                    "warnings": warnings,
                    "blocking_reasons": blocking,
                    "metadata": meta_base,
                    "exit_code": EXIT_FAILED,
                }
                _write_smoke_result(out_dir, payload)
                return payload
    except KeyboardInterrupt:
        interrupted = True

    if interrupted:
        iw = list(warnings)
        if "runway_poll_interrupted" not in iw:
            iw.append("runway_poll_interrupted")
        payload = {
            "schema_version": RESULT_SCHEMA,
            "run_id": rid,
            "ok": False,
            "status": "interrupted",
            "image_path": img_display,
            "prompt": (prompt or "").strip(),
            "output_video_path": "",
            "warnings": iw,
            "blocking_reasons": [],
            "metadata": meta_base,
            "message": "Polling interrupted by operator (Ctrl+C). Task may still complete on Runway.",
            "recommended_action": _TIMEOUT_USER_MESSAGE,
            "exit_code": EXIT_INTERRUPTED,
        }
        _write_smoke_result(out_dir, payload)
        return payload

    if final_task is None:
        tw = list(warnings)
        if "runway_task_poll_timeout" not in tw:
            tw.append("runway_task_poll_timeout")
        payload = {
            "schema_version": RESULT_SCHEMA,
            "run_id": rid,
            "ok": False,
            "status": "timeout",
            "image_path": img_display,
            "prompt": (prompt or "").strip(),
            "output_video_path": "",
            "warnings": tw,
            "blocking_reasons": [],
            "metadata": meta_base,
            "message": _TIMEOUT_USER_MESSAGE,
            "recommended_action": _TIMEOUT_USER_MESSAGE,
            "exit_code": EXIT_TIMEOUT,
        }
        _write_smoke_result(out_dir, payload)
        return payload

    urls = _extract_output_video_urls(final_task)
    video_url = ""
    for u in urls:
        if ".mp4" in u.lower() or "video" in u.lower():
            video_url = u
            break
    if not video_url and urls:
        video_url = urls[0]

    if not video_url:
        blocking.append("runway_output_url_missing")
        warnings.append("runway_task_succeeded_without_video_url")
        payload = {
            "schema_version": RESULT_SCHEMA,
            "run_id": rid,
            "ok": False,
            "status": "failed",
            "image_path": img_display,
            "prompt": (prompt or "").strip(),
            "output_video_path": "",
            "warnings": warnings,
            "blocking_reasons": blocking,
            "metadata": meta_base,
            "exit_code": EXIT_FAILED,
        }
        _write_smoke_result(out_dir, payload)
        return payload

    ok_dl, dw = save_fn(video_url, clip_path)
    warnings.extend(dw)
    if not ok_dl:
        blocking.append("runway_download_failed")
        payload = {
            "schema_version": RESULT_SCHEMA,
            "run_id": rid,
            "ok": False,
            "status": "failed",
            "image_path": img_display,
            "prompt": (prompt or "").strip(),
            "output_video_path": "",
            "warnings": warnings,
            "blocking_reasons": blocking,
            "metadata": meta_base,
            "exit_code": EXIT_FAILED,
        }
        _write_smoke_result(out_dir, payload)
        return payload

    out_video_path_str = str(clip_path.resolve())
    payload = {
        "schema_version": RESULT_SCHEMA,
        "run_id": rid,
        "ok": True,
        "status": "completed",
        "image_path": img_display,
        "prompt": (prompt or "").strip(),
        "output_video_path": out_video_path_str,
        "warnings": warnings,
        "blocking_reasons": [],
        "metadata": meta_base,
        "exit_code": EXIT_OK,
    }
    _write_smoke_result(out_dir, payload)
    return payload


def _build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="BA 26.2 — Runway Image-to-Video Smoke (ein Clip, lokale Speicherung, kein Upload)."
    )
    p.add_argument("--image-path", type=Path, default=None, dest="image_path")
    p.add_argument("--prompt", default="", dest="prompt")
    p.add_argument("--run-id", required=True, dest="run_id")
    p.add_argument("--out-root", type=Path, default=ROOT / "output", dest="out_root")
    p.add_argument(
        "--duration-seconds",
        type=int,
        default=5,
        dest="duration_seconds",
        help=f"Clip-Dauer in Sekunden (wird auf {MIN_DURATION}–{MAX_DURATION} begrenzt).",
    )
    p.add_argument(
        "--poll-timeout-seconds",
        type=float,
        default=DEFAULT_POLL_TIMEOUT_SEC,
        dest="poll_timeout_seconds",
        help="Max. Wartezeit fürs Task-Polling (Sekunden, mindestens 0.05).",
    )
    p.add_argument(
        "--poll-interval-seconds",
        type=float,
        default=DEFAULT_POLL_INTERVAL_SEC,
        dest="poll_interval_seconds",
        help="Pause zwischen Poll-Requests (Sekunden, mindestens 0.05).",
    )
    p.add_argument(
        "--no-wait",
        action="store_true",
        dest="no_wait",
        help="Nach Task-Create nicht pollen; Status pending, task_url im Result.",
    )
    p.add_argument(
        "--task-id",
        default=None,
        dest="task_id",
        help="Nur Polling: bestehende Runway-Task-ID (kein Image-to-Video-POST).",
    )
    p.add_argument(
        "--task-url",
        default=None,
        dest="task_url",
        help="Nur Polling: volle Task-GET-URL (schlägt konstruierte URL vor).",
    )
    p.add_argument("--print-json", action="store_true", dest="print_json")
    return p


def main(argv: Optional[List[str]] = None) -> int:
    p = _build_arg_parser()
    args = p.parse_args(argv)
    resume = bool((args.task_id or "").strip() or (args.task_url or "").strip())
    if not resume:
        if args.image_path is None:
            p.error("--image-path ist erforderlich (außer bei --task-id / --task-url).")
        if not (args.prompt or "").strip():
            p.error("--prompt ist erforderlich (außer bei --task-id / --task-url).")

    rid = (args.run_id or "").strip()
    out_dir = Path(args.out_root).resolve() / f"runway_smoke_{rid}"

    def _emit_and_exit(payload: Dict[str, Any]) -> int:
        code = int(payload.get("exit_code", EXIT_FAILED))
        printable = {k: v for k, v in payload.items() if k != "exit_code"}
        if args.print_json:
            print(json.dumps(printable, ensure_ascii=False, indent=2))
        else:
            print(json.dumps({"ok": printable.get("ok"), "status": printable.get("status")}, ensure_ascii=False))
        return code

    try:
        res = run_runway_image_to_video_smoke(
            image_path=args.image_path,
            prompt=args.prompt or "",
            run_id=args.run_id,
            out_root=args.out_root,
            duration_seconds=int(args.duration_seconds),
            poll_timeout_seconds=float(args.poll_timeout_seconds),
            poll_interval_seconds=float(args.poll_interval_seconds),
            no_wait=bool(args.no_wait),
            existing_task_id=(args.task_id or "").strip() or None,
            existing_task_url=(args.task_url or "").strip() or None,
        )
    except KeyboardInterrupt:
        dur = _clamp_duration(int(args.duration_seconds))
        payload: Dict[str, Any] = {
            "schema_version": RESULT_SCHEMA,
            "run_id": rid,
            "ok": False,
            "status": "interrupted",
            "image_path": str(Path(args.image_path).resolve()) if args.image_path else "",
            "prompt": (args.prompt or "").strip(),
            "output_video_path": "",
            "warnings": ["runway_poll_interrupted"],
            "blocking_reasons": [],
            "metadata": {
                "provider": "runway",
                "duration_seconds": dur,
                "task_id": "",
                "task_url": "",
            },
            "message": "Interrupted before or outside polling loop (Ctrl+C).",
            "recommended_action": _TIMEOUT_USER_MESSAGE,
            "exit_code": EXIT_INTERRUPTED,
        }
        _write_smoke_result(out_dir, payload)
        return _emit_and_exit(payload)

    return _emit_and_exit(res)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
