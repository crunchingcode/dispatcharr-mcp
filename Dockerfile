# syntax=docker/dockerfile:1
FROM python:3.12-slim

# Install the package from source (no build tools needed — pure Python)
WORKDIR /app
COPY pyproject.toml README.md ./
COPY dispatcharr_mcp/ ./dispatcharr_mcp/

RUN pip install --no-cache-dir .

# Environment variables — all required at runtime
# DISPATCHARR_URL       - e.g. http://dispatcharr.example.com
# DISPATCHARR_API_KEY   - preferred auth (generate in Dispatcharr UI)
# DISPATCHARR_USERNAME  - JWT fallback
# DISPATCHARR_PASSWORD  - JWT fallback
#
# MCP_TRANSPORT         - transport mode (default: streamable-http for Docker use)
#                         set to stdio only if the client spawns the process directly
# PORT                  - HTTP listen port (default: 8000)

ENV DISPATCHARR_URL=""
ENV DISPATCHARR_API_KEY=""
ENV DISPATCHARR_USERNAME=""
ENV DISPATCHARR_PASSWORD=""
ENV MCP_TRANSPORT="streamable-http"

EXPOSE 8000

ENTRYPOINT ["dispatcharr-mcp"]
