"""BA 8.6 — Provider-Disziplin: Standard-Seed und Laufzeit-Gesundheit ohne Secrets/externe Calls."""

from __future__ import annotations

from typing import List, Tuple

from app.watchlist.models import ProviderConfig, ProviderNameLiteral


def seed_default_provider_configs(*, now_iso: str) -> List[ProviderConfig]:
    """Legt vier produktionsnahe Konfig-Slots an (alle ``enabled=False``, ``dry_run=True``).

    Dokument-ID = ``provider_name``. Keine API-Keys, keine Netzwerkzugriffe.
    """
    spec: List[tuple[ProviderNameLiteral, str, float]] = [
        (
            "openai",
            "BA 8.6 Seed: Text/LLM-Slot. Budget-Platzhalter; Secrets nur via Runtime.",
            120.0,
        ),
        (
            "voice_default",
            "BA 8.6 Seed: Standard-Voice/TTS-Slot vor Anbieterwahl; nur Dry-Run.",
            200.0,
        ),
        (
            "image_default",
            "BA 8.6 Seed: Standard-Bild/Prompt-Slot; nur Dry-Run.",
            150.0,
        ),
        (
            "render_default",
            "BA 8.6 Seed: Render/Export-Slot; nur Dry-Run.",
            100.0,
        ),
    ]
    out: List[ProviderConfig] = []
    for name, notes, budget in spec:
        out.append(
            ProviderConfig(
                id=name,
                provider_name=name,
                enabled=False,
                dry_run=True,
                monthly_budget_limit=budget,
                current_month_estimated_cost=0.0,
                status="disabled",
                notes=notes,
                created_at=now_iso,
                updated_at=now_iso,
            )
        )
    return out


def validate_provider_runtime_health(
    configs: List[ProviderConfig],
) -> Tuple[bool, List[str]]:
    """Prüft Konfigurationsdisziplin (keine echten Provider-Pings).

    Regeln u. a.: aktivierte Provider ohne Dry-Run → Hinweis; geschätzte Kosten über Limit → kritisch.
    """
    issues: List[str] = []
    ok = True
    for c in configs:
        name = c.provider_name
        if c.enabled and not c.dry_run:
            issues.append(
                f"{name}: enabled ohne dry_run — in Produktion nur mit Freigabe/Monitoring."
            )
            ok = False
        limit = float(c.monthly_budget_limit or 0.0)
        spent = float(c.current_month_estimated_cost or 0.0)
        if limit > 0.0 and spent > limit:
            issues.append(
                f"{name}: current_month_estimated_cost ({spent}) über monthly_budget_limit ({limit})."
            )
            ok = False
        if c.status == "error":
            issues.append(f"{name}: status=error — manuell prüfen.")
            ok = False
    return ok, issues
