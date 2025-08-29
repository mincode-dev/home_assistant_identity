# ic_identity/Dockerfile
ARG BUILD_FROM
FROM ${BUILD_FROM}

ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
RUN apk add --no-cache curl libffi-dev openssl-dev build-base

# App working dir (your code will live under here)
WORKDIR /usr/src/app

# Copy ONLY what you need, to the right places:
COPY home_identity/ /usr/src/app/home_identity/
COPY run.sh /run.sh

# Install Python deps from the correct path
RUN pip install --no-cache-dir --upgrade pip \
 && pip install --no-cache-dir -r /usr/src/app/home_identity/requirements.txt

# Make the entrypoint executable
RUN chmod a+x /run.sh

EXPOSE 8099

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD curl -fsS http://127.0.0.1:8099/api/v1/health || exit 1

# s6-overlay will exec this
CMD ["/run.sh"]
