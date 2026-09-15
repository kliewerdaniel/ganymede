#!/usr/bin/env bash
# Ganymede — TLS Setup Script
#
# Configures TLS for Ganymede using self-signed certs or Let's Encrypt.
#
# Usage:
#   ./scripts/setup_tls.sh <domain> [--letsencrypt | --selfsigned]
#
# Without --letsencrypt, generates self-signed certs for testing only.

set -euo pipefail

DOMAIN="${1:-}"
MODE="${2:---selfsigned}"

if [ -z "${DOMAIN}" ]; then
    echo "ERROR: Domain required"
    echo "Usage: $0 <domain> [--letsencrypt | --selfsigned]"
    exit 1
fi

TLS_DIR="./tls"
mkdir -p "${TLS_DIR}"

if [ "${MODE}" == "--letsencrypt" ]; then
    echo "=== Let's Encrypt TLS Setup ==="
    echo "Domain: ${DOMAIN}"
    echo ""
    
    if ! command -v certbot &>/dev/null; then
        echo "Installing certbot..."
        brew install certbot 2>/dev/null || {
            echo "ERROR: Could not install certbot"
            echo "Install manually: https://certbot.eff.org/"
            exit 1
        }
    fi
    
    # Stop any process on port 80
    echo "NOTE: Port 80 must be free for HTTP challenge"
    
    sudo certbot certonly --standalone -d "${DOMAIN}" --agree-tos -n --email admin@"${DOMAIN}"
    
    # Copy certs
    cp "/etc/letsencrypt/live/${DOMAIN}/fullchain.pem" "${TLS_DIR}/cert.pem"
    cp "/etc/letsencrypt/live/${DOMAIN}/privkey.pem" "${TLS_DIR}/key.pem"
    
    echo ""
    echo "Certs installed. Auto-renewal configured via certbot."
else
    echo "=== Self-Signed TLS Setup ==="
    echo "Domain: ${DOMAIN}"
    echo "WARNING: Self-signed certs are for TESTING ONLY"
    echo ""
    
    openssl req -x509 -nodes -days 365 \
        -newkey rsa:2048 \
        -keyout "${TLS_DIR}/key.pem" \
        -out "${TLS_DIR}/cert.pem" \
        -subj "/CN=${DOMAIN}" \
        -addext "subjectAltName=DNS:${DOMAIN},DNS:localhost,IP:127.0.0.1"
    
    echo "Self-signed cert generated: ${TLS_DIR}/cert.pem"
fi

echo ""
echo "TLS files:"
echo "  Certificate: ${TLS_DIR}/cert.pem"
echo "  Key:         ${TLS_DIR}/key.pem"
echo ""
echo "Next: update docker-compose.yml to use TLS:"
echo ""
echo "  api:"
echo "    ports:"
echo "      - '443:8000'"
echo "    environment:"
echo "      TLS_CERT: /tls/cert.pem"
echo "      TLS_KEY: /tls/key.pem"
echo "    volumes:"
echo "      - ./tls:/tls"
