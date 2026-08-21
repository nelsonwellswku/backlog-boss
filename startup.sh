#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

usage() {
    cat <<EOF
Usage: $(basename "$0") [OPTIONS]

Start Backlog Boss development environment (SQL Server, Grate migrations,
backend API, and frontend dev server).

Options:
  -r, --reset  Remove Docker volumes before starting (clean database state)
  -h, --help   Show this help message and exit

Services:
  Backend     http://localhost:8000
  Frontend    http://localhost:5173
EOF
    exit 0
}

# Parse flags
RESET=false
for arg in "$@"; do
    case "$arg" in
        -r|--reset) RESET=true ;;
        -h|--help) usage ;;
        *) echo "Unknown option: $arg"; usage ;;
    esac
done

# 1. Check Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker and try again."
    exit 1
fi
echo "✅ Docker is running"

# Optionally remove volumes for a clean start
if [ "$RESET" = true ]; then
    echo "🔄 Removing Docker volumes for a clean start..."
    docker compose -f "$REPO_ROOT/docker-compose.yaml" down -v --remove-orphans 2>/dev/null || true
fi

# 2. Spin up Docker compose (SQL Server + Grate)
echo "🚀 Starting Docker compose services (sqlserver + grate)..."
docker compose -f "$REPO_ROOT/docker-compose.yaml" up -d

# 3. Wait for SQL Server to be healthy
echo "⏳ Waiting for SQL Server to be healthy..."
MAX_RETRIES=30
INTERVAL=2
for ((i=1; i<=MAX_RETRIES; i++)); do
    if docker compose -f "$REPO_ROOT/docker-compose.yaml" ps sqlserver | grep -q "healthy"; then
        echo "✅ SQL Server is healthy"
        break
    fi
    if (( i == MAX_RETRIES )); then
        echo "❌ SQL Server did not become healthy after $((MAX_RETRIES * INTERVAL)) seconds"
        exit 1
    fi
    echo "   Attempt $i/$MAX_RETRIES... waiting $INTERVAL s"
    sleep "$INTERVAL"
done

# 4. Wait for grate to finish
echo "⏳ Waiting for grate migrations to finish..."
MAX_RETRIES=15
INTERVAL=2
ATTEMPT=0
for ((i=1; i<=MAX_RETRIES; i++)); do
    STATUS=$(docker compose -f "$REPO_ROOT/docker-compose.yaml" ps -a grate --format '{{.State}}' 2>/dev/null || true)
    if [[ "$STATUS" == "exited" ]]; then
        echo "✅ Grate migrations complete"
        break
    fi
    if (( i == MAX_RETRIES )); then
        echo "❌ Grate did not finish after $((MAX_RETRIES * INTERVAL)) seconds"
        exit 1
    fi
    if (( i == 1 || i % 3 == 0 )); then
        ATTEMPT=$((ATTEMPT + 1))
        echo "   Attempt $ATTEMPT/$MAX_RETRIES... waited $((i * INTERVAL)) s"
    fi
    sleep "$INTERVAL"
done

# 5. Tail container logs in background
docker compose -f "$REPO_ROOT/docker-compose.yaml" logs -f &
LOGS_PID=$!

# 6. Run export_openapi.py to generate OpenAPI schema
echo "📝 Running export_openapi.py to generate OpenAPI schema..."
cd "$REPO_ROOT/backend"
uv run python export_openapi.py

# 7. Run npm run genclient to generate TypeScript client
echo "🎨 Running npm run genclient to generate TypeScript client..."
cd "$REPO_ROOT/frontend"
npm run genclient

# 8. Start the backend
echo "🦅 Starting backend (uv run fastapi dev main.py)..."
cd "$REPO_ROOT/backend"
uv run fastapi dev main.py &
BACKEND_PID=$!
echo "   Backend PID: $BACKEND_PID"

# 9. Start the frontend
echo "🎨 Starting frontend (npm run dev)..."
cd "$REPO_ROOT/frontend"
npm run dev &
FRONTEND_PID=$!
echo "   Frontend PID: $FRONTEND_PID"

# 10. Tail logs from all processes with prefixes
echo ""
echo "=== Backlog Boss is running ==="
echo "  Backend:  http://localhost:8000"
echo "  Frontend: http://localhost:5173"
echo "  Press Ctrl+C to stop all services"
echo ""

trap "echo '🛑 Stopping all services...'; kill $LOGS_PID $BACKEND_PID $FRONTEND_PID 2>/dev/null; docker compose -f $REPO_ROOT/docker-compose.yaml down; exit 0" INT TERM

wait -n
EXIT_CODE=$?

echo "🛑 One process exited with code $EXIT_CODE"
kill $LOGS_PID $BACKEND_PID $FRONTEND_PID 2>/dev/null
docker compose -f "$REPO_ROOT/docker-compose.yaml" down > /dev/null 2>&1
exit $EXIT_CODE