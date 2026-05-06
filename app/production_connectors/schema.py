"""BA 10.0–10.10 + BA 11.0–11.5 — Connector-, Safety-, Run-Core und Live-Activation-Schema."""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field

from app.production_connectors.result_store_schema import ProviderExecutionRecord

ConnectorExecutionStatus = Literal[
    "ready",
    "blocked",
    "invalid_payload",
    "dry_run_success",
    "dry_run_warning",
]

ProductionConnectorSuiteStatus = Literal[
    "blocked",
    "invalid_payload",
    "dry_run_partial",
    "dry_run_complete",
]


class ConnectorExecutionRequest(BaseModel):
    """Normiertes Ausführungs-Intent (V1 nur Dry-Run / Planung)."""

    connector_name: str = ""
    provider_type: str = ""
    payload: Dict[str, Any] = Field(default_factory=dict)
    dry_run: bool = True


class ConnectorExecutionResult(BaseModel):
    """Ergebnis je Connector-Slot nach Validierung / Dry-Run."""

    connector_name: str = ""
    provider_type: str = ""
    execution_status: ConnectorExecutionStatus = "blocked"
    normalized_request: Dict[str, Any] = Field(default_factory=dict)
    normalized_response: Dict[str, Any] = Field(default_factory=dict)
    warnings: List[str] = Field(default_factory=list)
    blocking_reasons: List[str] = Field(default_factory=list)


ConnectorAuthStatus = Literal["auth_not_required", "auth_configured", "auth_missing", "auth_unknown"]
ConnectorAuthType = Literal["api_key", "oauth", "none", "unknown"]


class ConnectorAuthContractResult(BaseModel):
    """BA 10.1 — Erwartete Auth-Anforderungen je Connector (ohne ENV-Lesung)."""

    connector_name: str = ""
    auth_status: ConnectorAuthStatus = "auth_unknown"
    required_env_vars: List[str] = Field(default_factory=list)
    optional_env_vars: List[str] = Field(default_factory=list)
    auth_type: ConnectorAuthType = "unknown"
    warnings: List[str] = Field(default_factory=list)


class ConnectorAuthContractsResult(BaseModel):
    """BA 10.1 — gebündelte Auth-Contracts für die Prompt-Plan-API."""

    contracts_version: str = Field(default="10.1-v1")
    contracts: List[ConnectorAuthContractResult] = Field(default_factory=list)


ExecutionQueueJobStatus = Literal["queued", "blocked", "invalid"]
ProviderExecutionQueueStatus = Literal["ready", "partial", "blocked"]


class ExecutionQueueJob(BaseModel):
    """BA 10.2 — Ein geplanter Provider-Job (ohne Queue-Backend)."""

    job_id: str = ""
    provider_name: str = ""
    provider_type: str = ""
    queue_status: ExecutionQueueJobStatus = "blocked"
    dependency_order: int = Field(default=0, ge=0)
    payload: Dict[str, Any] = Field(default_factory=dict)
    warnings: List[str] = Field(default_factory=list)


class ProviderExecutionQueueResult(BaseModel):
    """BA 10.2 — deterministische Ausführungsreihenfolge."""

    queue_version: str = Field(default="10.2-v1")
    queue_status: ProviderExecutionQueueStatus = "blocked"
    jobs: List[ExecutionQueueJob] = Field(default_factory=list)
    total_jobs: int = Field(default=0, ge=0)
    execution_order_summary: str = ""
    blocking_reasons: List[str] = Field(default_factory=list)


AssetNormalizationStatus = Literal["normalized", "partial", "invalid"]
NormalizedAssetType = Literal["image", "video", "audio", "thumbnail", "render"]


class NormalizedAssetResult(BaseModel):
    """BA 10.3 — provider-neutrales Asset-Ergebnis (Stub)."""

    normalization_version: str = Field(default="10.3-v1")
    provider_name: str = ""
    provider_type: str = ""
    normalization_status: AssetNormalizationStatus = "invalid"
    asset_type: NormalizedAssetType = "image"
    asset_url: Optional[str] = None
    local_path: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    warnings: List[str] = Field(default_factory=list)


class ProductionConnectorSuiteResult(BaseModel):
    """Gesamtlauf über alle Bundle-Slots (ohne externe Calls)."""

    suite_version: str = Field(default="10.0-v1")
    suite_status: ProductionConnectorSuiteStatus = "blocked"
    connector_results: List[ConnectorExecutionResult] = Field(default_factory=list)
    summary: str = ""
    blocking_reasons: List[str] = Field(default_factory=list)
    insights: List[str] = Field(default_factory=list)
    auth_contracts: Optional[List[ConnectorAuthContractResult]] = Field(
        default=None,
        description="BA 10.1 — optionale Auth-Contract-Zeilen (keine Secret-Werte).",
    )
    execution_queue_result: Optional[ProviderExecutionQueueResult] = Field(
        default=None,
        description="BA 10.2 — optionale Ausführungswarteschlange.",
    )


