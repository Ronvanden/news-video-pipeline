"""BA 17.0 — Viral Upgrade Layer (Founder-only, lean, advisory).

Import ``build_viral_upgrade_layer`` from ``app.viral_upgrade.layer`` to avoid
import cycles with ``app.prompt_engine.schema``.
"""

from app.viral_upgrade.schema import ViralUpgradeLayerResult

__all__ = ["ViralUpgradeLayerResult"]
