from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "News to Video Pipeline"
    debug: bool = False
    #: Nur Entwicklung/Test: ``POST /dev/fixtures/*`` (siehe README).
    enable_test_fixtures: bool = False
    openai_api_key: str = ""
    openai_model: str = "gpt-3.5-turbo"
    #: OpenAI Speech (``/v1/audio/speech``); kein Secret — Modell-/Stimmnamen sind öffentliche Parameter.
    openai_tts_model: str = "tts-1"
    openai_tts_voice: str = "alloy"
    #: BA 26.5 — OpenAI Images (public params, kein Secret)
    openai_image_model: str = "gpt-image-1"
    openai_image_size: str = "1024x1024"
    #: BA 26.5 — Schutz: Live-Bildcalls nur wenn explizit aktiviert (Default false)
    enable_openai_images_live: bool = False
    #: BA 26.8c — heuristische Visual Cost Defaults (EUR, keine Billing-API)
    visual_cost_openai_image_eur: float = 0.04
    visual_cost_leonardo_image_eur: float = 0.05
    visual_cost_runway_clip_eur: float = 0.26
    visual_cost_seedance_clip_eur: float = 0.31
    visual_cost_render_layer_eur: float = 0.0
    #: Phase 7.2: ``audio_base64`` in Preview nur wenn aktiv (Default Metadata‑only).
    enable_voice_synth_preview_body: bool = False
    #: Max. dekodierte Audiolänge je Chunk für Base64-Auslieferung (Steckbrief ≤ 262144).
    voice_synth_preview_max_bytes: int = 262144
    #: Firestore-Datenbank-ID (Named DB, z. B. „watchlist“; nicht „(default)“).
    firestore_database: str = "watchlist"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
