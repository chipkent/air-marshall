#!/usr/bin/env bash
# Run all integration tests (Python + Flutter) against a live DB server.
# Usage: ./bin/test-integration.sh
# Requires: uv, Flutter SDK
set -uo pipefail

DB_PORT=18889
DB_API_KEY=integration-test-key
DB_PATH=$(mktemp)
BASE_URL="http://127.0.0.1:${DB_PORT}"

log() { echo "[$(date '+%H:%M:%S')] $*"; }

cleanup() {
    if [ -n "${DB_PID:-}" ]; then
        kill "$DB_PID" 2>/dev/null || true
    fi
    rm -f "$DB_PATH"
}
trap cleanup EXIT

# ---------------------------------------------------------------------------
# Start the DB server
# ---------------------------------------------------------------------------

log "==> Starting DB server on port ${DB_PORT}"
AIR_MARSHALL_DB_API_KEY="$DB_API_KEY" \
AIR_MARSHALL_DB_DB_PATH="$DB_PATH" \
AIR_MARSHALL_DB_PORT="$DB_PORT" \
    uv run air-marshall-db &
DB_PID=$!

for i in $(seq 1 30); do
    if curl -sf "${BASE_URL}/data/latest" \
            -H "X-API-Key: ${DB_API_KEY}" > /dev/null 2>&1; then
        log "Server ready"
        break
    fi
    if [ "$i" -eq 30 ]; then
        log "Server did not start in time"
        exit 1
    fi
    sleep 1
done

# ---------------------------------------------------------------------------
# Run tests
# ---------------------------------------------------------------------------

python_exit=0
flutter_exit=0

log "==> Python integration tests"
uv run pytest -m integration -v --no-cov --log-cli-level=INFO || python_exit=$?
log "Python exit code: $python_exit"

log "==> Flutter integration tests (cwd: $(pwd)/app)"
cd app
INTEGRATION_TEST_BASE_URL="$BASE_URL" \
INTEGRATION_TEST_API_KEY="$DB_API_KEY" \
    flutter test --tags integration --reporter expanded || flutter_exit=$?
log "Flutter exit code: $flutter_exit"

if [ $python_exit -ne 0 ] || [ $flutter_exit -ne 0 ]; then
    log "Integration tests failed (Python: $python_exit, Flutter: $flutter_exit)"
    exit 1
fi

log "All integration tests passed."
