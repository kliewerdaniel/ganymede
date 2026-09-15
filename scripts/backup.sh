#!/usr/bin/env bash
# Ganymede — Backup Script
#
# Creates a pg_dump backup of the PostgreSQL database.
#
# Usage:
#   ./scripts/backup.sh [backup_directory]
#   docker exec -t ganymede-db-1 ./scripts/backup.sh /var/backups
#
# Defaults:
#   backup_directory = ./backups
#   Database: ganymede/ganymede@localhost:5432/ganymede

set -euo pipefail

BACKUP_DIR="${1:-./backups}"
TIMESTAMP=$(date -u +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/ganymede_backup_${TIMESTAMP}.sql"
CONTAINER_NAME="${CONTAINER_NAME:-ganymede-db-1}"
DB_NAME="${DB_NAME:-ganymede}"
DB_USER="${DB_USER:-ganymede}"

echo "=== Ganymede Backup ==="
echo "Container: ${CONTAINER_NAME}"
echo "Database:  ${DB_NAME}"
echo "User:      ${DB_USER}"
echo "Target:    ${BACKUP_FILE}"
echo ""

mkdir -p "${BACKUP_DIR}"

# Run pg_dump inside the DB container
docker exec -t "${CONTAINER_NAME}" pg_dump \
    --username="${DB_USER}" \
    --format=plain \
    --clean \
    --if-exists \
    --no-owner \
    --no-privileges \
    "${DB_NAME}" > "${BACKUP_FILE}"

if [ $? -eq 0 ]; then
    SIZE=$(du -h "${BACKUP_FILE}" | cut -f1)
    echo ""
    echo "=== Backup Complete ==="
    echo "File: ${BACKUP_FILE}"
    echo "Size: ${SIZE}"
else
    echo "ERROR: Backup failed"
    rm -f "${BACKUP_FILE}"
    exit 1
fi
