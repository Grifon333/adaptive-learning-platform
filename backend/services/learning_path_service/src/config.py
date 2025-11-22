from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    USER_SERVICE_URL: str
    KG_SERVICE_URL: str
    ML_SERVICE_URL: str
    LOG_LEVEL: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()  # type: ignore[call-arg]
