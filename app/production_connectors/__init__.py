"""BA 10.0 — Production Connector Layer (Dry-Run only).

Importiere ``dry_run_provider_bundle`` aus ``app.production_connectors.dry_run_executor``,
um Zyklen mit ``app.prompt_engine.schema`` zu vermeiden.
"""

from app.production_connectors.registry import get_connector, list_available_connectors
from app.production_connectors.schema import (
    ConnectorExecutionRequest,
    ConnectorExecutionResult,
    ProductionConnectorSuiteResult,
)

__all__ = [
    "get_connector",
    "list_available_connectors",
    "ConnectorExecutionRequest",
    "ConnectorExecutionResult",
    "ProductionConnectorSuiteResult",
]
