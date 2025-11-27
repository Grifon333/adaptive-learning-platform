from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str
    MONGODB_URL: str
    MONGODB_DB_NAME: str = "adaptive_learning_events"
    LOG_LEVEL: str = "INFO"

settings = Settings()
