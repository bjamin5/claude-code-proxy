FROM ghcr.io/astral-sh/uv:bookworm-slim

# Install build dependencies for Python packages
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy the project into the image
ADD . /app

# Sync the project into a new environment, asserting the lockfile is up to date
WORKDIR /app
RUN uv sync --locked

CMD ["uv", "run", "start_proxy.py"]
