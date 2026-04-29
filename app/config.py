from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_name: str = "News to Video Pipeline"
    debug: bool = False
    # Add other settings like API keys if needed

    class Config:
        env_file = ".env"

settings = Settings()