#!/bin/bash

# ICP Identity Addon Runner Script for Docker
echo "🚀 Starting ICP Identity Addon..."

# Set Python path for Docker container
export PYTHONPATH="/app:$PYTHONPATH"

# Start the application
python app/main.py