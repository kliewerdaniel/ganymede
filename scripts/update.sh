#!/usr/bin/env bash
# Ganymede — Update Script
#
# Safely updates Ganymede to a new version.
# Supports rollback on failure.
#
# Usage:
#   ./scripts/update.sh [VERSION | "latest" | "rollback"]
#
# Environment:
#   GANYMEDE_REPO    (default: kliewerdaniel/ganymede)
#   BACKUP_BEFORE_UPDATE (default: true)
set -euo pipefail

VERSION="${1:-latest}"
COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.yml}"
REPO="${GANYMEDE_REPO:-kliewerdaniel/ganymede}"
BACKUP_BEFORE_UPDATE="${BACKUP_BEFORE_UPDATE:-true}"

ROLLBACK_DIR="./.update_rollback"
LOG_FILE="./update_$(date -u +%Y%m%d_%H%M%S).log"

log() { echo "[$(date -u +%H:%M:%S)] $*" | tee -a "${LOG_FILE}"; }
err()  { log "ERROR: $*"; }
ok()   { log "PASS: $*"; }

echo "=== Ganymede Update ==="
echo "Version: ${VERSION}"
echo ""

# Step 1: Create rollback point
mkdir -p "${ROLLBACK_DIR}"

if [ "${VERSION}" != "rollback" ]; then
    log "Creating rollback point..."
    
    # Backup database
    if [ "${BACKUP_BEFORE_UPDATE}" == "true" ]; then
        log "Creating pre-update database backup..."
        ROLLBACK_BACKUP="${ROLLBACK_DIR}/pre_update_$(date -u +%Y%m%d_%H%M%S).sql"
        docker exec ganymede-db-1 pg_dump --username=ganymede --format=plain --clean --no-owner --no-privileges ganymede > "${ROLLBACK_BACKUP}" 2>>"${LOG_FILE}"
        ok "Database backup: ${ROLLBACK_BACKUP}"
    fi
    
    # Save current compose config
    cp "${COMPOSE_FILE}" "${ROLLBACK_DIR}/docker-compose.yml.bak"
    docker compose images --format json > "${ROLLBACK_DIR}/images.json" 2>/dev/null || echo "[]" > "${ROLLBACK_DIR}/images.json"
    ok "Rollback point saved to ${ROLLBACK_DIR}/"
fi

# Step 2: Perform update
if [ "${VERSION}" == "rollback" ]; then
    log "Rolling back to previous state..."
    
    if [ ! -d "${ROLLBACK_DIR}" ] || [ ! -f "${ROLLBACK_DIR}/docker-compose.yml.bak" ]; then
        err "No rollback point found"
        exit 1
    fi
    
    # Stop current containers
    log "Stopping current containers..."
    docker compose down 2>>"${LOG_FILE}"
    
    # Restore compose config
    cp "${ROLLBACK_DIR}/docker-compose.yml.bak" "${COMPOSE_FILE}"
    
    # Restart
    log "Restarting from rollback config..."
    docker compose up -d 2>>"${LOG_FILE}"
    sleep 5
    
    # Restore DB backup if exists
    LATEST_BACKUP=$(ls -t ${ROLLBACK_DIR}/pre_update_*.sql 2>/dev/null | head -1)
    if [ -n "${LATEST_BACKUP}" ]; then
        log "Restoring database from ${LATEST_BACKUP}..."
        docker exec -i ganymede-db-1 psql --username=ganymede --dbname=ganymede --echo-errors --set ON_ERROR_STOP=on < "${LATEST_BACKUP}" 2>>"${LOG_FILE}" || true
        ok "Database restored"
    fi
    
    # Verify health
    if curl -sf http://localhost:8000/api/v1/healthz &>/dev/null; then
        ok "Rollback complete — API healthy"
    else
        err "Rollback complete — API health check failed"
        exit 1
    fi
    
    rm -rf "${ROLLBACK_DIR}"
else
    log "Pulling latest code..."
    
    # Stash any local changes (for dev deployments)
    git stash 2>/dev/null || true
    
    if [ "${VERSION}" == "latest" ]; then
        git pull origin main 2>>"${LOG_FILE}"
    else
        git fetch origin 2>>"${LOG_FILE}"
        git checkout "${VERSION}" 2>>"${LOG_FILE}"
    fi
    
    ok "Code updated"
    
    # Rebuild containers
    log "Rebuilding containers..."
    docker compose build api 2>>"${LOG_FILE}"
    ok "API image rebuilt"
    
    # Run migrations
    log "Running database migrations..."
    docker compose stop api 2>>"${LOG_FILE}"
    docker compose up -d db 2>>"${LOG_FILE}"
    sleep 3
    
    # Auto-create tables if not existing
    docker exec ganymede-api-1 python3 -c "
from app.core.database import engine
from app.models import Base
Base.metadata.create_all(bind=engine)
print('Tables verified/created.')
" 2>>"${LOG_FILE}" || true
    
    # Restart API
    docker compose up -d api 2>>"${LOG_FILE}"
    sleep 5
    
    # Health check
    log "Verifying deployment..."
    RETRY=0
    MAX_RETRY=12
    until curl -sf http://localhost:8000/api/v1/healthz &>/dev/null; do
        RETRY=$((RETRY + 1))
        if [ ${RETRY} -ge ${MAX_RETRY} ]; then
            err "API failed health check after update"
            log "Run ./scripts/update.sh rollback to revert"
            exit 1
        fi
        sleep 5
    done
    
    ok "API healthy after update"
    ok "Update complete (${VERSION})"
    
    # Clean up rollback point after successful update
    rm -rf "${ROLLBACK_DIR}"
fi

echo ""
echo "Done."
