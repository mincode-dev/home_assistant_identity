#!/usr/bin/with-contenv bashio

bashio::log.info "Starting IC Identity Manager..."

# Get configuration options (if any)
LOG_LEVEL=$(bashio::config 'log_level' 'info')
bashio::log.info "Log level set to: ${LOG_LEVEL}"

# Start the application
python main.py
