# PatternShield — Production Dockerfile
FROM python:3.12-slim AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install into a venv so any user can import the packages
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements-prod.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

RUN python -c "\
import nltk; \
nltk.download('vader_lexicon', download_dir='/usr/local/share/nltk_data'); \
nltk.download('punkt',         download_dir='/usr/local/share/nltk_data'); \
nltk.download('punkt_tab',     download_dir='/usr/local/share/nltk_data')"

# ── Runtime stage ─────────────────────────────────────────────────────────────
FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /opt/venv /opt/venv
COPY --from=builder /usr/local/share/nltk_data /usr/local/share/nltk_data

ENV PATH="/opt/venv/bin:$PATH"
ENV NLTK_DATA=/usr/local/share/nltk_data

COPY app.py .
COPY config.py .
COPY ml_detector.py .
COPY gunicorn_config.py .
COPY api/ api/
COPY services/ services/
COPY storage/ storage/
COPY data/ data/

RUN mkdir -p logs

RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app
USER appuser

EXPOSE 5000

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

CMD ["gunicorn", \
     "--bind", "0.0.0.0:5000", \
     "--workers", "4", \
     "--threads", "2", \
     "--timeout", "60", \
     "--access-logfile", "-", \
     "--error-logfile", "-", \
     "--log-level", "info", \
     "app:app"]
