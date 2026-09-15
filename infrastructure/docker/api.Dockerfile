FROM python:3.12-slim-bookworm
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg && rm -rf /var/lib/apt/lists/*
COPY pyproject.toml uv.lock ./
COPY apps/api apps/api
RUN pip install --no-cache-dir uv==0.12.13 && uv sync --frozen --no-dev
COPY infrastructure/database infrastructure/database
COPY alembic.ini ./
COPY data data
ENV PATH="/app/.venv/bin:$PATH"
RUN useradd -u 10001 -m civicquest && mkdir -p /app/.local/media && chown -R civicquest:civicquest /app
USER civicquest
EXPOSE 8000
CMD ["uvicorn","civicquest.main:app","--host","0.0.0.0","--port","8000"]
