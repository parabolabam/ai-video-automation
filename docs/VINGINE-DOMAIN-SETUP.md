# Vingine Domain Setup Guide

Your backend will be accessible at: **vingine.duckdns.org**

## Quick Setup Steps

### 1. Update DuckDNS (Do this first!)

1. Go to: https://www.duckdns.org/domains
2. Find your `vingine` domain
3. Update the IP to: **134.199.244.59**
4. Click "update ip"

### 2. Test DNS (wait 1-2 minutes after updating)

```bash
# From your local machine
nslookup vingine.duckdns.org

# Should return: 134.199.244.59
ping vingine.duckdns.org
```

### 3. Setup Domain on Droplet

SSH to your droplet and run the setup script:

```bash
# From your local machine
scp -i ~/.ssh/id_dig_ocean scripts/setup-vingine-domain.sh root@134.199.244.59:~/

# SSH to droplet
ssh -i ~/.ssh/id_dig_ocean root@134.199.244.59

# Run setup script
bash ~/setup-vingine-domain.sh
```

The script will:
- ✅ Detect your droplet IP
- ✅ Install nginx (if needed)
- ✅ Configure reverse proxy
- ✅ Setup SSL with Let's Encrypt
- ✅ Configure firewall
- ✅ Setup auto-renewal for SSL

### 4. Access Your Backend

After setup completes:

- **API**: https://vingine.duckdns.org
- **Health**: https://vingine.duckdns.org/health
- **Docs**: https://vingine.duckdns.org/docs

## Manual Setup (Alternative)

If you prefer to set it up manually:

### Update DuckDNS IP

```bash
# On your droplet
curl "https://www.duckdns.org/update?domains=vingine&token=YOUR_TOKEN&ip=134.199.244.59"
```

Get your token from: https://www.duckdns.org

### Install Nginx

```bash
sudo apt-get update
sudo apt-get install -y nginx certbot python3-certbot-nginx
```

### Create Nginx Config

```bash
sudo nano /etc/nginx/sites-available/vingine-backend
```

Paste this:

```nginx
server {
    listen 80;
    server_name vingine.duckdns.org;

    client_max_body_size 500M;

    location / {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Timeouts for long-running video processing
        proxy_read_timeout 600s;
        proxy_connect_timeout 75s;
        proxy_send_timeout 600s;
    }
}
```

Enable the site:

```bash
sudo ln -s /etc/nginx/sites-available/vingine-backend /etc/nginx/sites-enabled/
sudo rm /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx
```

### Setup SSL

```bash
sudo certbot --nginx -d vingine.duckdns.org
```

Follow the prompts and choose:
- Email: your email (or skip)
- Agree to terms: Yes
- Redirect HTTP to HTTPS: Yes (recommended)

### Update Firewall

```bash
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw status
```

## Update Your Application

### Update CORS in Backend

Edit `features/platform/server.py`:

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://vingine.duckdns.org",
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Update Frontend Environment

If you have a frontend, update its API URL:

```bash
# In your frontend .env
NEXT_PUBLIC_API_URL=https://vingine.duckdns.org
```

## Auto-Update DuckDNS IP (Optional)

If your droplet IP changes, auto-update DuckDNS:

```bash
# Create update script
cat > /opt/ai-video-automation/update-duckdns.sh << 'EOF'
#!/bin/bash
TOKEN="YOUR_DUCKDNS_TOKEN"
DOMAIN="vingine"
curl "https://www.duckdns.org/update?domains=$DOMAIN&token=$TOKEN&ip="
EOF

chmod +x /opt/ai-video-automation/update-duckdns.sh

# Add to crontab (updates every 5 minutes)
(crontab -l 2>/dev/null; echo "*/5 * * * * /opt/ai-video-automation/update-duckdns.sh") | crontab -
```

Get your DuckDNS token from: https://www.duckdns.org

## Verify Setup

### Check DNS

```bash
nslookup vingine.duckdns.org
# Should return: 134.199.244.59
```

### Check SSL

```bash
curl -I https://vingine.duckdns.org/health
# Should return HTTP/2 200
```

### Check Backend

```bash
curl https://vingine.duckdns.org/health
# Should return backend health status
```

## Troubleshooting

### DNS not resolving

```bash
# Check from different DNS servers
nslookup vingine.duckdns.org 8.8.8.8
nslookup vingine.duckdns.org 1.1.1.1

# Online checker
# https://dnschecker.org/#A/vingine.duckdns.org
```

### SSL certificate failed

```bash
# Make sure backend is running first
docker ps | grep ai-video-backend

# Make sure DNS is pointing correctly
ping vingine.duckdns.org

# Try again
sudo certbot --nginx -d vingine.duckdns.org
```

### Nginx errors

```bash
# Test config
sudo nginx -t

# Check logs
sudo tail -f /var/log/nginx/error.log
sudo tail -f /var/log/nginx/access.log
```

### Backend not accessible

```bash
# Check if backend is running on port 8000
curl http://localhost:8000/health

# Check nginx is forwarding correctly
curl -H "Host: vingine.duckdns.org" http://localhost/health

# Check nginx status
sudo systemctl status nginx
```

## SSL Certificate Renewal

Certificates auto-renew via certbot systemd timer. To check:

```bash
# Check renewal timer
sudo systemctl status certbot.timer

# Test renewal (dry run)
sudo certbot renew --dry-run

# Force renewal if needed
sudo certbot renew --force-renewal
```

## Summary

| Item | Value |
|------|-------|
| **Domain** | vingine.duckdns.org |
| **Droplet IP** | 134.199.244.59 |
| **Backend Port** | 8000 |
| **Protocol** | HTTPS (with SSL) |
| **API URL** | https://vingine.duckdns.org |
| **Health Check** | https://vingine.duckdns.org/health |
| **API Docs** | https://vingine.duckdns.org/docs |

## Next Steps

After domain is setup:

1. ✅ Update GitHub secrets if using domain in deployment
2. ✅ Update frontend to use `https://vingine.duckdns.org`
3. ✅ Test all API endpoints
4. ✅ Monitor SSL expiry (auto-renews)
5. ✅ Consider rate limiting for production

---

**Quick Reference Commands:**

```bash
# SSH to droplet
ssh -i ~/.ssh/id_dig_ocean root@134.199.244.59

# View backend logs
docker logs -f ai-video-backend

# View nginx logs
sudo tail -f /var/log/nginx/access.log

# Restart nginx
sudo systemctl restart nginx

# Restart backend
docker restart ai-video-backend

# Check SSL status
sudo certbot certificates
```
