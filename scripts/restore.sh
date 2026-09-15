#!/usr/bin/env bash
# Ganymede — Restore Script
#
# Restores a Ganymede database from a pg_dump backup file.
#
# Usage:
#   ./scripts/restore.sh <backup_file.sql>
#   ./scripts/restore.sh ./backups/ganymede_backup_20260915_120000.sql
#
# WARNING: This will DROP existing tables and recreate them.
#          All current data will be lost.

set -euo pipefail

BACKUP_FILE="${1:-}"
CONTAINER_NAME="${CONTAINER_NAME:-ganymede-db-1}"
DB_NAME="${DB_NAME:-ganymede}"
DB_USER="${DB_USER:-ganymede}"

if [ -z "${BACKUP_FILE}" ]; then
    echo "ERROR: No backup file specified"
    echo "Usage: $0 <backup_file.sql>"
    exit 1
fi

if [ ! -f "${BACKUP_FILE}" ]; then
    echo "ERROR: Backup file not found: ${BACKUP_FILE}"
    exit 1
fi

echo "=== Ganymede Restore ==="
echo "Container: ${CONTAINER_NAME}"
echo "Database:  ${DB_NAME}"
echo "Source:    ${BACKUP_FILE}"
echo ""

read -p "This will DESTROY existing data. Continue? (y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Aborted."
    exit 1
fi

docker exec -i "${CONTAINER_NAME}" psql \
    --username="${DB_USER}" \
    --dbname="${DB_NAME}" \
    --echo-errors \
    --set ON_ERROR_STOP=on < "${BACKUP_FILE}"

if [ $? -eq 0 ]; then
    echo ""
    echo "=== Restore Complete ==="
else
    echo "ERROR: Restore failed"
    exit 1
fi
