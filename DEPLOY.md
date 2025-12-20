# Deploying to Digital Ocean

This guide walks you through deploying the AI Video Automation platform to a Digital Ocean droplet with a free domain using nip.io.

## Prerequisites

- Digital Ocean account
- Your API keys ready:
  - `SUPABASE_URL` and `SUPABASE_KEY`
  - `OPENAI_API_KEY`
  - `KIE_API_KEY` (optional, for video generation)
  - YouTube OAuth credentials (optional, for publishing)

## Step 1: Create a Digital Ocean Droplet

1. Log into [Digital Ocean](https://cloud.digitalocean.com/)

2. Click **Create** → **Droplets**

3. Choose configuration:
   - **Region**: Choose closest to your users
   - **Image**: Ubuntu 24.04 LTS
   - **Size**: Basic → Regular (Recommend **2GB RAM / 1 vCPU** minimum, **4GB RAM / 2 vCPU** for video processing)
   - **Authentication**: SSH Key (recommended) or Password

4. Click **Create Droplet**

5. Note your droplet's **IP address** (e.g., `167.99.123.45`)

## Step 2: Free Domain with nip.io

No domain registration needed! Use [nip.io](https://nip.io) for automatic DNS:

```
http://167.99.123.45.nip.io
```

This automatically resolves `167.99.123.45.nip.io` to `167.99.123.45`.

**Other free domain options:**
- **nip.io**: `YOUR_IP.nip.io`
- **sslip.io**: `YOUR_IP.sslip.io`
- **xip.io**: `YOUR_IP.xip.io`

## Step 3: Connect to Your Droplet

```bash
ssh root@YOUR_DROPLET_IP
```

## Step 4: Run Setup Script

```bash
# Download and run the setup script
curl -fsSL https://raw.githubusercontent.com/YOUR_REPO/main/deploy/setup-droplet.sh | bash

# Or manually:
apt update && apt upgrade -y
apt install -y docker.io docker-compose git curl ufw

# Enable and start Docker
systemctl enable docker
systemctl start docker

# Configure firewall
ufw allow ssh
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable
```

## Step 5: Clone and Configure

```bash
# Navigate to app directory
cd /opt/ai-video-automation

# Clone your repository
git clone https://github.com/YOUR_USERNAME/ai-video-automation.git .

# Create environment file
cp .env.example .env

# Edit with your API keys
nano .env
```

**Required environment variables:**
```env
# Required
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_supabase_anon_key

OPENAI_API_KEY=sk-your-openai-key

# Optional (for video generation)
KIE_API_KEY=your_kie_api_key

# Optional (for YouTube publishing)
YOUTUBE_CLIENT_ID=your_client_id
YOUTUBE_CLIENT_SECRET=your_client_secret
YOUTUBE_REFRESH_TOKEN=your_refresh_token
```

## Step 6: Deploy

```bash
# Start the application
./deploy/deploy.sh start

# Or manually:
docker-compose -f docker-compose.prod.yml up -d --build
```

## Step 7: Access Your Application

Your app is now live at:

- **Web UI**: `http://YOUR_IP.nip.io`
- **API**: `http://YOUR_IP.nip.io/api/`
- **Health Check**: `http://YOUR_IP.nip.io/health`

Example: If your IP is `167.99.123.45`:
- Web: http://167.99.123.45.nip.io
- API: http://167.99.123.45.nip.io/api/

## Management Commands

```bash
# View logs
./deploy/deploy.sh logs

# Check status
./deploy/deploy.sh status

# Stop application
./deploy/deploy.sh stop

# Restart application
./deploy/deploy.sh restart

# Update to latest code
./deploy/deploy.sh update
```

## Adding HTTPS (Optional)

For production with a real domain, you can add Let's Encrypt SSL:

1. Get a domain and point it to your droplet IP

2. Update `nginx/conf.d/default.conf`:
   ```nginx
   server_name yourdomain.com;
   ```

3. Install certbot and get certificate:
   ```bash
   apt install certbot python3-certbot-nginx
   certbot --nginx -d yourdomain.com
   ```

## Troubleshooting

### Check container logs
```bash
docker-compose -f docker-compose.prod.yml logs web
docker-compose -f docker-compose.prod.yml logs app
docker-compose -f docker-compose.prod.yml logs nginx
```

### Restart a specific service
```bash
docker-compose -f docker-compose.prod.yml restart web
```

### Check resource usage
```bash
docker stats
```

### View nginx access logs
```bash
docker-compose -f docker-compose.prod.yml exec nginx cat /var/log/nginx/access.log
```

### Common issues

**Port 80 already in use:**
```bash
sudo lsof -i :80
# Kill the process or stop the service using port 80
```

**Out of memory:**
- Upgrade to a larger droplet (4GB+ recommended for video processing)
- Or reduce memory limits in `docker-compose.prod.yml`

**Connection refused:**
- Check if containers are running: `docker ps`
- Check firewall: `ufw status`
- Check nginx logs: `docker logs ai-video-nginx`

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Digital Ocean Droplet                     │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐    │
│  │                      Nginx                           │    │
│  │                   (Port 80/443)                      │    │
│  └──────────────┬───────────────────┬──────────────────┘    │
│                 │                   │                        │
│        /api/*   │          /*       │                        │
│                 ▼                   ▼                        │
│  ┌──────────────────┐   ┌──────────────────────┐            │
│  │   Python API     │   │     Next.js Web      │            │
│  │   (FastAPI)      │   │     (React SSR)      │            │
│  │   Port 8000      │   │     Port 3000        │            │
│  └──────────────────┘   └──────────────────────┘            │
│                                                              │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │    Supabase     │
                    │   (PostgreSQL)  │
                    └─────────────────┘
```

## Cost Estimate

| Component | Cost/Month |
|-----------|------------|
| Basic Droplet (2GB) | $12 |
| Basic Droplet (4GB) | $24 |
| Domain (nip.io) | Free |
| Supabase (free tier) | Free |
| **Total** | **$12-24** |

## Next Steps

1. Set up Supabase database with the migration files
2. Configure your API keys in `.env`
3. Test the deployment
4. Set up monitoring (optional: add Uptime Robot for free monitoring)
