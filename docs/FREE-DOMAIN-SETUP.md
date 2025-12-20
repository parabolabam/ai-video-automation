# Free Domain Setup for Backend

This guide shows you how to set up a free domain name for your backend API.

## Option 1: DuckDNS (Recommended - Easiest)

DuckDNS provides free subdomains that are easy to set up and maintain.

### Step 1: Create DuckDNS Account

1. Go to https://www.duckdns.org
2. Sign in with GitHub, Google, or Reddit
3. Choose a subdomain (e.g., `mybackend`)
4. Add your droplet IP address
5. Click "Add domain"

You'll get: `mybackend.duckdns.org`

### Step 2: Point to Your Droplet

1. In DuckDNS dashboard, enter your droplet IP in the "current ip" field
2. Click "update ip"
3. Done! Your domain now points to your droplet

### Step 3: Test

```bash
# Test DNS resolution
nslookup mybackend.duckdns.org

# Should return your droplet IP
ping mybackend.duckdns.org
```

### Step 4: Update Your Backend URL

Your backend will now be accessible at:
- `http://mybackend.duckdns.org:8000`

### Step 5: Setup SSL (Optional but Recommended)

See SSL setup section below.

---

## Option 2: Freenom (Free .tk, .ml, .ga domains)

Freenom offers completely free domain names.

### Step 1: Register Domain

1. Go to https://www.freenom.com
2. Search for available domain (e.g., `mybackend.tk`)
3. Click "Get it now" and checkout (it's free)
4. Create an account
5. Complete registration

### Step 2: Configure DNS

1. Go to "Services" → "My Domains"
2. Click "Manage Domain" next to your domain
3. Go to "Management Tools" → "Nameservers"
4. Choose "Use custom nameservers"
5. Enter Digital Ocean nameservers:
   - `ns1.digitalocean.com`
   - `ns2.digitalocean.com`
   - `ns3.digitalocean.com`

### Step 3: Add DNS Records in Digital Ocean

1. Log in to Digital Ocean dashboard
2. Go to "Networking" → "Domains"
3. Add your domain (e.g., `mybackend.tk`)
4. Add an A record:
   - **Hostname**: `@` (or `api` for `api.mybackend.tk`)
   - **Will Direct To**: Select your droplet
   - **TTL**: 3600

### Step 4: Wait for DNS Propagation

DNS changes can take 24-48 hours to propagate globally. Check status:

```bash
# Check if DNS is working
dig mybackend.tk

# Or use online tool
# https://dnschecker.org
```

---

## Option 3: eu.org (Free .eu.org domain)

### Step 1: Register

1. Go to https://nic.eu.org
2. Create an account
3. Request a domain (e.g., `mybackend.eu.org`)
4. Wait for approval (typically 1-7 days)

### Step 2: Configure DNS

Once approved, add DNS records:

1. Log in to eu.org control panel
2. Add A record pointing to your droplet IP
3. Wait for DNS propagation

---

## Setting Up SSL/HTTPS (Free with Let's Encrypt)

Once you have a domain, you should set up HTTPS for security.

### Install Certbot on Your Droplet

```bash
# SSH to your droplet
ssh -i ~/.ssh/id_dig_ocean root@YOUR_DROPLET_IP

# Install Certbot and Nginx
sudo apt-get update
sudo apt-get install -y certbot python3-certbot-nginx nginx

# Get SSL certificate
sudo certbot --nginx -d yourdomain.duckdns.org

# Follow the prompts
# Choose: Redirect HTTP to HTTPS (recommended)
```

### Configure Nginx as Reverse Proxy

Create nginx config:

```bash
sudo nano /etc/nginx/sites-available/backend
```

Add this configuration:

```nginx
server {
    server_name yourdomain.duckdns.org;

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
    }

    # SSL configuration will be added by Certbot
}
```

Enable the site:

```bash
sudo ln -s /etc/nginx/sites-available/backend /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

Now your backend is accessible at:
- ✅ `https://yourdomain.duckdns.org` (SSL secured!)

---

## Updating Your Application

### Update Environment Variables

Add to your droplet's `.env`:

```bash
BACKEND_URL=https://yourdomain.duckdns.org
```

### Update CORS Settings

In your FastAPI backend (`features/platform/server.py`), update CORS:

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://yourdomain.duckdns.org",
        "http://localhost:3000",  # for local development
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## Auto-Renew SSL Certificate

Let's Encrypt certificates expire after 90 days. Set up auto-renewal:

```bash
# Test renewal
sudo certbot renew --dry-run

# Auto-renewal is already set up by certbot
# It creates a cron job automatically
# Check it:
sudo systemctl status certbot.timer
```

---

## DNS Update Script (for DuckDNS)

If your droplet IP changes, update DuckDNS automatically:

```bash
# Create update script
cat > /opt/ai-video-automation/update-duckdns.sh << 'EOF'
#!/bin/bash
TOKEN="your-duckdns-token"
DOMAIN="mybackend"
echo url="https://www.duckdns.org/update?domains=$DOMAIN&token=$TOKEN&ip=" | curl -k -o /var/log/duckdns.log -K -
EOF

chmod +x /opt/ai-video-automation/update-duckdns.sh

# Add to crontab (runs every 5 minutes)
(crontab -l 2>/dev/null; echo "*/5 * * * * /opt/ai-video-automation/update-duckdns.sh") | crontab -
```

Get your DuckDNS token from: https://www.duckdns.org

---

## Summary

### DuckDNS (Easiest)
- ✅ Free forever
- ✅ Instant setup
- ✅ No approval needed
- ✅ Auto-renewal scripts available
- ❌ Subdomain only (e.g., `mybackend.duckdns.org`)

### Freenom
- ✅ Free for 12 months (renewable)
- ✅ Full domain (e.g., `mybackend.tk`)
- ✅ More professional looking
- ❌ Requires account
- ❌ DNS propagation delay

### eu.org
- ✅ Free forever
- ✅ Full domain (e.g., `mybackend.eu.org`)
- ✅ More professional than .tk
- ❌ Requires approval (1-7 days)
- ❌ Manual DNS management

---

## Recommended Setup

For quick testing: **DuckDNS**
For production: **Freenom** or buy a cheap domain ($1-5/year on Namecheap, Porkbun)

---

## After Setup Checklist

- [ ] Domain points to droplet IP
- [ ] DNS propagation complete
- [ ] SSL certificate installed
- [ ] Nginx reverse proxy configured
- [ ] Firewall allows HTTPS (port 443)
- [ ] CORS settings updated
- [ ] Test: `https://yourdomain.com/health`

---

## Troubleshooting

### Domain not resolving
```bash
# Check DNS
nslookup yourdomain.duckdns.org

# Check from different locations
# https://dnschecker.org
```

### SSL certificate failed
```bash
# Make sure port 80 is open
sudo ufw allow 80/tcp

# Make sure domain resolves to your IP first
ping yourdomain.duckdns.org

# Try again
sudo certbot --nginx -d yourdomain.duckdns.org
```

### Nginx errors
```bash
# Check nginx config
sudo nginx -t

# Check nginx logs
sudo tail -f /var/log/nginx/error.log
```
