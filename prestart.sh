#!/bin/bash
set -e

echo "=== Running pre-start tasks ==="

# Create uploads directory if it doesn't exist
UPLOAD_DIR="/app/uploads"
if [ ! -d "$UPLOAD_DIR" ]; then
    echo "Creating uploads directory..."
    mkdir -p "$UPLOAD_DIR"
    chmod 755 "$UPLOAD_DIR"
fi

# Create logs directory if it doesn't exist
LOG_DIR="/app/logs"
if [ ! -d "$LOG_DIR" ]; then
    echo "Creating logs directory..."
    mkdir -p "$LOG_DIR"
    touch "$LOG_DIR/app.log"
    chmod -R 755 "$LOG_DIR"
fi

# Install any additional dependencies if needed
# echo "Installing additional dependencies..."
# pip install --no-cache-dir package_name

# Check database connection if using a database
if [ -n "$DATABASE_URL" ]; then
    echo "Checking database connection..."
    # You might want to add a script to check database connectivity
    # python /app/scripts/check_db.py
fi

echo "=== Pre-start tasks completed ==="
