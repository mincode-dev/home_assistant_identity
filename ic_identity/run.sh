#!/usr/bin/with-contenv bashio
set -euo pipefail

bashio::log.info "Starting IC Identity Manager..."

PORT="$(bashio::config 'port' '8099')"
LOG_LEVEL="$(bashio::config 'log_level' 'info')"
export LOG_LEVEL

# No Supervisor curl here.
exec python3 -m home_identity.main
