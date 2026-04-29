from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_name: str = "News to Video Pipeline"
    debug: bool = False
    openai_api_key: str = ""
    openai_model: str = "gpt-3.5-turbo"

    class Config:
        env_file = ".env"

settings = Settings()