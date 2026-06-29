FROM python:3.12-slim

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Copy requirements and install
COPY pyproject.toml README.md ./
RUN uv pip install --system -e .

# Copy source and config
COPY src/ /app/src/
COPY instances.yaml /app/
COPY runbooks/ /app/runbooks/

ENV PYTHONPATH=/app/src
