# Stage 1: Backend - Generate OpenAPI schema
FROM ghcr.io/astral-sh/uv:python3.13-trixie-slim AS backend-openapi
WORKDIR /backend

# Install system dependencies for pyodbc (MSSQL)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    unixodbc \
    unixodbc-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Microsoft ODBC Driver for SQL Server
RUN curl -fsSL https://packages.microsoft.com/config/debian/13/packages-microsoft-prod.deb -o packages-microsoft-prod.deb && \
    dpkg -i packages-microsoft-prod.deb && \
    rm packages-microsoft-prod.deb && \
    apt-get update && \
    ACCEPT_EULA=Y apt-get install -y msodbcsql18 && \
    rm -rf /var/lib/apt/lists/*

COPY backend/pyproject.toml backend/uv.lock* ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project
COPY backend/ ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen
RUN uv run python export_openapi.py

# Stage 2: Frontend - Build static files
FROM node:22-slim AS frontend-builder
WORKDIR /frontend
# Copy package files first for better caching
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm ci
# Copy OpenAPI schema from backend stage
COPY --from=backend-openapi /backend/openapi.json ../backend/openapi.json
# Copy frontend source
COPY frontend/ ./
# Generate API client from OpenAPI schema
RUN npm run genclient
# Build frontend
RUN npm run build

# Stage 3: Backend - Final production image
FROM ghcr.io/astral-sh/uv:python3.13-trixie-slim AS backend-final
LABEL "org.opencontainers.image.source"="https://github.com/nelsonwellswku/backlog-boss" \
      "org.opencontainers.image.description" = "Backlog Boss container image" \
      "org.opencontainers.image.licenses=AGPL"
WORKDIR /app

# Install system dependencies for pyodbc (MSSQL)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    unixodbc \
    unixodbc-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Microsoft ODBC Driver for SQL Server
RUN curl -fsSL https://packages.microsoft.com/config/debian/13/packages-microsoft-prod.deb -o packages-microsoft-prod.deb && \
    dpkg -i packages-microsoft-prod.deb && \
    rm packages-microsoft-prod.deb && \
    apt-get update && \
    ACCEPT_EULA=Y apt-get install -y msodbcsql18 && \
    rm -rf /var/lib/apt/lists/*

# Copy backend project files
COPY backend/pyproject.toml backend/uv.lock* ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project --no-dev

COPY backend/ ./

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

# Copy built frontend files to be served by FastAPI
COPY --from=frontend-builder /frontend/dist ./static

# Create a non-root user
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 9000

# Run the FastAPI application
ENV PATH="/app/.venv/bin:$PATH"
CMD ["fastapi", "run", "main.py", "--host", "0.0.0.0", "--port", "9000"]
