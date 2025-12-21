FROM nginx:1.29.4-alpine

# Install tools for dynamic configuration
RUN apk add --no-cache gettext

# Copy nginx configuration template
COPY nginx.conf.template /etc/nginx/nginx.conf.template
COPY vingine.conf.template /etc/nginx/conf.d/vingine.conf.template

# Copy entrypoint script
COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

# SSL certificates directory
RUN mkdir -p /etc/letsencrypt/live/vingine.duckdns.org

EXPOSE 80 443

ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["nginx", "-g", "daemon off;"]
