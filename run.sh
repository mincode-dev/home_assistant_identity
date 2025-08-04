#!/bin/bash
set -e

echo "Starting ICP Identity Manager addon..."

# Ensure data directory exists
mkdir -p /data

# Start the Python application
cd /app
python main.py 