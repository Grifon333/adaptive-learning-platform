from fastapi import FastAPI
from .config import settings

app = FastAPI(title="ML Service API")

@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "ML Service",
        "framework": "PyTorch",
        "device": "CPU"
    }
