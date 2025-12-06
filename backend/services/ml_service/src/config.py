from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    REDIS_URL: str
    LOG_LEVEL: str = "INFO"
    DATABASE_URL: str

    # RL / DKT Parameters
    # 123 Concepts + 5 Behavior + 2 Cognitive + 4 Preferences = 134
    INPUT_DIM_DKT: int = 123
    OUTPUT_DIM_DKT: int = 123
    INPUT_DIM_RL: int = 134
    OUTPUT_DIM_RL: int = 123
    HIDDEN_DIM: int = 128  # Size of the hidden layer of the LSTM
    LAYER_DIM: int = 1


settings = Settings()
