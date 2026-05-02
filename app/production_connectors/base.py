"""BA 10.0 — Basis-Contract für Production-Connectoren (Dry-Run only)."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Tuple

from app.production_connectors.schema import ConnectorExecutionResult


class BaseProductionConnector(ABC):
    """Einheitliche Adapter-Schicht: validieren → Request bauen → Dry-Run → Response-Normalform."""

    provider_name: str = ""
    provider_type: str = ""

    @abstractmethod
    def validate_payload(self, payload: Dict[str, Any]) -> Tuple[bool, List[str], List[str]]:
        """Returns (ok, warnings, blocking_reasons)."""

    @abstractmethod
    def build_request(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Standardisiertes Provider-Request-Objekt (ohne Secrets / URLs mit Keys)."""

    def normalize_response(self, raw: Any) -> Dict[str, Any]:
        """Antwort in stabiles Dict (Dry-Run: simulierte Struktur)."""
        if isinstance(raw, dict):
            return dict(raw)
        return {"raw_type": type(raw).__name__, "note": "non-dict response normalized to stub"}

    def dry_run(self, payload: Dict[str, Any]) -> ConnectorExecutionResult:
        ok, warns, blockers = self.validate_payload(payload)
        if blockers or not ok:
            br = list(blockers) if blockers else ["payload_validation_failed"]
            return ConnectorExecutionResult(
                connector_name=self.provider_name,
                provider_type=self.provider_type,
                execution_status="invalid_payload",
                normalized_request={},
                normalized_response={},
                warnings=warns,
                blocking_reasons=br,
            )
        req = self.build_request(payload)
        sim = {"dry_run": True, "provider": self.provider_name, "accepted_fields": list(req.keys())}
        resp = self.normalize_response(sim)
        status = "dry_run_success"
        if warns:
            status = "dry_run_warning"
        return ConnectorExecutionResult(
            connector_name=self.provider_name,
            provider_type=self.provider_type,
            execution_status=status,
            normalized_request=req,
            normalized_response=resp,
            warnings=warns,
            blocking_reasons=[],
        )
