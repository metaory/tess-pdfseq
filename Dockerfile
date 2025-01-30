# syntax=docker/dockerfile:1.6
#
# tess-pdfseq: Sequential PDF OCR with Tesseract
#

# --- Build Stage -------------------------------------------
FROM python:3.12-slim-bookworm AS builder

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python packages
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir \
    --no-compile \
    -r requirements.txt

# --- Final Stage ------------------------------------------
FROM python:3.12-slim-bookworm

# Labels
LABEL org.opencontainers.image.title="tess-pdfseq" \
      org.opencontainers.image.description="Sequential PDF OCR with Tesseract" \
      org.opencontainers.image.version="1.0.0"

# Build arguments
ARG TESS_LANGS="eng"
ARG UID=1000
ARG GID=1000

# Runtime environment
ENV OCR_LANGS=${TESS_LANGS} \
    LANG=C.UTF-8 \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DPI=500 \
    TARGET_WIDTH=1800 \
    MAX_PAGES=3

# Install runtime dependencies and language packages
RUN apt-get update && apt-get install -y --no-install-recommends \
        poppler-utils \
        tesseract-ocr \
        $(echo "${TESS_LANGS}" | tr '+' '\n' | xargs -I{} echo "tesseract-ocr-{}") \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd -g ${GID} ocr \
    && useradd -u ${UID} -g ocr -s /bin/bash -m ocr

# Setup application
WORKDIR /app
COPY --from=builder \
    /usr/local/lib/python3.12/site-packages \
    /usr/local/lib/python3.12/site-packages
COPY src ./src

# Set permissions
RUN chown -R ocr:ocr /app

# Switch to non-root user
USER ocr

# Define volumes
VOLUME ["/app/data", "/app/output"]

# Health check
HEALTHCHECK \
    --interval=30s \
    --timeout=10s \
    --start-period=5s \
    --retries=3 \
    CMD python3 -c "import pytesseract; pytesseract.get_tesseract_version()" || exit 1

# Default command
CMD ["python3", "src/ocr.py"]

