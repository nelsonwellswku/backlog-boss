#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

LOGS_PID=""
BACKEND_PID=""
FRONTEND_PID=""
CLEANED_UP=false

cleanup() {
    if [[ "$CLEANED_UP" == true ]]; then
        return
    fi
    CLEANED_UP=true
    echo
    echo "🛑 Stopping all services..."
    if [[ -n "$FRONTEND_PID" ]]; then
        echo "🛑 Stopping frontend..."
        kill -- -"$FRONTEND_PID" 2>/dev/null || kill "$FRONTEND_PID" 2>/dev/null || true
    fi
    if [[ -n "$BACKEND_PID" ]]; then
        echo "🛑 Stopping backend..."
        kill -- -"$BACKEND_PID" 2>/dev/null || kill "$BACKEND_PID" 2>/dev/null || true
    fi
    if [[ -n "$LOGS_PID" ]]; then
        kill "$LOGS_PID" 2>/dev/null || true
    fi
    echo "🛑 Stopping database..."
    docker compose -f "$REPO_ROOT/docker-compose.yaml" down > /dev/null 2>&1 || true
    echo "✅ Shutdown complete."
}

trap cleanup INT TERM EXIT

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
for ((i=1; i<=MAX_RETRIES; i++)); do
    STATUS=$(docker compose -f "$REPO_ROOT/docker-compose.yaml" ps -a grate --format '{{.State}} {{.ExitCode}}' 2>/dev/null || true)
    if [[ "$STATUS" == "exited 0" ]]; then
        echo "✅ Grate migrations complete"
        break
    fi
    if [[ "$STATUS" == exited\ * ]]; then
        echo "❌ Grate migrations failed (exit code: ${STATUS#* })"
        exit 1
    fi
    if (( i == MAX_RETRIES )); then
        echo "❌ Grate did not finish after $((MAX_RETRIES * INTERVAL)) seconds"
        exit 1
    fi
    if (( i == 1 || i % 3 == 0 )); then
        echo "   Waiting for grate... $((i * INTERVAL)) s"
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

# 8. Start the backend (in its own process group so child processes are killed too)
echo "🦅 Starting backend (uv run fastapi dev main.py)..."
cd "$REPO_ROOT/backend"
setsid bash -c 'uv run fastapi dev main.py' &
BACKEND_PID=$!
echo "   Backend PID: $BACKEND_PID"

# 9. Start the frontend (in its own process group so child processes are killed too)
echo "🎨 Starting frontend (npm run dev)..."
cd "$REPO_ROOT/frontend"
setsid bash -c 'npm run dev' &
FRONTEND_PID=$!
echo "   Frontend PID: $FRONTEND_PID"

# 10. Tail logs from all processes with prefixes
echo ""
echo "=== Backlog Boss is running ==="
echo "  Backend:  http://localhost:8000"
echo "  Frontend: http://localhost:5173"
echo "  Press Ctrl+C to stop all services"
echo ""

wait -n
EXIT_CODE=$?

echo "🛑 One process exited with code $EXIT_CODE"
exit $EXIT_CODE
