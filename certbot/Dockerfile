FROM certbot/certbot:latest

# Install any additional tools if needed
RUN apk add --no-cache bash

# Copy renewal script
COPY renew-certs.sh /renew-certs.sh
RUN chmod +x /renew-certs.sh

# Default command runs certbot renew
CMD ["renew", "--non-interactive"]
