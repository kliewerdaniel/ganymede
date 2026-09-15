#!/usr/bin/env bash
# Ganymede — Admin Bootstrap Script
#
# Creates the first tenant + administrator account on a fresh deployment.
# Run once after initial docker compose up.
#
# Usage:
#   ./scripts/bootstrap_admin.sh
#
# Environment:
#   ADMIN_EMAIL    (default: admin@ganymede.local)
#   ADMIN_NAME     (default: "Administrator")
#   ADMIN_PASSWORD (default: prompts interactively)
#   TENANT_NAME    (default: "Default Organization")

set -euo pipefail

ADMIN_EMAIL="${ADMIN_EMAIL:-admin@ganymede.local}"
ADMIN_NAME="${ADMIN_NAME:-Administrator}"
TENANT_NAME="${TENANT_NAME:-Default Organization}"
API_CONTAINER="${API_CONTAINER:-ganymede-api-1}"

echo "=== Ganymede Admin Bootstrap ==="
echo ""

# Prompt for password if not set
if [ -z "${ADMIN_PASSWORD:-}" ]; then
    read -s -p "Admin password (min 8 chars): " ADMIN_PASSWORD
    echo
    if [ ${#ADMIN_PASSWORD} -lt 8 ]; then
        echo "ERROR: Password must be at least 8 characters"
        exit 1
    fi
fi

echo "Email:    ${ADMIN_EMAIL}"
echo "Name:     ${ADMIN_NAME}"
echo "Tenant:   ${TENANT_NAME}"
echo ""

# Check if an admin already exists
EXISTING=$(docker exec "${API_CONTAINER}" python3 -c "
from app.core.database import SessionLocal
from app.models import User
db = SessionLocal()
count = db.query(User).filter(User.role == 'administrator').count()
print(count)
db.close()
" 2>/dev/null || echo "0")

if [ "${EXISTING:-0}" -gt "0" ]; then
    echo "WARNING: ${EXISTING} administrator account(s) already exist."
    if [ -t 0 ]; then
        read -p "Create another admin? (y/N) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo "Aborted."
            exit 0
        fi
    else
        echo "Non-interactive mode — creating additional admin."
    fi
fi

# Create tenant + admin
RESULT=$(docker exec -e ADMIN_EMAIL="${ADMIN_EMAIL}" \
    -e ADMIN_NAME="${ADMIN_NAME}" \
    -e ADMIN_PASSWORD="${ADMIN_PASSWORD}" \
    -e TENANT_NAME="${TENANT_NAME}" \
    "${API_CONTAINER}" python3 -c "
import os, sys
from app.core.database import SessionLocal, engine
from app.models import Base, Tenant, User
from app.core.auth import hash_password

Base.metadata.create_all(bind=engine)
db = SessionLocal()

# Check if tenant with this admin email already exists
existing_user = db.query(User).filter(User.email == os.environ['ADMIN_EMAIL']).first()
if existing_user:
    print(f'ERROR: User with email {os.environ[\"ADMIN_EMAIL\"]} already exists')
    sys.exit(1)

# Create tenant
tenant = Tenant(name=os.environ['TENANT_NAME'])
db.add(tenant)
db.flush()

# Create admin user
admin = User(
    tenant_id=tenant.id,
    email=os.environ['ADMIN_EMAIL'],
    name=os.environ['ADMIN_NAME'],
    role='administrator',
    password_hash=hash_password(os.environ['ADMIN_PASSWORD']),
)
db.add(admin)
db.commit()

print(f'TENANT_ID={tenant.id}')
print(f'USER_ID={admin.id}')
print(f'EMAIL={admin.email}')
db.close()
")

echo "${RESULT}"

if echo "${RESULT}" | grep -q "^ERROR"; then
    echo ""
    echo "Bootstrap failed."
    exit 1
fi

echo ""
echo "=== Bootstrap Complete ==="
echo ""
echo "Next steps:"
echo "  1. Log in: curl -X POST http://localhost:8000/api/v1/auth/login \\"
echo "       -H 'Content-Type: application/json' \\"
echo "       -d '{\"email\":\"${ADMIN_EMAIL}\",\"password\":\"***\"}'"
echo "  2. Change default JWT_SECRET_KEY in docker-compose.yml"
echo "  3. Configure TLS (see docs/operations/tls.md)"
echo "  4. Run: ./scripts/diag.sh to verify deployment"
