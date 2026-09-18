# ============================================================
# Stage 1 — Python dependency builder
# ============================================================
FROM python:3.12-slim AS builder

WORKDIR /install

# Install system build deps needed by easyocr / pdf2image / Pillow
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --prefix=/install/deps --no-cache-dir -r requirements.txt

# ============================================================
# Stage 2 — Lean runtime image
# ============================================================
FROM python:3.12-slim AS runtime

WORKDIR /app

# Runtime-only system libraries
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# Copy installed Python packages from builder
COPY --from=builder /install/deps /usr/local

# Copy application source
COPY ./app ./app
COPY ./alembic.ini ./alembic.ini
COPY ./alembic ./alembic

# Non-root user for security
RUN useradd --system --no-create-home --uid 1001 appuser

# Writable directories for uploads, EasyOCR models, and framework caches.
RUN mkdir -p /app/uploads /app/easyocr-models /app/user-home/.cache && \
    chown -R appuser:appuser /app/uploads /app/easyocr-models /app/user-home

USER appuser

ENV HOME=/app/user-home \
    XDG_CACHE_HOME=/app/user-home/.cache \
    TORCH_HOME=/app/easyocr-models \
    OCR_MODEL_DIR=/app/easyocr-models

EXPOSE 8000

# Render supplies PORT; default to 8000 for local container runs.
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers ${WEB_CONCURRENCY:-1} --no-access-log"]
