ARG BUILD_FROM=ghcr.io/home-assistant/amd64-base-python:3.11-alpine3.18
FROM $BUILD_FROM

# Install additional system dependencies if needed
RUN apk add --no-cache \
    curl \
    build-base \
    libffi-dev \
    openssl-dev \
    && rm -rf /var/cache/apk/*

# Set working directory
WORKDIR /

# Copy application files
COPY . .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Make run script executable
RUN chmod a+x /run.sh

# Expose port (optional, mainly for documentation)
EXPOSE 8099

# Health check using HA add-on standards
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD curl -fsS http://127.0.0.1:8099/api/v1/health || exit 1

# Start via run.sh script (HA add-on standard)
CMD ["/run.sh"]