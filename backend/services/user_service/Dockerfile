FROM python:3.11-slim

WORKDIR /app

RUN pip install poetry
RUN poetry config virtualenvs.in-project true

RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml poetry.lock ./
RUN poetry install --no-root

COPY src/ ./src/
COPY migrations/ ./migrations/
COPY alembic.ini ./

EXPOSE 8000

CMD ["sh", "-c", "poetry run alembic upgrade head && poetry run uvicorn src.main:app --host 0.0.0.0 --port 8000"]