# --- BA 10.4–10.6 Execution Safety ---

LiveExecutionGuardStatus = Literal["live_ready", "dry_run_only", "blocked", "policy_review"]


class LiveExecutionGuardResult(BaseModel):
    """BA 10.4 — Live-Ausführung nur bei explizit erfüllten Gates (V1 Default: Dry-Run)."""

    guard_version: str = Field(default="10.4-v1")
    live_execution_status: LiveExecutionGuardStatus = "dry_run_only"
    live_execution_allowed: bool = False
    blockers: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    required_conditions: List[str] = Field(default_factory=list)


APIActivationMode = Literal["dry_run", "restricted_live", "disabled"]


class ProviderActivationMatrix(BaseModel):
    """BA 10.5 — welche Provider-Slots theoretisch Live-fähig wären (V1 meist False)."""

    leonardo: bool = False
    kling: bool = False
    voice: bool = False
    thumbnail: bool = False
    render: bool = False


class APIActivationControlResult(BaseModel):
    """BA 10.5 — zentrale API-Aktivierungslogik (ohne echte Keys)."""

    activation_version: str = Field(default="10.5-v1")
    activation_mode: APIActivationMode = "dry_run"
    activation_allowed: bool = False
    activation_reason: str = ""
    provider_activation_matrix: ProviderActivationMatrix = Field(default_factory=ProviderActivationMatrix)
    warnings: List[str] = Field(default_factory=list)


GlobalExecutionMode = Literal["dry_run_only", "guarded_live", "emergency_stop"]


class ExecutionPolicyResult(BaseModel):
    """BA 10.6 — globale Policy / Kill-Switch (ohne Persistenz)."""

    policy_version: str = Field(default="10.6-v1")
    global_execution_mode: GlobalExecutionMode = "dry_run_only"
    kill_switch_active: bool = True
    max_estimated_cost_eur: float = Field(default=500.0, ge=0.0)
    max_jobs_per_run: int = Field(default=50, ge=1)
    policy_flags: List[str] = Field(default_factory=list)
    violations: List[str] = Field(default_factory=list)


# --- BA 10.8 Job Runner Mock ---

JobRunnerFinalStatus = Literal["queued", "skipped", "blocked", "simulated_success"]


class JobRunnerJobOutcome(BaseModel):
    """Ein simulierter Job-Endzustand."""

    job_id: str = ""
    provider_name: str = ""
    provider_type: str = ""
    final_status: JobRunnerFinalStatus = "queued"
    notes: str = ""


class ProviderJobRunnerMockResult(BaseModel):
    """BA 10.8 — Mock-Abarbeitung der Queue ohne Netzwerk."""

    runner_version: str = Field(default="10.8-v1")
    runner_status: Literal["complete", "partial", "blocked"] = "blocked"
    job_outcomes: List[JobRunnerJobOutcome] = Field(default_factory=list)
    connector_execution_records: List[ProviderExecutionRecord] = Field(
        default_factory=list,
        description="BA 10.7-kompatibel — Snapshots je simuliertem Job.",
    )
    summary: str = ""


# --- BA 10.9 Asset Status Tracker ---

AssetTrackerSlotStatus = Literal["pending", "generated", "failed", "skipped"]


class AssetMatrixEntry(BaseModel):
    """Status je Asset-Typ."""

    asset_type: NormalizedAssetType = "image"
    status: AssetTrackerSlotStatus = "pending"
    detail: str = ""


class AssetStatusTrackerResult(BaseModel):
    """BA 10.9 — erwartete vs. simulierte Assets."""

    tracker_version: str = Field(default="10.9-v1")
    tracker_status: Literal["ok", "partial", "degraded"] = "ok"
    total_expected_assets: int = Field(default=0, ge=0)
    generated_assets: int = Field(default=0, ge=0)
    pending_assets: int = Field(default=0, ge=0)
    failed_assets: int = Field(default=0, ge=0)
    asset_matrix: List[AssetMatrixEntry] = Field(default_factory=list)


# --- BA 10.10 Production Run Summary ---

ProductionLaunchRecommendation = Literal["hold", "dry_run_execute", "guarded_live_candidate"]


