"""Budget-Heuristik V1 für Production Jobs (BA 7.9) — nur Schätzung, keine Abbuchungen."""

from __future__ import annotations

from typing import Dict, List, NamedTuple, Optional, Tuple

from app.utils import count_words
from app.watchlist.firestore_repo import FirestoreUnavailableError, FirestoreWatchlistRepository
from app.watchlist.models import ProductionCosts, ProductionFileRecord, ProductionJob

EUR_PER_1000_WORDS_VOICE = 0.30
EUR_PER_IMAGE = 0.04
EUR_PER_VIDEO_CLIP = 0.25
EUR_THUMBNAIL_FIXED = 0.05
BUFFER_RATIO_OF_SUBTOTAL = 0.08

# BA 8.7 — konservativere Referenzbandbreite (Baseline), nicht identisch mit Schätz-Koeffizienten.
EUR_BASELINE_VOICE_PER_1K = 0.22
EUR_BASELINE_IMAGE = 0.032
EUR_BASELINE_VIDEO_CLIP = 0.20
EUR_BASELINE_THUMBNAIL = 0.04


def _compute_cost_baseline_v1(*, word_count: int, scene_count: int) -> float:
    wc = max(1, int(word_count))
    sc = max(1, int(scene_count))
    voice = round((wc / 1000.0) * EUR_BASELINE_VOICE_PER_1K, 4)
    image = round(sc * EUR_BASELINE_IMAGE, 4)
    video = round(sc * EUR_BASELINE_VIDEO_CLIP, 4)
    thumb = EUR_BASELINE_THUMBNAIL
    sub = voice + image + video + thumb
    buf = round(sub * BUFFER_RATIO_OF_SUBTOTAL, 4)
    return round(sub + buf, 4)


def _profitability_hint(*, estimated: float, baseline: float, over_budget: bool) -> str:
    if baseline <= 0.0 and estimated <= 0.0:
        return "unknown"
    base = max(baseline, 0.01)
    ratio = (estimated - baseline) / base
    if over_budget:
        return "likely_loss"
    if ratio <= -0.06:
        return "comfortable"
    if ratio <= 0.06:
        return "neutral"
    if ratio <= 0.14:
        return "tight"
    return "likely_loss"


class CategoryMoneyV1(NamedTuple):
    """Aggregierte Kostenschätzung und Hilfszeilen."""

    voice: float
    image: float
    video: float
    thumbnail: float
    buffer: float
    subtotal_before_buffer: float
    estimated_total: float
    word_count: int
    scene_count: int
    warnings: Tuple[str, ...]


def _resolve_word_scene_and_warnings(
    repo: FirestoreWatchlistRepository,
    pj: ProductionJob,
) -> Tuple[int, int, List[str]]:
    ws: List[str] = []
    gid = (pj.generated_script_id or "").strip()
    word_count = 0
    if gid:
        try:
            gs = repo.get_generated_script(gid)
        except FirestoreUnavailableError:
            raise
        if gs is not None:
            wc = getattr(gs, "word_count", 0)
            if isinstance(wc, int) and wc > 0:
                word_count = wc
            else:
                fw = getattr(gs, "full_script", "") or ""
                word_count = count_words(fw) if fw else 0
                ws.append(
                    "Kosten-Schätzung: word_count aus Volltext abgeleitet (generated_script)."
                )
    if word_count <= 0:
        ws.append(
            "Kosten-Schätzung: keine Wortanzahl ermittelbar — Voice-Anteil mit 1000 Wörtern angenommen."
        )
        word_count = 1000

    pid = (pj.id or "").strip()
    scene_count = 1
    try:
        sa = repo.get_scene_assets(pid)
        if sa is not None and sa.scenes:
            scene_count = max(1, len(sa.scenes))
        else:
            sp = repo.get_scene_plan(pid)
            if sp is not None and sp.scenes:
                scene_count = max(1, len(sp.scenes))
            else:
                rm = repo.get_render_manifest(pid)
                tl = getattr(rm, "timeline", None) if rm else None
                if tl:
                    scene_count = max(1, len(tl))
    except FirestoreUnavailableError:
        raise

    return word_count, scene_count, ws


