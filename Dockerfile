# syntax=docker/dockerfile:1.7
FROM python:3.12-slim

# --- Base env (faster startup, cleaner FS, no pip cache) ---
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# --- Minimal OS deps (TLS + healthcheck helper) ---
RUN apt-get update && apt-get install -y --no-install-recommends \
      ca-certificates curl \
    && rm -rf /var/lib/apt/lists/*

# --- App workspace ---
WORKDIR /app

# Copy & install deps first for better build caching
COPY requirements.txt ./
RUN python -m pip install --upgrade pip \
 && pip install -r requirements.txt

# Now copy the application code
COPY . .

# --- Drop root ---
RUN useradd -m -u 10001 appuser && chown -R appuser:appuser /app
USER appuser

# If your API listens on 8000, keep this; otherwise adjust/remove.
EXPOSE 8099

# Optional: if you expose a /health, this keeps Compose/K8s happy.
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD curl -fsS http://127.0.0.1:8099/api/v1/health || exit 1

# Start your app
CMD ["python", "main.py"]
