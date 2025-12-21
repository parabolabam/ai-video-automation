#!/bin/bash
set -e

echo "Starting certificate renewal check..."
certbot renew --non-interactive --webroot -w /var/www/certbot

# Reload nginx if certificates were renewed
if [ $? -eq 0 ]; then
    echo "Certificates renewed successfully"
    # Signal nginx to reload (requires shared volume or network communication)
    echo "Nginx should be reloaded to use new certificates"
fi
