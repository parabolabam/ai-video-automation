#!/bin/bash

# Initialize Let's Encrypt certificates using Docker volumes
# This script runs ONCE to generate initial certificates
# After that, the certbot container handles renewals automatically

set -e

DOMAIN="vingine.duckdns.org"
EMAIL="parabolabam@gmail.com"
STAGING=0  # Set to 1 for testing to avoid rate limits

echo "=========================================="
echo "Let's Encrypt Certificate Initialization"
echo "=========================================="
echo "Domain: $DOMAIN"
echo "Email: $EMAIL"
echo "=========================================="

# Check if certificates already exist
if docker volume inspect ai-video-automation_letsencrypt_certs >/dev/null 2>&1; then
    echo "Checking for existing certificates..."
    if docker run --rm \
        -v ai-video-automation_letsencrypt_certs:/etc/letsencrypt \
        certbot/certbot:latest \
        certificates 2>/dev/null | grep -q "$DOMAIN"; then
        echo "✅ Certificates already exist for $DOMAIN"
        echo "Skipping certificate generation"
        exit 0
    fi
fi

echo "Generating new certificates for $DOMAIN..."

# Temporary stop nginx if running to free up port 80
docker stop ai-video-nginx 2>/dev/null || true

# Generate certificates using standalone mode
if [ $STAGING -eq 1 ]; then
    echo "⚠️  Running in STAGING mode (test certificates)"
    STAGING_ARG="--staging"
else
    STAGING_ARG=""
fi

docker run --rm \
    -p 80:80 \
    -p 443:443 \
    -v ai-video-automation_letsencrypt_certs:/etc/letsencrypt \
    -v ai-video-automation_certbot_www:/var/www/certbot \
    certbot/certbot:latest \
    certonly \
    --standalone \
    --preferred-challenges http \
    -d "$DOMAIN" \
    --email "$EMAIL" \
    --agree-tos \
    --non-interactive \
    $STAGING_ARG

if [ $? -eq 0 ]; then
    echo "=========================================="
    echo "✅ Certificates generated successfully!"
    echo "=========================================="
    echo "Certificates are stored in Docker volume: ai-video-automation_letsencrypt_certs"
    echo "Now start your containers with: docker-compose up -d"
else
    echo "=========================================="
    echo "❌ Certificate generation failed"
    echo "=========================================="
    exit 1
fi
