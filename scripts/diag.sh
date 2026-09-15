#!/usr/bin/env bash
# Ganymede — Diagnostic Bundle
#
# Collects system diagnostics for support.
# Redacts secrets and matter content by default.
#
# Usage:
#   ./scripts/diag.sh [output_directory]
#
# Output: ganymede_diag_<timestamp>.tar.gz

set -euo pipefail

OUTPUT_DIR="${1:-./diagnostics}"
TIMESTAMP=$(date -u +%Y%m%d_%H%M%S)
WORK_DIR=$(mktemp -d)
API_CONTAINER="${API_CONTAINER:-ganymede-api-1}"
DB_CONTAINER="${DB_CONTAINER:-ganymede-db-1}"

mkdir -p "${OUTPUT_DIR}" "${WORK_DIR}/diag"

echo "=== Ganymede Diagnostic Bundle ==="
echo "Timestamp: ${TIMESTAMP}"
echo "Output:    ${OUTPUT_DIR}"
echo ""

# System info
echo "Collecting system info..."
{
    echo "Ganymede Diagnostic Bundle"
    echo "Generated: $(date -u)"
    echo "Hostname: $(hostname)"
    echo "OS: $(uname -s -r -m)"
    echo "Docker: $(docker --version 2>/dev/null || echo 'not found')"
    echo "Compose: $(docker compose version 2>/dev/null || echo 'not found')"
    echo ""
    echo "=== Container Status ==="
    docker compose ps 2>/dev/null || echo "docker compose not available"
    echo ""
    echo "=== Resource Usage ==="
    docker stats --no-stream 2>/dev/null || echo "docker stats not available"
} > "${WORK_DIR}/diag/system_info.txt"

# Docker inspect (no secrets)
echo "Collecting container configs..."
docker inspect "${API_CONTAINER}" 2>/dev/null | python3 -c "
import json, sys
data = json.load(sys.stdin)
if data:
    c = data[0]
    config = c.get('Config', {})
    # Redact env vars
    env_redacted = []
    for e in config.get('Env', []):
        if any(k in e for k in ['SECRET', 'PASSWORD', 'KEY', 'TOKEN']):
            k, _ = e.split('=', 1)
            env_redacted.append(f'{k}=***REDACTED***')
        else:
            env_redacted.append(e)
    print(f\"Image: {config.get('Image', 'unknown')}\")
    print(f\"Cmd: {config.get('Cmd')}\")
    print(f\"Env:\")
    for e in env_redacted:
        print(f'  {e}')
    print(f\"Mounts:\")
    for m in c.get('Mounts', []):
        print(f'  {m.get(\"Source\")} -> {m.get(\"Destination\")}')
" > "${WORK_DIR}/diag/container_config.txt" 2>/dev/null || echo "Could not inspect API container"

# Database health
echo "Collecting database health..."
{
    echo "=== Database Info ==="
    docker exec "${DB_CONTAINER}" psql -U ganymede -c "SELECT version();" 2>/dev/null || echo "Could not connect to DB"
    echo ""
    echo "=== Table Counts ==="
    docker exec "${DB_CONTAINER}" psql -U ganymede -c "
        SELECT 'users' as tbl, count(*) FROM users
        UNION ALL SELECT 'matters', count(*) FROM matters
        UNION ALL SELECT 'documents', count(*) FROM documents
        UNION ALL SELECT 'chunks', count(*) FROM chunks
        UNION ALL SELECT 'audit_logs', count(*) FROM audit_logs
        UNION ALL SELECT 'artifacts', count(*) FROM artifacts
        UNION ALL SELECT 'citation_feedback', count(*) FROM citation_feedback;
    " 2>/dev/null || echo "Could not query DB"
    echo ""
    echo "=== Storage Size ==="
    docker exec "${DB_CONTAINER}" psql -U ganymede -c "SELECT pg_size_pretty(pg_database_size('ganymede')) as db_size;" 2>/dev/null
    docker exec "${API_CONTAINER}" df -h /data/storage 2>/dev/null || echo "Could not check storage"
    echo ""
    echo "=== Recent Errors (last 24h) ==="
    docker exec "${DB_CONTAINER}" psql -U ganymede -c "
        SELECT created_at, action, resource_type
        FROM audit_logs
        WHERE created_at > NOW() - INTERVAL '24 hours'
        ORDER BY created_at DESC
        LIMIT 50;
    " 2>/dev/null || echo "Could not query audit logs"
} > "${WORK_DIR}/diag/database_health.txt" 2>/dev/null || echo "DB diagnostics unavailable"

# API health
echo "Collecting API health..."
{
    echo "=== API Health Endpoints ==="
    curl -s http://localhost:8000/api/v1/healthz 2>/dev/null || echo "healthz unavailable"
    echo ""
    curl -s http://localhost:8000/api/v1/readyz 2>/dev/null || echo "readyz unavailable"
    echo ""
    echo "=== Container Logs (last 100 lines, errors only) ==="
    docker logs "${API_CONTAINER}" 2>&1 | tail -100 | grep -i -E "error|exception|warning" | tail -30 || echo "No recent errors"
} > "${WORK_DIR}/diag/api_health.txt" 2>/dev/null || echo "API diagnostics unavailable"

# Ollama status
echo "Collecting Ollama status..."
{
    echo "=== Ollama Models ==="
    curl -s http://localhost:11434/api/tags 2>/dev/null | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    for m in data.get('models', []):
        print(f\"  {m['name']} ({m.get('size', 'unknown')} bytes)\")
except:
    print('  Could not list models')
" 2>/dev/null || echo "Ollama not accessible"
} > "${WORK_DIR}/diag/ollama_status.txt" 2>/dev/null || echo "Ollama diagnostics unavailable"

# Redact: make sure no matter content leaked
echo "Verifying no sensitive data in bundle..."
find "${WORK_DIR}/diag" -type f -exec grep -l -i -E "password=|secret_key=|jwt|raw_token" {} \; 2>/dev/null | while read f; do
    # Exclude matches that are clearly redacted
    if grep -q -v -E "REDACTED|\*\*\*|PASS:" "${f}" 2>/dev/null; then
        echo "  WARNING: ${f} may contain sensitive data"
    fi
done

# Package
BUNDLE_FILE="${OUTPUT_DIR}/ganymede_diag_${TIMESTAMP}.tar.gz"
tar -czf "${BUNDLE_FILE}" -C "${WORK_DIR}" diag/
rm -rf "${WORK_DIR}"

echo ""
echo "=== Bundle Complete ==="
echo "File: ${BUNDLE_FILE}"
echo "Size: $(du -h "${BUNDLE_FILE}" | cut -f1)"
echo ""
echo "Review before sharing — verify no matter content is included."
echo "Expected: system info, table counts, error logs, container configs."
