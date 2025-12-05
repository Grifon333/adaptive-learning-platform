from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    REDIS_URL: str
    LOG_LEVEL: str = "INFO"
    DATABASE_URL: str

    # RL / DKT Parameters
    # 130 Concepts + 5 Behavior + 2 Cognitive + 4 Preferences = 141
    INPUT_DIM: int = 141
    HIDDEN_DIM: int = 128  # Size of the hidden layer of the LSTM
    LAYER_DIM: int = 1
    OUTPUT_DIM: int = 130


settings = Settings()
