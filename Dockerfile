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

# Copy validation script
COPY validate_env.py .

# Make validation script executable
RUN chmod +x validate_env.py

# Validate environment and start application
# This ensures container fails immediately if required env vars are missing
# Note: docker-compose.yml overrides this with uvicorn server for local dev
CMD ["sh", "-c", "python validate_env.py && uv run uvicorn features.platform.server:app --host 0.0.0.0 --port 8000"]
