#!/bin/bash
# Install Python dependencies
pip install --upgrade pip
pip install -r requirements.txt --target .vercel/python/lib/python3.9/site-packages

# Clean up unnecessary files
find .vercel -type d -name "__pycache__" -exec rm -rf {} +
find .vercel -type d -name "*.dist-info" -exec rm -rf {} +
find .vercel -type d -name "tests" -exec rm -rf {} +
find .vercel -type d -name "test" -exec rm -rf {} +
