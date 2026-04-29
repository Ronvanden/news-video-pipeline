"""Firestore-Zugriffe für die Watchlist-Kollektion ``watch_channels``.

Client ist injizierbar (Unit-Tests mit Mock).
"""

from __future__ import annotations

import logging
from typing import Any, Callable, Dict, List, Optional

from app.watchlist.models import ProcessedVideo, WatchlistChannel

logger = logging.getLogger(__name__)

COLLECTION_NAME = "watch_channels"
PROCESSED_VIDEOS_COLLECTION = "processed_videos"


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
