# syntax=docker/dockerfile:1
FROM nginx:alpine AS web

ARG ASSET_VERSION=dev
ENV ASSET_VERSION=${ASSET_VERSION}

# Install python3 for asset injection
RUN apk add --no-cache python3

# Workdir for app
WORKDIR /app

# Copy frontend pages and static assets
COPY ../frontend/pages /app/pages
COPY ../frontend/static /app/static

# Copy injector script
COPY ../scripts/inject_assets.py /app/scripts/inject_assets.py

# Run asset injection to replace placeholders
RUN python3 /app/scripts/inject_assets.py

# Copy to nginx html directory
RUN mkdir -p /usr/share/nginx/html/pages /usr/share/nginx/html/static \
    && cp -r /app/pages /usr/share/nginx/html/ \
    && cp -r /app/static /usr/share/nginx/html/

# Provide custom nginx config with /health and extensionless pages support
COPY ./docker/nginx.conf /etc/nginx/conf.d/default.conf

# Expose default nginx port
EXPOSE 80

# Default nginx configuration serves /usr/share/nginx/html
CMD ["nginx", "-g", "daemon off;"]
