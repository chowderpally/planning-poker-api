FROM python:3.12-slim AS builder

ENV POETRY_HOME=/opt/poetry \
    POETRY_VENV=/opt/poetry-venv \
    POETRY_VIRTUALENVS_IN_PROJECT=true \
    POETRY_CACHE_DIR=/opt/.cache

RUN python -m venv $POETRY_VENV \
    && $POETRY_VENV/bin/pip install poetry==2.3.2

ENV PATH="${POETRY_VENV}/bin:${PATH}"

WORKDIR /app
COPY pyproject.toml poetry.lock* ./
RUN --mount=type=cache,target=/opt/.cache \
    poetry install --no-interaction --no-root --without dev

FROM python:3.12-slim AS runtime

RUN addgroup --gid 1000 appgroup && \
    adduser --uid 1000 --gid 1000 --disabled-password --gecos "" appuser

WORKDIR /app
COPY --from=builder /app/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONPATH="/app" \
    PYTHONUNBUFFERED=1

EXPOSE 8000
COPY app/ app/

USER appuser
CMD ["uvicorn", "app.main:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000"]
