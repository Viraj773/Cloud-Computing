# ── Stage 1: install dependencies ────────────────────────────────────────────
FROM python:3.12-slim AS builder
WORKDIR /build
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ── Stage 2: lean runtime image ───────────────────────────────────────────────
FROM python:3.12-slim
RUN useradd -m -u 1001 appuser
WORKDIR /app

# Copy installed packages from builder stage
COPY --from=builder /install /usr/local

# Copy application source and templates
COPY app.py         ./
COPY templates/     ./templates/
COPY static/        ./static/

EXPOSE 80
USER root

# 4 workers suits a Fargate task with 1 vCPU / 2 GB RAM
CMD ["gunicorn", "app:app", \
     "--workers", "4", \
     "--bind", "0.0.0.0:80", \
     "--timeout", "120", \
     "--access-logfile", "-", \
     "--error-logfile", "-"]
