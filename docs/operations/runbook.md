# Ganymede — Pilot-Readiness Runbook

**Version:** 0.1.0
**Date:** September 2026
**Owner:** Ganymede Engineering

This runbook covers installation, backups, updates, and recovery.

---

## Quick Start

```bash
# 1. Clone and start
git clone https://github.com/kliewerdaniel/ganymede.git
cd ganymede
docker compose up -d

# 2. Validate environment
./scripts/validate_env.sh
# Should show: all checks passed, JWT warning expected

# 3. Bootstrap first admin
./scripts/bootstrap_admin.sh
# Sets up tenant + admin account

# 4. Verify
curl http://localhost:8000/api/v1/healthz
# Should return: {"status": "ok"}

# 5. Log in
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@ganymede.local","password":"***"}'
```

---

## Installation

### Requirements

- Docker Desktop 4.0+ with Compose
- 4 CPU cores, 16GB RAM minimum
- 10GB+ free disk space
- macOS (ARM64/x86_64) or Linux (x86_64)
- Ollama running on host (install: https://ollama.com)

### First Deploy

```bash
# Start services
docker compose up -d

# Wait for health
docker compose ps
# Both db and api should show "running" and healthy

# Bootstrap admin
export ADMIN_EMAIL="you@yourfirm.com"
export ADMIN_PASSWORD="secure-password-here"
./scripts/bootstrap_admin.sh

# Verify
./scripts/validate_env.sh
```

### Production Hardening

1. **Change JWT secret:**
   ```bash
   # Generate a strong secret
   openssl rand -hex 32
   # Update docker-compose.yml: JWT_SECRET_KEY=<generated>
   docker compose restart api
   ```

2. **Enable TLS:**
   ```bash
   # For testing:
   ./scripts/setup_tls.sh yourdomain.com --selfsigned
   
   # For production:
   ./scripts/setup_tls.sh yourdomain.com --letsencrypt
   ```

3. **Configure Ollama models:**
   ```bash
   # Required models
   ollama pull qwen3:8b        # Verifier
   ollama pull nomic-embed-text # Embeddings
   ```

---

## Backups

### Manual Backup

```bash
# Plain backup
./scripts/backup.sh ./backups

# Encrypted backup (recommended for offsite)
export BACKUP_PASSWORD="strong-passphrase"
./scripts/backup_encrypted.sh ./backups
```

### Automated Backups

Add to crontab:

```bash
# Daily at 2 AM
0 2 * * * cd /path/to/ganymede && ./scripts/backup_encrypted.sh /backups/ganymede
```

### Restore

```bash
# From plain backup
./scripts/restore.sh ./backups/ganymede_backup_20260915_120000.sql

# From encrypted backup
openssl enc -aes-256-cbc -d -pbkdf2 -iter 100000 \
  -in ./backups/ganymede_backup_*.sql.gz.enc \
  -pass pass:'YOUR_PASSWORD' | gunzip | \
  docker exec -i ganymede-db-1 psql -U ganymede -d ganymede
```

---

## Updates

### Standard Update

```bash
# Update to latest
./scripts/update.sh latest

# Update to specific version
./scripts/update.sh v0.2.0
```

### Rollback

```bash
# If update fails
./scripts/update.sh rollback
```

### Update Safety

- Pre-update backup is automatic
- Rollback point saved to `.update_rollback/`
- Health check verifies API after update
- Database migrations run automatically

---

## Monitoring

### Health Endpoints

| Endpoint | Purpose |
|----------|---------|
| `/api/v1/healthz` | Liveness probe |
| `/api/v1/readyz` | Readiness (DB + Ollama) |
| `/api/v1/health/detailed` | Full system status |
| `/api/v1/health/db` | Database connectivity |
| `/api/v1/health/ollama` | Ollama model status |

### Diagnostic Bundle

```bash
./scripts/diag.sh ./diagnostics
# Creates: ganymede_diag_<timestamp>.tar.gz
# Redacts secrets and matter content
```

### Logs

```bash
# API logs
docker logs ganymede-api-1 --tail 100

# DB logs
docker logs ganymede-db-1 --tail 100

# Follow
docker logs ganymede-api-1 -f
```

---

## Troubleshooting

### API won't start

```bash
# Check containers
docker compose ps

# Check logs
docker logs ganymede-api-1 --tail 50

# Restart
docker compose restart api
```

### Database connection failed

```bash
# Check DB is running
docker exec ganymede-db-1 pg_isready -U ganymede

# Check connection from API
docker exec ganymede-api-1 python3 -c "
from app.core.database import engine
engine.connect()
print('DB connection OK')
"
```

### Ollama not reachable

```bash
# Check Ollama on host
curl http://localhost:11434/api/tags

# Check from container
docker exec ganymede-api-1 curl -s http://host.docker.internal:11434/api/tags

# Verify models
ollama list
```

### Reset Everything

```bash
# WARNING: Destroys all data
docker compose down -v
docker compose up -d
./scripts/bootstrap_admin.sh
```

---

## Security

### Default Credentials

- **NEVER** deploy with default JWT_SECRET_KEY
- **NEVER** use default admin password in production
- **ALWAYS** enable TLS for production deployments

### Access Control

- 5 roles: administrator, attorney, reviewer, paralegal, it_operator
- Matter-level membership required for access
- Audit log records all actions

### Data Protection

- All data stays in your Docker volumes
- No egress to external services (except Ollama on host)
- Encrypted backups for offsite storage
- Diagnostic bundle redacts secrets by default

---

## Reference

| Component | Port | Protocol |
|-----------|------|----------|
| API | 8000 | HTTP (TLS in prod) |
| PostgreSQL | 5432 | TCP |
| Ollama | 11434 | HTTP (host only) |

| Volume | Purpose |
|--------|---------|
| `db_data` | PostgreSQL data |
| `api_storage` | Uploaded documents |

---

## Support

- Issues: https://github.com/kliewerdaniel/ganymede/issues
- Diagnostics: `./scripts/diag.sh`
- Logs: `docker logs ganymede-api-1`