def compute_category_totals_v1(
    *,
    repo: FirestoreWatchlistRepository,
    pj: ProductionJob,
) -> CategoryMoneyV1:
    wc, scenes, warns = _resolve_word_scene_and_warnings(repo, pj)

    voice = round((wc / 1000.0) * EUR_PER_1000_WORDS_VOICE, 4)
    image = round(scenes * EUR_PER_IMAGE, 4)
    video = round(scenes * EUR_PER_VIDEO_CLIP, 4)
    thumb = EUR_THUMBNAIL_FIXED
    sub = voice + image + video + thumb
    buf = round(sub * BUFFER_RATIO_OF_SUBTOTAL, 4)
    total = round(sub + buf, 4)

    w2 = list(warns)
    w2.append(
        "Alle Beträge sind Heuristik (V1); tatsächliche Providerpreise können abweichen."
    )

    cm = CategoryMoneyV1(
        voice=voice,
        image=image,
        video=video,
        thumbnail=thumb,
        buffer=buf,
        subtotal_before_buffer=sub,
        estimated_total=total,
        word_count=wc,
        scene_count=scenes,
        warnings=tuple(w2),
    )
    return cm


def build_production_costs_document(
    *,
    repo: FirestoreWatchlistRepository,
    pj: ProductionJob,
    now_iso: str,
    existing_created_at: Optional[str] = None,
) -> ProductionCosts:
    cat = compute_category_totals_v1(repo=repo, pj=pj)
    pid = (pj.id or "").strip()

    merged_warns = list(cat.warnings)

    baseline_total = _compute_cost_baseline_v1(
        word_count=cat.word_count, scene_count=cat.scene_count
    )
    variance = round(cat.estimated_total - baseline_total, 4)
    over_budget = baseline_total > 0.0 and variance > max(
        0.02, round(baseline_total * 0.12, 4)
    )
    if over_budget:
        merged_warns.append(
            "Kosten-Baseline überschritten (heuristisch): Schätzung deutlich über Referenzband."
        )
    step_breakdown = {
        "voice": cat.voice,
        "image": cat.image,
        "video": cat.video,
        "thumbnail": cat.thumbnail,
        "buffer": cat.buffer,
        "subtotal_before_buffer": cat.subtotal_before_buffer,
    }
    profit_hint = _profitability_hint(
        estimated=cat.estimated_total,
        baseline=baseline_total,
        over_budget=over_budget,
    )
    merged_warns.append(
        "estimated_profitability_hint ist grob und ersetzt keine Buchhaltung oder Yield-Ermittlung."
    )

    cid = existing_created_at or now_iso
    pc = ProductionCosts(
        id=pid,
        production_job_id=pid,
        estimated_total_cost=cat.estimated_total,
        actual_total_cost=0.0,
        currency="EUR",
        voice_cost_estimate=cat.voice,
        image_cost_estimate=cat.image,
        video_cost_estimate=cat.video,
        thumbnail_cost_estimate=cat.thumbnail,
        buffer_cost_estimate=cat.buffer,
        cost_baseline_expected=baseline_total,
        cost_variance=variance,
        over_budget_flag=over_budget,
        step_cost_breakdown=step_breakdown,
        estimated_profitability_hint=profit_hint,
        warnings=merged_warns,
        created_at=cid,
        updated_at=now_iso,
    )
    return pc


def estimated_cost_per_execution_job(
    pf: ProductionFileRecord,
    *,
    cat: CategoryMoneyV1,
    file_type_counts: Dict[str, int],
) -> float:
    """Teilt aggregierte Kostenschätzung auf Execution-Jobs proportional auf."""
    ft = pf.file_type
    if ft == "voice":
        return round(cat.voice / max(file_type_counts.get("voice", 0), 1), 6)
    if ft == "image":
        return round(cat.image / max(file_type_counts.get("image", 0), 1), 6)
    if ft == "video":
        return round(cat.video / max(file_type_counts.get("video", 0), 1), 6)
    if ft == "thumbnail":
        return cat.thumbnail
    if ft in ("export_json", "export_markdown", "export_csv", "manifest"):
        return 0.0
    return 0.0


def count_production_files_by_file_type(rows: List[ProductionFileRecord]) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for r in rows:
        k = r.file_type
        counts[k] = counts.get(k, 0) + 1
    return counts
