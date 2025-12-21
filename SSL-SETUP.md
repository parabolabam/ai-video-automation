# SSL Certificate Management - Fully Containerized

This project uses a **fully containerized SSL certificate management system** with **zero host dependencies**. All certificates are stored in Docker volumes and managed by a certbot container.

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   Docker Volumes                         │
│  ┌──────────────────────┐  ┌──────────────────────┐    │
│  │ letsencrypt_certs    │  │   certbot_www        │    │
│  │ (SSL certificates)   │  │   (ACME challenges)  │    │
│  └──────────────────────┘  └──────────────────────┘    │
│           ↑  ↑                      ↑                   │
│           │  │                      │                   │
│  ┌────────┘  └────────┐    ┌───────┘                   │
│  │                     │    │                           │
│  │  nginx (read-only)  │    │  certbot (read/write)     │
│  │                     │    │                           │
│  └─────────────────────┘    └───────────────────────────┘
└─────────────────────────────────────────────────────────┘
```

## Components

### 1. Certbot Container
- **Image**: `certbot/certbot:latest`
- **Purpose**: Automatically renews SSL certificates every 12 hours
- **Volumes**:
  - `letsencrypt_certs`: Stores SSL certificates
  - `certbot_www`: Stores ACME challenge files for domain validation
- **Process**: Runs `certbot renew` in a loop with 12-hour intervals

### 2. Nginx Container
- **Volumes** (read-only):
  - `letsencrypt_certs`: Reads SSL certificates
  - `certbot_www`: Serves ACME challenge files for domain validation
- **SSL Detection**: Automatically detects if certificates exist and switches between HTTP-only and HTTPS configurations

## Initial Setup (One-Time)

When deploying to a **new server** or **new domain**, you need to generate certificates once:

### Option 1: Using the init script (Recommended)

```bash
# On the droplet
cd /opt/ai-video-automation
./scripts/init-letsencrypt.sh
```

This script will:
1. Check if certificates already exist
2. If not, temporarily stop nginx
3. Use certbot in standalone mode to generate certificates
4. Store certificates in Docker volumes
5. Display success message

### Option 2: Manual initialization

```bash
# Stop nginx to free port 80
docker stop ai-video-nginx

# Generate certificates
docker run --rm \
  -p 80:80 \
  -p 443:443 \
  -v ai-video-automation_letsencrypt_certs:/etc/letsencrypt \
  -v ai-video-automation_certbot_www:/var/www/certbot \
  certbot/certbot:latest \
  certonly \
  --standalone \
  -d vingine.duckdns.org \
  --email your-email@example.com \
  --agree-tos \
  --non-interactive

# Start all services
docker-compose -f docker-compose.prod.yml up -d
```

## Automatic Renewal

Once certificates are generated, the certbot container handles renewals automatically:

1. **Certbot container** runs in the background
2. Every **12 hours**, it checks if certificates need renewal
3. Let's Encrypt certificates are valid for 90 days
4. Certbot renews them when they have **30 days or less** remaining
5. **No manual intervention required**

## How It Works

### HTTP-01 Challenge (Webroot Method)

```
┌─────────┐                    ┌──────────────┐                ┌────────────┐
│ Let's   │                    │    Nginx     │                │  Certbot   │
│ Encrypt │                    │  Container   │                │ Container  │
└─────────┘                    └──────────────┘                └────────────┘
     │                                │                               │
     │  1. Challenge Request          │                               │
     ├────────────────────────────────►                               │
     │                                │                               │
     │  2. Serve challenge file       │                               │
     │    from /var/www/certbot       │                               │
     ◄────────────────────────────────┤                               │
     │                                │                               │
     │  3. Validation Success         │                               │
     │  4. Issue Certificate          │ ◄─────────────────────────────┤
     │                                │                               │
     │                                │  5. Certbot renew writes      │
     │                                │     to letsencrypt_certs      │
     │                                │ ◄─────────────────────────────┤
```

## Advantages

### ✅ Zero Host Dependencies
- No need to install certbot on the host system
- No host filesystem pollution
- Portable across any server with Docker

### ✅ Automatic Renewals
- Runs in background 24/7
- Checks every 12 hours
- Renews 30 days before expiration
- No cron jobs needed

### ✅ Easy Backup & Restore
```bash
# Backup certificates
docker run --rm \
  -v ai-video-automation_letsencrypt_certs:/certs \
  -v $(pwd):/backup \
  alpine tar czf /backup/certificates-backup.tar.gz -C /certs .

# Restore certificates
docker run --rm \
  -v ai-video-automation_letsencrypt_certs:/certs \
  -v $(pwd):/backup \
  alpine tar xzf /backup/certificates-backup.tar.gz -C /certs
```

### ✅ Environment Isolation
- Certificates stored in Docker volumes
- Isolated from host filesystem
- Consistent across environments

## Troubleshooting

### Check certificate status
```bash
docker run --rm \
  -v ai-video-automation_letsencrypt_certs:/etc/letsencrypt \
  certbot/certbot:latest \
  certificates
```

### Manual renewal (force)
```bash
docker exec ai-video-certbot certbot renew --force-renewal
```

### View certbot logs
```bash
docker logs ai-video-certbot
```

### Check nginx SSL detection
```bash
docker logs ai-video-nginx | grep SSL
```

### Verify HTTPS is working
```bash
curl -I https://vingine.duckdns.org
```

## Migration from Host Certificates

If you have existing certificates on the host system:

```bash
# Migrate certificates to Docker volume
docker run --rm \
  -v /etc/letsencrypt:/source:ro \
  -v ai-video-automation_letsencrypt_certs:/dest \
  alpine sh -c "cp -a /source/. /dest/"
```

## Rate Limits

Let's Encrypt has rate limits:
- **50 certificates** per registered domain per week
- **5 duplicate certificates** per week
- **300 new orders** per account per 3 hours

For testing, use staging mode:
```bash
# In init-letsencrypt.sh, set:
STAGING=1
```

Staging certificates won't be trusted by browsers but let you test the flow without hitting rate limits.

## Security Notes

- Nginx mounts certificates as **read-only** (`:ro`)
- Only certbot container has **write access** to certificates
- Private keys are stored in Docker volumes with proper permissions
- No sensitive data on host filesystem

## Support

For issues:
1. Check container logs: `docker logs ai-video-certbot`
2. Verify volume exists: `docker volume ls | grep letsencrypt`
3. Check nginx configuration: `docker exec ai-video-nginx nginx -t`
4. Verify domain DNS: `nslookup vingine.duckdns.org`

## References

- [Let's Encrypt Documentation](https://letsencrypt.org/docs/)
- [Certbot Documentation](https://certbot.eff.org/docs/)
- [Docker Volumes](https://docs.docker.com/storage/volumes/)
