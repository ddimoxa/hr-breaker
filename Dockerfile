FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright \
    STREAMLIT_SERVER_PORT=8501 \
    STREAMLIT_SERVER_ADDRESS=0.0.0.0 \
    STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

RUN apt-get update && apt-get install -y --no-install-recommends \
        ca-certificates \
        libpango-1.0-0 \
        libpangoft2-1.0-0 \
        libpangocairo-1.0-0 \
        libharfbuzz0b \
        libfontconfig1 \
        libfreetype6 \
        libglib2.0-0 \
        libgdk-pixbuf-2.0-0 \
        libcairo2 \
        libffi8 \
        libjpeg62-turbo \
        libopenjp2-7 \
        libtiff6 \
        shared-mime-info \
        fonts-dejavu \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY pyproject.toml uv.lock README.md /app/
COPY src /app/src
COPY templates /app/templates

RUN pip install . \
    && python -m playwright install --with-deps --no-shell chromium \
    && rm -rf /root/.cache /var/lib/apt/lists/*

EXPOSE 8501

CMD ["streamlit", "run", "src/hr_breaker/main.py", "--server.address=0.0.0.0", "--server.port=8501"]
