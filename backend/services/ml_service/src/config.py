from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    REDIS_URL: str
    LOG_LEVEL: str = "INFO"

    # DKT model parameters (Deep Knowledge Tracing)
    INPUT_DIM: int = 100  # Number of unique concepts (vocabulary size)
    HIDDEN_DIM: int = 128 # Size of the hidden layer of the LSTM
    LAYER_DIM: int = 1
    OUTPUT_DIM: int = 100

settings = Settings()
