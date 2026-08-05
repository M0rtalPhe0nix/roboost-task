FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_LINK_MODE=copy

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

COPY app ./app
COPY scripts/prepare_runtime_data.py ./scripts/prepare_runtime_data.py
COPY data/operations_data_anonymized.xlsx ./data/operations_data_anonymized.xlsx
RUN uv run --no-dev python -m scripts.prepare_runtime_data \
    data/operations_data_anonymized.xlsx \
    data/operations.runtime.csv.gz

ENV OPERATIONS_DATA_PATH=/app/data/operations.runtime.csv.gz

CMD ["uv", "run", "--no-dev", "python", "-m", "app.telegram_bot"]
