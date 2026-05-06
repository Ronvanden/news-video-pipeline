"""BA 18.0 — Multi-Scene Asset Expansion (plan-only).

Import ``build_scene_expansion_layer`` from ``app.scene_expansion.layer`` to avoid
cycles with ``app.prompt_engine.schema``.
"""

from app.scene_expansion.schema import ExpandedSceneAssetBeat, SceneExpansionResult

__all__ = ["ExpandedSceneAssetBeat", "SceneExpansionResult"]
