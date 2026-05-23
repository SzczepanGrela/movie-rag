FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:0.11 /uv /uvx /usr/local/bin/

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project --no-dev

ENV HF_HOME=/app/.cache/huggingface
RUN --mount=type=secret,id=hf_token \
    HF_TOKEN=$(cat /run/secrets/hf_token) \
    .venv/bin/python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('google/embeddinggemma-300m')"

COPY app/ ./app/
COPY alembic.ini ./
COPY migrations/ ./migrations/

ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
