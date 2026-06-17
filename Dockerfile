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

ENV DISPATCHARR_URL=""
ENV DISPATCHARR_API_KEY=""
ENV DISPATCHARR_USERNAME=""
ENV DISPATCHARR_PASSWORD=""

ENTRYPOINT ["dispatcharr-mcp"]
