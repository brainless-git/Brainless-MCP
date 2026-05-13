FROM python:3.12-slim

WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy project files
COPY pyproject.toml .
COPY src/ src/

# Install dependencies
RUN uv sync --no-dev

ENV BRAINLESS_MCP_TRANSPORT=http
ENV BRAINLESS_MCP_PORT=8000

EXPOSE 8000

ENTRYPOINT ["uv", "run", "brainless-mcp-server"]
