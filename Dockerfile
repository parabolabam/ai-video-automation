FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim

WORKDIR /app

# System deps (FFmpeg for audio/video composition)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl ca-certificates ffmpeg && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

COPY . .

# Default envs (override in Render/cron)
ENV PYTHONUNBUFFERED=1 \
    LOG_LEVEL=INFO

# Health check (optional)
HEALTHCHECK CMD python -c "import sys; sys.exit(0)"

# Default command runs orchestrator
CMD ["uv", "run", "main_v2.py"]
