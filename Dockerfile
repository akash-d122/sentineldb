FROM python:3.12-slim

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Copy requirements and install
COPY pyproject.toml .
RUN uv pip install --system -e .

# Copy source
COPY src/ /app/src/

ENV PYTHONPATH=/app/src
