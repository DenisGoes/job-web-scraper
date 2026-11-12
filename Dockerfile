FROM python:3.14-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

WORKDIR /app

# libatomic1 é exigida pelo binário Node interno do Playwright antes do install --with-deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    libatomic1 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --upgrade pip \
    && pip install -r requirements.txt \
    && playwright install --with-deps chromium \
    && rm -rf /var/lib/apt/lists/*

COPY . .

EXPOSE 8000

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]