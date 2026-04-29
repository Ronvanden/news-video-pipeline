"""Firestore-Zugriffe für Watchlist: ``watch_channels``, ``processed_videos``, ``script_jobs``, ``generated_scripts``, ``review_results``, ``production_jobs``, ``scene_plans``, ``scene_assets``, ``voice_plans``, ``render_manifests``.

Client ist injizierbar (Unit-Tests mit Mock).
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional

from app.watchlist.models import (
    GeneratedScript,
    ProcessedVideo,
    ProductionJob,
    RenderManifest,
    ReviewResultStored,
    SceneAssets,
    ScenePlan,
    ScriptJob,
    VoicePlan,
    WatchlistChannel,
)

logger = logging.getLogger(__name__)

COLLECTION_NAME = "watch_channels"
PROCESSED_VIDEOS_COLLECTION = "processed_videos"
SCRIPT_JOBS_COLLECTION = "script_jobs"
GENERATED_SCRIPTS_COLLECTION = "generated_scripts"
REVIEW_RESULTS_COLLECTION = "review_results"
PRODUCTION_JOBS_COLLECTION = "production_jobs"
SCENE_PLANS_COLLECTION = "scene_plans"
SCENE_ASSETS_COLLECTION = "scene_assets"
VOICE_PLANS_COLLECTION = "voice_plans"
RENDER_MANIFESTS_COLLECTION = "render_manifests"
WATCHLIST_META_COLLECTION = "watchlist_meta"
WATCHLIST_META_AUTOMATION_DOC = "automation"


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def get_firestore_client():
    """Erstellt einen Firestore-Client (ADC). Nutzt die Datenbank-ID aus ``Settings``.

    Named Database (Umgebungsvariable ``FIRESTORE_DATABASE``, Standard ``watchlist``).

    Raises:
        RuntimeError: Bei fehlendem Paket oder nicht initialisierbarem Client (ohne Secrets loggen).
    """
    try:
        from google.cloud import firestore as gcf  # type: ignore
    except ImportError as e:
        raise RuntimeError(
            "google-cloud-firestore is not installed."
        ) from e
    try:
        from app.config import settings

        return gcf.Client(database=settings.firestore_database)
    except Exception as e:
        logger.warning(
            "Firestore client init failed: type=%s check ADC, project, or database id",
            type(e).__name__,
        )
        raise RuntimeError("Could not initialize Firestore client.") from e


ClientFactory = Callable[[], Any]


class FirestoreUnavailableError(Exception):
    """Firestore nicht erreichbar oder API-Fehler (keine Secrets im message)."""


class FirestoreWatchlistRepository:
    """Kapselt CRUD für ``watch_channels`` mit ``channel_id`` als Document-ID."""

    def __init__(self, client: Any = None, client_factory: Optional[ClientFactory] = None):
        self._client = client
        self._client_factory = client_factory or get_firestore_client

    def _ensure_client(self):
        if self._client is None:
            self._client = self._client_factory()
        return self._client

    def _collection_ref(self):
        return self._ensure_client().collection(COLLECTION_NAME)

    @staticmethod
    def _doc_to_dict(data: Dict[str, Any], doc_id: str) -> Dict[str, Any]:
        if not data:
            return {}
        out = dict(data)
        out["id"] = doc_id
        return out

    def upsert_watch_channel(self, doc_id: str, data: Dict[str, Any]) -> None:
        """Legt an oder überschreibt ein Kanal-Dokument (Document-ID = UC…)."""
        try:
            self._collection_ref().document(doc_id).set(data)
        except Exception as e:
            logger.warning("Firestore set failed: type=%s", type(e).__name__)
            raise FirestoreUnavailableError(
                "Firestore is not reachable or rejected the write."
            ) from e

    def get_watch_channel_doc(self, channel_id: str) -> Optional[Dict[str, Any]]:
        try:
            snap = self._collection_ref().document(channel_id).get()
        except Exception as e:
            logger.warning("Firestore get failed: type=%s", type(e).__name__)
            raise FirestoreUnavailableError(
                "Firestore is not reachable."
            ) from e
        if not snap.exists:
            return None
        merged = self._doc_to_dict(snap.to_dict() or {}, snap.id)
        return merged

    def list_watch_channel_docs(self) -> List[Dict[str, Any]]:
        try:
            snaps = self._collection_ref().stream()
        except Exception as e:
            logger.warning("Firestore stream failed: type=%s", type(e).__name__)
            raise FirestoreUnavailableError(
                "Firestore is not reachable."
            ) from e
        out: List[Dict[str, Any]] = []
        for snap in snaps:
            merged = self._doc_to_dict(snap.to_dict() or {}, snap.id)
            out.append(merged)
        return out

    def _processed_collection_ref(self):
        return self._ensure_client().collection(PROCESSED_VIDEOS_COLLECTION)

    def _script_jobs_collection_ref(self):
        return self._ensure_client().collection(SCRIPT_JOBS_COLLECTION)

    def _generated_scripts_collection_ref(self):
        return self._ensure_client().collection(GENERATED_SCRIPTS_COLLECTION)

    def get_script_job(self, job_id: str) -> Optional[ScriptJob]:
        try:
            snap = self._script_jobs_collection_ref().document(job_id).get()
        except Exception as e:
            logger.warning("Firestore script_jobs get failed: type=%s", type(e).__name__)
            raise FirestoreUnavailableError(
                "Firestore is not reachable."
            ) from e
        if not snap.exists:
            return None
        data = snap.to_dict() or {}
        merged = self._doc_to_dict(data, snap.id)
        try:
            return ScriptJob.model_validate(merged)
        except Exception as e:
            logger.warning(
                "invalid script_jobs doc: job_id=%s type=%s",
                snap.id,
                type(e).__name__,
            )
            return None

    def create_script_job(self, job: ScriptJob) -> ScriptJob:
        doc_id = job.video_id
        try:
            self._script_jobs_collection_ref().document(doc_id).set(job.model_dump())
        except Exception as e:
            logger.warning("Firestore script_jobs set failed: type=%s", type(e).__name__)
            raise FirestoreUnavailableError(
                "Firestore is not reachable or rejected the write."
            ) from e
        return job

    def list_script_jobs(self, limit: int = 50) -> List[ScriptJob]:
        """Listet Jobs, neuestes ``created_at`` zuerst (Sortierung Client-seitig)."""
        lim = max(1, min(int(limit), 500))
        try:
            snaps = self._script_jobs_collection_ref().stream()
        except Exception as e:
            logger.warning("Firestore script_jobs stream failed: type=%s", type(e).__name__)
            raise FirestoreUnavailableError(
                "Firestore is not reachable."
            ) from e
        out: List[ScriptJob] = []
        for snap in snaps:
            merged = self._doc_to_dict(snap.to_dict() or {}, snap.id)
            try:
                out.append(ScriptJob.model_validate(merged))
            except Exception as e:
                logger.warning(
                    "skip invalid script_jobs row: doc_id=%s type=%s",
                    snap.id,
                    type(e).__name__,
                )
                continue
        out.sort(key=lambda j: j.created_at or "", reverse=True)
        return out[:lim]

    def mark_script_job_running(self, job_id: str) -> None:
        try:
            from google.cloud.firestore import Increment

            now = _utc_now_iso()
            self._script_jobs_collection_ref().document(job_id).update(
                {
                    "status": "running",
                    "started_at": now,
                    "last_attempt_at": now,
                    "attempt_count": Increment(1),
                }
            )
        except Exception as e:
            logger.warning(
                "Firestore script_jobs mark running failed: type=%s", type(e).__name__
            )
            raise FirestoreUnavailableError(
                "Firestore is not reachable or rejected the update."
            ) from e

    def mark_script_job_completed(self, job_id: str, generated_script_id: str) -> None:
        try:
            self._script_jobs_collection_ref().document(job_id).update(
                {
                    "status": "completed",
                    "completed_at": _utc_now_iso(),
                    "generated_script_id": generated_script_id,
                    "error": "",
                    "error_code": "",
                }
            )
        except Exception as e:
            logger.warning(
                "Firestore script_jobs mark completed failed: type=%s", type(e).__name__
            )
            raise FirestoreUnavailableError(
                "Firestore is not reachable or rejected the update."
            ) from e

    def mark_script_job_failed(
        self,
        job_id: str,
        error: str,
        *,
        error_code: Optional[str] = None,
    ) -> None:
        err_short = (error or "")[:2000]
        ec = error_code if error_code is not None else error
        ec_short = (ec or "")[:200]
        try:
            self._script_jobs_collection_ref().document(job_id).update(
                {
                    "status": "failed",
                    "completed_at": _utc_now_iso(),
                    "error": err_short,
                    "error_code": ec_short,
                }
            )
        except Exception as e:
            logger.warning(
                "Firestore script_jobs mark failed failed: type=%s", type(e).__name__
            )
            raise FirestoreUnavailableError(
                "Firestore is not reachable or rejected the update."
            ) from e

    def create_generated_script(self, script: GeneratedScript) -> GeneratedScript:
        doc_id = script.id
        try:
            self._generated_scripts_collection_ref().document(doc_id).set(
                script.model_dump()
            )
        except Exception as e:
            logger.warning(
                "Firestore generated_scripts set failed: type=%s", type(e).__name__
            )
            raise FirestoreUnavailableError(
                "Firestore is not reachable or rejected the write."
            ) from e
        return script

    def get_generated_script(self, script_id: str) -> Optional[GeneratedScript]:
        try:
            snap = self._generated_scripts_collection_ref().document(script_id).get()
        except Exception as e:
            logger.warning(
                "Firestore generated_scripts get failed: type=%s", type(e).__name__
            )
            raise FirestoreUnavailableError(
                "Firestore is not reachable."
            ) from e
        if not snap.exists:
            return None
        data = snap.to_dict() or {}
        merged = self._doc_to_dict(data, snap.id)
        try:
            return GeneratedScript.model_validate(merged)
        except Exception as e:
            logger.warning(
                "invalid generated_scripts doc: script_id=%s type=%s",
                snap.id,
                type(e).__name__,
            )
            return None

    def update_processed_video_status(
        self,
        video_id: str,
        status: str,
        *,
        script_job_id: Optional[str] = None,
        generated_script_id: Optional[str] = None,
    ) -> None:
        payload: Dict[str, Any] = {"status": status}
        if script_job_id is not None:
            payload["script_job_id"] = script_job_id
        if generated_script_id is not None:
            payload["generated_script_id"] = generated_script_id
        try:
            self._processed_collection_ref().document(video_id).update(payload)
        except Exception as e:
            logger.warning(
                "Firestore processed_videos status update failed: type=%s",
                type(e).__name__,
            )
            raise FirestoreUnavailableError(
                "Firestore is not reachable or rejected the update."
            ) from e

    def update_processed_video_job_link(self, video_id: str, script_job_id: str) -> None:
        try:
            self._processed_collection_ref().document(video_id).update(
                {"script_job_id": script_job_id}
            )
        except Exception as e:
            logger.warning(
                "Firestore processed_videos job link update failed: type=%s",
                type(e).__name__,
            )
            raise FirestoreUnavailableError(
                "Firestore is not reachable or rejected the update."
            ) from e

    def get_watch_channel(self, channel_id: str) -> Optional[WatchlistChannel]:
        doc = self.get_watch_channel_doc(channel_id)
        if not doc:
            return None
        try:
            return WatchlistChannel.model_validate(doc)
        except Exception as e:
            logger.warning(
                "invalid watch_channels document: doc_id=%s type=%s",
                channel_id,
                type(e).__name__,
            )
            return None

    def get_processed_video(self, video_id: str) -> Optional[ProcessedVideo]:
        try:
            snap = self._processed_collection_ref().document(video_id).get()
        except Exception as e:
            logger.warning("Firestore processed_videos get failed: type=%s", type(e).__name__)
            raise FirestoreUnavailableError(
                "Firestore is not reachable."
            ) from e
        if not snap.exists:
            return None
        data = snap.to_dict() or {}
        merged = self._doc_to_dict(data, snap.id)
        try:
            return ProcessedVideo.model_validate(merged)
        except Exception as e:
            logger.warning(
                "invalid processed_videos doc: video_id=%s type=%s",
                snap.id,
                type(e).__name__,
            )
            return None

    def create_processed_video(self, video: ProcessedVideo) -> ProcessedVideo:
        doc_id = video.video_id
        try:
            self._processed_collection_ref().document(doc_id).set(video.model_dump())
        except Exception as e:
            logger.warning("Firestore processed_videos set failed: type=%s", type(e).__name__)
            raise FirestoreUnavailableError(
                "Firestore is not reachable or rejected the write."
            ) from e
        return video

    def delete_processed_video(self, video_id: str) -> bool:
        """Entfernt genau einen ``processed_videos``-Eintrag — für Dev/Recheck (ein Video)."""
        try:
            ref = self._processed_collection_ref().document(video_id)
            snap = ref.get()
        except Exception as e:
            logger.warning("Firestore processed_videos get failed: type=%s", type(e).__name__)
            raise FirestoreUnavailableError(
                "Firestore is not reachable."
            ) from e
        if not snap.exists:
            return False
        try:
            ref.delete()
        except Exception as e:
            logger.warning(
                "Firestore processed_videos delete failed: type=%s", type(e).__name__
            )
            raise FirestoreUnavailableError(
                "Firestore is not reachable or rejected the delete."
            ) from e
        return True

    def list_pending_script_jobs(self, limit: int) -> List[ScriptJob]:
        """Pending Jobs, FIFO (ältestes ``created_at`` zuerst), max ``limit`` (1 … 50).

        Nutzt eine Firestore-Query ``status == pending`` + ``order_by(created_at)`` +
        serverseitiges ``limit`` (Composite-Index erforderlich, siehe DEPLOYMENT.md).
        """
        lim = max(1, min(int(limit), 50))
        try:
            q = (
                self._script_jobs_collection_ref()
                .where("status", "==", "pending")
                .order_by("created_at")
                .limit(lim)
            )
            snaps = q.stream()
        except Exception as e:
            logger.warning(
                "Firestore script_jobs pending query failed: type=%s", type(e).__name__
            )
            raise FirestoreUnavailableError(
                "Firestore is not reachable."
            ) from e
        pending: List[ScriptJob] = []
        for snap in snaps:
            merged = self._doc_to_dict(snap.to_dict() or {}, snap.id)
            try:
                j = ScriptJob.model_validate(merged)
            except Exception:
                logger.warning(
                    "skip invalid script_jobs row: doc_id=%s", snap.id
                )
                continue
            if j.status == "pending":
                pending.append(j)
        return pending

    def list_processed_videos_by_channel(self, channel_id: str) -> List[ProcessedVideo]:
        try:
            snaps = (
                self._processed_collection_ref()
                .where("channel_id", "==", channel_id)
                .stream()
            )
        except Exception as e:
            logger.warning(
                "Firestore processed_videos query failed: type=%s", type(e).__name__
            )
            raise FirestoreUnavailableError(
                "Firestore is not reachable."
            ) from e
        out: List[ProcessedVideo] = []
        for snap in snaps:
            merged = self._doc_to_dict(snap.to_dict() or {}, snap.id)
            try:
                out.append(ProcessedVideo.model_validate(merged))
            except Exception as e:
                logger.warning(
                    "skip invalid processed_videos row: doc_id=%s type=%s",
                    snap.id,
                    type(e).__name__,
                )
                continue
        return out

    def _meta_doc_ref(self):
        return (
            self._ensure_client()
            .collection(WATCHLIST_META_COLLECTION)
            .document(WATCHLIST_META_AUTOMATION_DOC)
        )

    def get_last_automation_cycle_at(self) -> Optional[str]:
        try:
            snap = self._meta_doc_ref().get()
        except Exception as e:
            logger.warning(
                "Firestore watchlist_meta get failed: type=%s", type(e).__name__
            )
            raise FirestoreUnavailableError(
                "Firestore is not reachable."
            ) from e
        if not snap.exists:
            return None
        data = snap.to_dict() or {}
        raw = data.get("last_run_cycle_at")
        return raw if isinstance(raw, str) and raw.strip() else None

    def set_last_automation_cycle_at(self, iso_timestamp: str) -> None:
        try:
            self._meta_doc_ref().set(
                {"last_run_cycle_at": iso_timestamp}, merge=True
            )
        except Exception as e:
            logger.warning(
                "Firestore watchlist_meta set failed: type=%s", type(e).__name__
            )
            raise FirestoreUnavailableError(
                "Firestore is not reachable or rejected the write."
            ) from e

    def list_running_script_jobs(self) -> List[ScriptJob]:
        try:
            snaps = (
                self._script_jobs_collection_ref()
                .where("status", "==", "running")
                .stream()
            )
        except Exception as e:
            logger.warning(
                "Firestore script_jobs running query failed: type=%s", type(e).__name__
            )
            raise FirestoreUnavailableError(
                "Firestore is not reachable."
            ) from e
        out: List[ScriptJob] = []
        for snap in snaps:
            merged = self._doc_to_dict(snap.to_dict() or {}, snap.id)
            try:
                out.append(ScriptJob.model_validate(merged))
            except Exception:
                logger.warning("skip invalid script_jobs row: doc_id=%s", snap.id)
                continue
        return out

    @staticmethod
    def _aggregation_count(query) -> int:
        """Gibt die Anzahl zurück oder ``-1`` bei Fehler (z. B. fehlender Index).

        Wertet alle ``AggregationResult``-Batches aus; Aliase vom Server können
        von ``all`` abweichen — dann wird der erste Zählwert genutzt.
        """
        try:
            from google.cloud.firestore_v1.aggregation import (
                AggregationQuery,
                AggregationResult,
            )
        except Exception:
            return -1
        try:
            aq = AggregationQuery(query).count(alias="all")
            raw = aq.get()
            batches = list(raw) if raw is not None else []
            for batch in batches:
                if isinstance(batch, AggregationResult):
                    return int(batch.value)
                if not isinstance(batch, (list, tuple)):
                    continue
                for agg in batch:
                    if getattr(agg, "alias", None) == "all":
                        return int(agg.value)
                for agg in batch:
                    return int(agg.value)
        except Exception as e:
            logger.warning(
                "Firestore aggregation count failed: type=%s", type(e).__name__
            )
            return -1
        return -1

    def _count_query_stream_fallback(self, query, *, cap: int = 65535) -> int:
        """Begrenzte Zählpass per Stream, wenn Aggregation nicht verfügbar ist."""
        try:
            n = 0
            for _ in query.limit(cap + 1).stream():
                n += 1
                if n > cap:
                    return -1
            return n
        except Exception as e:
            logger.warning(
                "Firestore stream count fallback failed: type=%s", type(e).__name__
            )
            return -1

    def count_collection(self, collection_name: str) -> int:
        ref = self._ensure_client().collection(collection_name)
        agg = self._aggregation_count(ref)
        if agg >= 0:
            return agg
        return self._count_query_stream_fallback(ref)

    def count_processed_videos_by_status(self, status: str) -> int:
        q = self._processed_collection_ref().where("status", "==", status)
        agg = self._aggregation_count(q)
        if agg >= 0:
            return agg
        return self._count_query_stream_fallback(q)

    def count_processed_videos_by_skip_reason(self, skip_reason: str) -> int:
        q = self._processed_collection_ref().where(
            "skip_reason", "==", skip_reason
        )
        agg = self._aggregation_count(q)
        if agg >= 0:
            return agg
        return self._count_query_stream_fallback(q)

    def count_script_jobs_by_status(self, status: str) -> int:
        q = self._script_jobs_collection_ref().where("status", "==", status)
        agg = self._aggregation_count(q)
        if agg >= 0:
            return agg
        return self._count_query_stream_fallback(q)

    def get_latest_completed_job_completed_at(self) -> Optional[str]:
        try:
            from google.cloud.firestore import Query

            q = (
                self._script_jobs_collection_ref()
                .where("status", "==", "completed")
                .order_by("completed_at", direction=Query.DESCENDING)
                .limit(1)
            )
            snaps = list(q.stream())
        except Exception as e:
            logger.warning(
                "Firestore script_jobs latest completed query failed: type=%s",
                type(e).__name__,
            )
            return None
        if not snaps:
            return None
        merged = self._doc_to_dict(snaps[0].to_dict() or {}, snaps[0].id)
        try:
            job = ScriptJob.model_validate(merged)
        except Exception:
            return None
        ca = job.completed_at
        return ca if isinstance(ca, str) and ca.strip() else None

    def reset_script_job_to_pending(self, job_id: str) -> None:
        try:
            from google.cloud.firestore import DELETE_FIELD

            self._script_jobs_collection_ref().document(job_id).update(
                {
                    "status": "pending",
                    "error": "",
                    "error_code": "",
                    "started_at": DELETE_FIELD,
                    "completed_at": DELETE_FIELD,
                }
            )
        except Exception as e:
            logger.warning(
                "Firestore script_jobs reset pending failed: type=%s", type(e).__name__
            )
            raise FirestoreUnavailableError(
                "Firestore is not reachable or rejected the update."
            ) from e

    def mark_script_job_skipped_manual(
        self, job_id: str, *, error_code: str, error_message: str
    ) -> None:
        err_short = (error_message or "")[:2000]
        ec_short = (error_code or "")[:200]
        try:
            self._script_jobs_collection_ref().document(job_id).update(
                {
                    "status": "skipped",
                    "completed_at": _utc_now_iso(),
                    "error": err_short,
                    "error_code": ec_short,
                }
            )
        except Exception as e:
            logger.warning(
                "Firestore script_jobs mark skipped failed: type=%s", type(e).__name__
            )
            raise FirestoreUnavailableError(
                "Firestore is not reachable or rejected the update."
            ) from e

    def patch_watch_channel_fields(self, channel_id: str, fields: Dict[str, Any]) -> None:
        try:
            self._collection_ref().document(channel_id).update(fields)
        except Exception as e:
            logger.warning(
                "Firestore watch_channels patch failed: type=%s", type(e).__name__
            )
            raise FirestoreUnavailableError(
                "Firestore is not reachable or rejected the update."
            ) from e

    def _production_jobs_collection_ref(self):
        return self._ensure_client().collection(PRODUCTION_JOBS_COLLECTION)

    def get_production_job(self, doc_id: str) -> Optional[ProductionJob]:
        try:
            snap = self._production_jobs_collection_ref().document(doc_id).get()
        except Exception as e:
            logger.warning(
                "Firestore production_jobs get failed: type=%s", type(e).__name__
            )
            raise FirestoreUnavailableError(
                "Firestore is not reachable."
            ) from e
        if not snap.exists:
            return None
        merged = self._doc_to_dict(snap.to_dict() or {}, snap.id)
        try:
            return ProductionJob.model_validate(merged)
        except Exception as e:
            logger.warning(
                "invalid production_jobs doc: id=%s type=%s", snap.id, type(e).__name__
            )
            return None

    def create_production_job(self, job: ProductionJob) -> ProductionJob:
        try:
            self._production_jobs_collection_ref().document(job.id).set(
                job.model_dump()
            )
        except Exception as e:
            logger.warning(
                "Firestore production_jobs set failed: type=%s", type(e).__name__
            )
            raise FirestoreUnavailableError(
                "Firestore is not reachable or rejected the write."
            ) from e
        return job

    def _review_results_collection_ref(self):
        return self._ensure_client().collection(REVIEW_RESULTS_COLLECTION)

    def create_review_result(self, record: ReviewResultStored) -> ReviewResultStored:
        doc_id = record.id
        try:
            self._review_results_collection_ref().document(doc_id).set(
                record.model_dump()
            )
        except Exception as e:
            logger.warning(
                "Firestore review_results set failed: type=%s", type(e).__name__
            )
            raise FirestoreUnavailableError(
                "Firestore is not reachable or rejected the write."
            ) from e
        return record

    def set_script_job_review_result_id(
        self, job_id: str, review_result_id: str
    ) -> None:
        try:
            self._script_jobs_collection_ref().document(job_id).update(
                {"review_result_id": review_result_id}
            )
        except Exception as e:
            logger.warning(
                "Firestore script_jobs review_result_id update failed: type=%s",
                type(e).__name__,
            )
            raise FirestoreUnavailableError(
                "Firestore is not reachable or rejected the update."
            ) from e

    def update_processed_video_review_result_id(
        self, video_id: str, review_result_id: str
    ) -> None:
        try:
            self._processed_collection_ref().document(video_id).update(
                {"review_result_id": review_result_id}
            )
        except Exception as e:
            logger.warning(
                "Firestore processed_videos review_result_id failed: type=%s",
                type(e).__name__,
            )
            raise FirestoreUnavailableError(
                "Firestore is not reachable or rejected the update."
            ) from e

    def list_production_jobs(self, limit: int = 50) -> List[ProductionJob]:
        lim = max(1, min(int(limit), 200))
        try:
            snaps = self._production_jobs_collection_ref().stream()
        except Exception as e:
            logger.warning(
                "Firestore production_jobs stream failed: type=%s", type(e).__name__
            )
            raise FirestoreUnavailableError(
                "Firestore is not reachable."
            ) from e
        out: List[ProductionJob] = []
        for snap in snaps:
            merged = self._doc_to_dict(snap.to_dict() or {}, snap.id)
            try:
                out.append(ProductionJob.model_validate(merged))
            except Exception:
                logger.warning(
                    "skip invalid production_jobs row: doc_id=%s", snap.id
                )
                continue
        out.sort(key=lambda j: j.created_at or "", reverse=True)
        return out[:lim]

    def patch_production_job(self, doc_id: str, fields: Dict[str, Any]) -> None:
        try:
            self._production_jobs_collection_ref().document(doc_id).update(fields)
        except Exception as e:
            logger.warning(
                "Firestore production_jobs patch failed: type=%s", type(e).__name__
            )
            raise FirestoreUnavailableError(
                "Firestore is not reachable or rejected the update."
            ) from e

    def _scene_plans_collection_ref(self):
        return self._ensure_client().collection(SCENE_PLANS_COLLECTION)

    def get_scene_plan(self, production_job_id: str) -> Optional[ScenePlan]:
        doc_id = (production_job_id or "").strip()
        if not doc_id:
            return None
        try:
            snap = self._scene_plans_collection_ref().document(doc_id).get()
        except Exception as e:
            logger.warning(
                "Firestore scene_plans get failed: type=%s", type(e).__name__
            )
            raise FirestoreUnavailableError(
                "Firestore is not reachable."
            ) from e
        if not snap.exists:
            return None
        merged = self._doc_to_dict(snap.to_dict() or {}, snap.id)
        try:
            return ScenePlan.model_validate(merged)
        except Exception as e:
            logger.warning(
                "invalid scene_plans doc: id=%s type=%s", snap.id, type(e).__name__
            )
            return None

    def upsert_scene_plan(self, plan: ScenePlan) -> ScenePlan:
        doc_id = (plan.production_job_id or plan.id or "").strip()
        if not doc_id:
            raise FirestoreUnavailableError("scene_plans Document-ID darf nicht leer sein.")
        try:
            self._scene_plans_collection_ref().document(doc_id).set(
                plan.model_dump()
            )
        except Exception as e:
            logger.warning(
                "Firestore scene_plans set failed: type=%s", type(e).__name__
            )
            raise FirestoreUnavailableError(
                "Firestore is not reachable or rejected the write."
            ) from e
        return plan

    def _scene_assets_collection_ref(self):
        return self._ensure_client().collection(SCENE_ASSETS_COLLECTION)

    def get_scene_assets(self, production_job_id: str) -> Optional[SceneAssets]:
        doc_id = (production_job_id or "").strip()
        if not doc_id:
            return None
        try:
            snap = self._scene_assets_collection_ref().document(doc_id).get()
        except Exception as e:
            logger.warning(
                "Firestore scene_assets get failed: type=%s", type(e).__name__
            )
            raise FirestoreUnavailableError(
                "Firestore is not reachable."
            ) from e
        if not snap.exists:
            return None
        merged = self._doc_to_dict(snap.to_dict() or {}, snap.id)
        try:
            return SceneAssets.model_validate(merged)
        except Exception as e:
            logger.warning(
                "invalid scene_assets doc: id=%s type=%s", snap.id, type(e).__name__
            )
            return None

    def upsert_scene_assets(self, assets: SceneAssets) -> SceneAssets:
        doc_id = (assets.production_job_id or assets.id or "").strip()
        if not doc_id:
            raise FirestoreUnavailableError("scene_assets Document-ID darf nicht leer sein.")
        try:
            self._scene_assets_collection_ref().document(doc_id).set(
                assets.model_dump()
            )
        except Exception as e:
            logger.warning(
                "Firestore scene_assets set failed: type=%s", type(e).__name__
            )
            raise FirestoreUnavailableError(
                "Firestore is not reachable or rejected the write."
            ) from e
        return assets

    def _voice_plans_collection_ref(self):
        return self._ensure_client().collection(VOICE_PLANS_COLLECTION)

    def get_voice_plan(self, production_job_id: str) -> Optional[VoicePlan]:
        doc_id = (production_job_id or "").strip()
        if not doc_id:
            return None
        try:
            snap = self._voice_plans_collection_ref().document(doc_id).get()
        except Exception as e:
            logger.warning(
                "Firestore voice_plans get failed: type=%s", type(e).__name__
            )
            raise FirestoreUnavailableError(
                "Firestore is not reachable."
            ) from e
        if not snap.exists:
            return None
        merged = self._doc_to_dict(snap.to_dict() or {}, snap.id)
        try:
            return VoicePlan.model_validate(merged)
        except Exception as e:
            logger.warning(
                "invalid voice_plans doc: id=%s type=%s", snap.id, type(e).__name__
            )
            return None

    def upsert_voice_plan(self, plan: VoicePlan) -> VoicePlan:
        doc_id = (plan.production_job_id or plan.id or "").strip()
        if not doc_id:
            raise FirestoreUnavailableError("voice_plans Document-ID darf nicht leer sein.")
        try:
            self._voice_plans_collection_ref().document(doc_id).set(
                plan.model_dump()
            )
        except Exception as e:
            logger.warning(
                "Firestore voice_plans set failed: type=%s", type(e).__name__
            )
            raise FirestoreUnavailableError(
                "Firestore is not reachable or rejected the write."
            ) from e
        return plan

    def _render_manifests_collection_ref(self):
        return self._ensure_client().collection(RENDER_MANIFESTS_COLLECTION)

    def get_render_manifest(self, production_job_id: str) -> Optional[RenderManifest]:
        doc_id = (production_job_id or "").strip()
        if not doc_id:
            return None
        try:
            snap = self._render_manifests_collection_ref().document(doc_id).get()
        except Exception as e:
            logger.warning(
                "Firestore render_manifests get failed: type=%s", type(e).__name__
            )
            raise FirestoreUnavailableError(
                "Firestore is not reachable."
            ) from e
        if not snap.exists:
            return None
        merged = self._doc_to_dict(snap.to_dict() or {}, snap.id)
        try:
            return RenderManifest.model_validate(merged)
        except Exception as e:
            logger.warning(
                "invalid render_manifests doc: id=%s type=%s", snap.id, type(e).__name__
            )
            return None

    def upsert_render_manifest(self, manifest: RenderManifest) -> RenderManifest:
        doc_id = (manifest.production_job_id or manifest.id or "").strip()
        if not doc_id:
            raise FirestoreUnavailableError(
                "render_manifests Document-ID darf nicht leer sein."
            )
        try:
            self._render_manifests_collection_ref().document(doc_id).set(
                manifest.model_dump()
            )
        except Exception as e:
            logger.warning(
                "Firestore render_manifests set failed: type=%s", type(e).__name__
            )
            raise FirestoreUnavailableError(
                "Firestore is not reachable or rejected the write."
            ) from e
        return manifest

    def stream_script_jobs_for_error_summary(
        self, *, max_docs: int
    ) -> tuple[List[ScriptJob], bool]:
        """Jobs mit Status failed oder skipped, begrenzte Stichprobe (kein Full-Scan)."""
        cap = max(1, min(int(max_docs), 2000))
        try:
            q = (
                self._script_jobs_collection_ref()
                .where("status", "in", ["failed", "skipped"])
                .limit(cap)
            )
            snaps = list(q.stream())
        except Exception as e:
            logger.warning(
                "Firestore script_jobs error-summary stream failed: type=%s",
                type(e).__name__,
            )
            raise FirestoreUnavailableError(
                "Firestore is not reachable."
            ) from e
        truncated = len(snaps) >= cap
        out: List[ScriptJob] = []
        for snap in snaps:
            merged = self._doc_to_dict(snap.to_dict() or {}, snap.id)
            try:
                out.append(ScriptJob.model_validate(merged))
            except Exception:
                logger.warning("skip invalid script_jobs row: doc_id=%s", snap.id)
                continue
        return out, truncated

    def stream_processed_videos_skipped_for_summary(
        self, *, max_docs: int
    ) -> tuple[List[ProcessedVideo], bool]:
        cap = max(1, min(int(max_docs), 2000))
        try:
            q = (
                self._processed_collection_ref()
                .where("status", "==", "skipped")
                .limit(cap)
            )
            snaps = list(q.stream())
        except Exception as e:
            logger.warning(
                "Firestore processed_videos skipped stream failed: type=%s",
                type(e).__name__,
            )
            raise FirestoreUnavailableError(
                "Firestore is not reachable."
            ) from e
        truncated = len(snaps) >= cap
        out: List[ProcessedVideo] = []
        for snap in snaps:
            merged = self._doc_to_dict(snap.to_dict() or {}, snap.id)
            try:
                out.append(ProcessedVideo.model_validate(merged))
            except Exception:
                logger.warning(
                    "skip invalid processed_videos row: doc_id=%s", snap.id
                )
                continue
        return out, truncated
