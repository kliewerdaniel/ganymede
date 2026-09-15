#!/usr/bin/env bash
# Ganymede — Encrypted Backup
#
# Creates an AES-256 encrypted backup of the PostgreSQL database.
# Uses OpenSSL for encryption (no extra dependencies).
#
# Usage:
#   ./scripts/backup_encrypted.sh [backup_directory]
#
# Environment:
#   BACKUP_PASSWORD  (prompted if not set — required)
#   BACKUP_GPG_KEY   (optional: GPG recipient for key wrapping)

set -euo pipefail

BACKUP_DIR="${1:-./backups}"
TIMESTAMP=$(date -u +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/ganymede_backup_${TIMESTAMP}.sql.gz.enc"
DB_NAME="${DB_NAME:-ganymede}"
DB_USER="${DB_USER:-ganymede}"
CONTAINER_NAME="${CONTAINER_NAME:-ganymede-db-1}"

echo "=== Ganymede Encrypted Backup ==="
echo "Target: ${BACKUP_FILE}"
echo ""

if [ -z "${BACKUP_PASSWORD:-}" ]; then
    if [ ! -t 0 ]; then
        echo "ERROR: BACKUP_PASSWORD required (or run interactively to prompt)"
        exit 1
    fi
    read -s -p "Backup encryption password: " BACKUP_PASSWORD
    echo ""
    if [ ${#BACKUP_PASSWORD} -lt 12 ]; then
        echo "ERROR: Password must be at least 12 characters"
        exit 1
    fi
    read -s -p "Confirm password: " CONFIRM_PASSWORD
    echo ""
    if [ "${BACKUP_PASSWORD}" != "${CONFIRM_PASSWORD}" ]; then
        echo "ERROR: Passwords do not match"
        exit 1
    fi
fi

mkdir -p "${BACKUP_DIR}"

# Dump → gzip → encrypt in one pipeline
docker exec -t "${CONTAINER_NAME}" pg_dump \
    --username="${DB_USER}" \
    --format=plain \
    --clean \
    --if-exists \
    --no-owner \
    --no-privileges \
    "${DB_NAME}" 2>/dev/null | \
    gzip | \
    openssl enc -aes-256-cbc -pbkdf2 -iter 100000 \
    -pass pass:"${BACKUP_PASSWORD}" \
    -out "${BACKUP_FILE}"

SIZE=$(du -h "${BACKUP_FILE}" | cut -f1)
echo ""
echo "=== Encrypted Backup Complete ==="
echo "File: ${BACKUP_FILE}"
echo "Size: ${SIZE}"
echo ""
echo "To decrypt and restore:"
echo "  openssl enc -aes-256-cbc -d -pbkdf2 -iter 100000 -in ${BACKUP_FILE} -pass pass:'YOUR_PASSWORD' | gunzip | psql -U ${DB_USER} -d ${DB_NAME}"