class ProductionRunSummaryResult(BaseModel):
    """BA 10.10 — kompakte Run-Sicht für Founder/Operator."""

    summary_version: str = Field(default="10.10-v1")
    run_readiness: str = ""
    execution_safety: str = ""
    projected_cost: float = Field(default=0.0, ge=0.0)
    projected_jobs: int = Field(default=0, ge=0)
    provider_summary: str = ""
    asset_summary: str = ""
    launch_recommendation: ProductionLaunchRecommendation = "hold"
    founder_summary: str = ""


# --- BA 11.0–11.5 Live Provider Activation ---

LiveProviderMode = Literal["dry_run_only", "guarded_live_ready", "provider_restricted", "blocked"]


class LiveProviderSafetyResult(BaseModel):
    """BA 11.0 — Safety-Contract vor Live-HTTP (Default: kein Live)."""

    safety_version: str = Field(default="11.0-v1")
    live_provider_mode: LiveProviderMode = "dry_run_only"
    live_provider_allowed: bool = False
    approved_providers: List[str] = Field(default_factory=list)
    blocked_providers: List[str] = Field(default_factory=list)
    required_conditions: List[str] = Field(default_factory=list)
    violations: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


SecretPresenceStatus = Literal["configured", "missing", "not_required", "unknown"]


class ProviderSecretStatus(BaseModel):
    """BA 11.1 — Secret-Anwesenheit je Provider (keine Werte)."""

    provider_name: str = ""
    secret_status: SecretPresenceStatus = "unknown"
    required_env_vars: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


RuntimeSecretCheckStatus = Literal["ready", "partial", "blocked"]


class RuntimeSecretCheckResult(BaseModel):
    """BA 11.1 — gebündelte ENV-Presence für Live-Kandidaten."""

    secret_check_version: str = Field(default="11.1-v1")
    runtime_status: RuntimeSecretCheckStatus = "blocked"
    provider_secrets: List[ProviderSecretStatus] = Field(default_factory=list)
    missing_required_secrets: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


LiveConnectorExecutionMode = Literal["dry_run", "live_attempt", "blocked"]


class LiveConnectorExecutionResult(BaseModel):
    """BA 11.2 / 11.3 — Leonardo- oder Voice-Live-Versuch (optional HTTP)."""

    live_connector_version: str = Field(default="11.2-v1")
    provider_name: str = ""
    provider_type: str = ""
    execution_mode: LiveConnectorExecutionMode = "dry_run"
    http_attempted: bool = False
    http_status_code: Optional[int] = None
    normalized_asset: Optional[NormalizedAssetResult] = None
    request_snapshot: Dict[str, Any] = Field(default_factory=dict)
    response_snapshot: Dict[str, Any] = Field(default_factory=dict)
    response_headers: Dict[str, str] = Field(default_factory=dict)
    warnings: List[str] = Field(default_factory=list)
    blocking_reasons: List[str] = Field(default_factory=list)


AssetPersistenceStatus = Literal["persist_ready", "metadata_only", "blocked"]


class AssetPersistenceResult(BaseModel):
    """BA 11.4 — Manifest / Ziele ohne Cloud-Pflicht."""

    persistence_version: str = Field(default="11.4-v1")
    persistence_status: AssetPersistenceStatus = "metadata_only"
    downloadable_assets: List[Dict[str, Any]] = Field(default_factory=list)
    local_storage_targets: List[str] = Field(default_factory=list)
    metadata_manifest: Dict[str, Any] = Field(default_factory=dict)
    warnings: List[str] = Field(default_factory=list)


ProviderErrorClassification = Literal["auth", "timeout", "payload", "provider", "unknown"]
ProviderRecoveryStatus = Literal["no_action", "retry_available", "fallback_to_dry_run", "blocked"]


class ProviderErrorRecoveryResult(BaseModel):
    """BA 11.5 — aggregierte Recovery-Empfehlung aus Live-Versuchen."""

    recovery_version: str = Field(default="11.5-v1")
    recovery_status: ProviderRecoveryStatus = "no_action"
    retry_recommended: bool = False
    fallback_provider: str = ""
    recovery_notes: List[str] = Field(default_factory=list)
    error_classification: ProviderErrorClassification = "unknown"


class LiveRuntimeGuardBundle(BaseModel):
    """Laufzeit-Gate für BA 11.2/11.3 (keine Secrets im Modell)."""

    guard_bundle_version: str = Field(default="11.x-v1")
    allow_live_http: bool = False
    leonardo_live_ok: bool = False
    voice_live_ok: bool = False
