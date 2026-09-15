#!/usr/bin/env bash
# Ganymede — Environment Validation
#
# Checks deployment prerequisites.
#
# Usage:
#   ./scripts/validate_env.sh
#
# Exit codes:
#   0 = all checks passed
#   1 = warnings found (non-critical)
#   2 = critical failures

set -euo pipefail

WARNINGS=0
ERRORS=0

ok()   { echo "  [PASS] $1"; }
warn() { echo "  [WARN] $1"; WARNINGS=$((WARNINGS + 1)); }
err()  { echo "  [FAIL] $1"; ERRORS=$((ERRORS + 1)); }

echo "=== Ganymede Environment Validation ==="
echo ""

# Docker
echo "Docker:"
if command -v docker &>/dev/null && docker info &>/dev/null; then
    ok "Docker daemon running ($(docker --version))"
else
    err "Docker not available"
fi

if docker compose version &>/dev/null; then
    ok "Docker Compose available ($(docker compose version | head -1))"
else
    err "Docker Compose not available"
fi

# Containers
echo ""
echo "Containers:"
for svc in db api; do
    CONTAINER="ganymede-${svc}-1"
    if docker inspect "${CONTAINER}" &>/dev/null; then
        STATE=$(docker inspect -f '{{.State.Status}}' "${CONTAINER}" 2>/dev/null || echo "unknown")
        if [ "${STATE}" == "running" ]; then
            ok "${CONTAINER}: running"
        else
            err "${CONTAINER}: ${STATE}"
        fi
    else
        err "${CONTAINER}: not found"
    fi
done

# Ports
echo ""
echo "Ports:"
if curl -sf http://localhost:8000/api/v1/healthz &>/dev/null; then
    ok "API port 8000: responding"
else
    err "API port 8000: not responding"
fi

if pg_isready -h localhost -p 5432 -U ganymede &>/dev/null; then
    ok "PostgreSQL port 5432: accepting connections"
else
    warn "PostgreSQL port 5432: not accepting connections (may need DB password)"
fi

# Disk space
echo ""
echo "Disk Space:"
AVAIL_KB=$(df -k . | awk 'NR==2 {print $4}')
AVAIL_GB=$((AVAIL_KB / 1048576))
if [ ${AVAIL_GB} -ge 10 ]; then
    ok "Available: ${AVAIL_GB}GB"
elif [ ${AVAIL_GB} -ge 2 ]; then
    warn "Available: ${AVAIL_GB}GB (recommend 10GB+)"
else
    err "Available: ${AVAIL_GB}GB (need at least 10GB)"
fi

# Memory
echo ""
echo "Memory:"
TOTAL_MEM_KB=$(sysctl -n hw.memsize 2>/dev/null | awk '{print $1 / 1024}' || echo "0")
TOTAL_MEM_GB=$((TOTAL_MEM_KB / 1048576))
if [ ${TOTAL_MEM_GB} -ge 16 ]; then
    ok "Total RAM: ${TOTAL_MEM_GB}GB"
elif [ ${TOTAL_MEM_GB} -ge 8 ]; then
    warn "Total RAM: ${TOTAL_MEM_GB}GB (recommend 16GB+ for local models)"
else
    err "Total RAM: ${TOTAL_MEM_GB}GB (minimum 8GB)"
fi

# Ollama
echo ""
echo "Ollama:"
if curl -sf http://localhost:11434/api/tags &>/dev/null; then
    MODEL_COUNT=$(curl -s http://localhost:11434/api/tags | python3 -c "import sys,json; print(len(json.load(sys.stdin).get('models', [])))" 2>/dev/null || echo "0")
    ok "Ollama reachable at localhost:11434 (${MODEL_COUNT} models)"
    if [ "${MODEL_COUNT}" -lt "1" ]; then
        warn "No Ollama models installed"
    fi
else
    warn "Ollama not reachable at localhost:11434 (verify OLLAMA_ENDPOINTS)"
fi

# Security
echo ""
echo "Security:"
JWT_SECRET=$(grep JWT_SECRET_KEY docker-compose.yml 2>/dev/null | head -1 || echo "")
if echo "${JWT_SECRET}" | grep -q "dev-jwt-secret-change-in-production"; then
    warn "JWT_SECRET_KEY is default — change before production"
elif echo "${JWT_SECRET}" | grep -q "CHANGE"; then
    warn "JWT_SECRET_KEY has placeholder value"
else
    ok "JWT_SECRET_KEY appears customized"
fi

# Summary
echo ""
echo "=== Summary ==="
if [ ${ERRORS} -eq 0 ] && [ ${WARNINGS} -eq 0 ]; then
    echo "All checks passed."
    exit 0
elif [ ${ERRORS} -eq 0 ]; then
    echo "${WARNINGS} warning(s), 0 errors."
    exit 1
else
    echo "${ERRORS} error(s), ${WARNINGS} warning(s)."
    exit 2
fi
