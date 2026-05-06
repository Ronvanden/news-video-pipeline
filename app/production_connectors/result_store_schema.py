"""BA 10.7 — Result-Store-Schema (nur Modelle, kein DB-Write)."""

from __future__ import annotations

from typing import Any, Dict, List, Literal

from pydantic import BaseModel, Field

ProviderExecutionRecordStatus = Literal["pending", "simulated_success", "failed", "skipped", "blocked"]


class ProviderExecutionRecord(BaseModel):
    """Einzelner Connector-Lauf (Snapshot-only V1)."""

    execution_id: str = ""
    provider_name: str = ""
    provider_type: str = ""
    request_snapshot: Dict[str, Any] = Field(default_factory=dict)
    response_snapshot: Dict[str, Any] = Field(default_factory=dict)
    execution_mode: str = "dry_run"
    execution_status: ProviderExecutionRecordStatus = "pending"
    created_at: str = ""
    warnings: List[str] = Field(default_factory=list)


ProductionRunRecordStatus = Literal["draft", "simulated", "failed", "blocked"]


class ProductionRunRecord(BaseModel):
    """Aggregat eines Produktions-Runs (ohne Persistenz)."""

    run_id: str = ""
    run_status: ProductionRunRecordStatus = "draft"
    connector_records: List[ProviderExecutionRecord] = Field(default_factory=list)
    estimated_cost: float = Field(default=0.0, ge=0.0)
    total_jobs: int = Field(default=0, ge=0)
    summary: str = ""
    meta: Dict[str, Any] = Field(default_factory=dict)
