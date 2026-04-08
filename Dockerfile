FROM ghcr.io/open-webui/pipelines:main

WORKDIR /app

# Install uv and export locked deps to requirements.txt, then install via pip
RUN pip install --no-cache-dir uv

COPY pyproject.toml uv.lock ./
RUN uv export --frozen --no-dev --no-hashes -o /tmp/requirements.txt && \
    pip install --no-cache-dir -r /tmp/requirements.txt

COPY src/ ./src/

# Copy pipeline file to the directory the pipelines server watches on startup
COPY src/app/ui/openwebui_pipeline.py /app/pipelines/trading_pipeline.py
