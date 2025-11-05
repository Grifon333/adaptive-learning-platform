FROM python:3.11-slim

WORKDIR /app

RUN pip install poetry
RUN poetry config virtualenvs.in-project true

COPY pyproject.toml poetry.lock ./
RUN poetry install --no-root

COPY src/ ./src/

EXPOSE 8000

CMD [ "poetry", "run", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
