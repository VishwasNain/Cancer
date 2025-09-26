#!/bin/bash
set -e  # Exit on error

# Install Python dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Install additional dependencies if needed
# pip install gunicorn

# Create necessary directories
mkdir -p static/uploads

# Set permissions
chmod +x vercel_build.sh

# Print Python version
python --version

# Print installed packages
pip list
