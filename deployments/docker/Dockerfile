# syntax=docker/dockerfile:1

FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim AS base

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install the project and its dependencies.
COPY pyproject.toml uv.lock README.md ./
COPY src ./src
RUN uv sync --frozen --no-dev

# Build UI
FROM node:20-slim AS ui-builder

WORKDIR /ui
COPY ui/package.json ui/package-lock.json ./
RUN npm ci --production=false
COPY ui/tsconfig.json ui/vite.config.ts ./
COPY ui/index.html ./
COPY ui/src ./src
RUN npm run build

# Final runtime image.
FROM python:3.13-slim-bookworm AS runtime

ENV PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app

# Copy Python dependencies and source
COPY --from=base /app/.venv /app/.venv
COPY src ./src
COPY pyproject.toml README.md ./

# Copy built UI
COPY --from=ui-builder /ui/dist ./ui/dist

# Create config directory
RUN mkdir -p /app/config

# Run as a non-root user.
RUN groupadd --system app && useradd --system --gid app app \
    && chown -R app:app /app
USER app

EXPOSE 8000 8080

ENTRYPOINT ["enterprise-mcp"]
CMD ["serve", "--host", "0.0.0.0", "--port", "8000"]