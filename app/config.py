from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "News to Video Pipeline"
    debug: bool = False
    openai_api_key: str = ""
    openai_model: str = "gpt-3.5-turbo"
    #: Firestore-Datenbank-ID (Named DB, z. B. „watchlist“; nicht „(default)“).
    firestore_database: str = "watchlist"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
