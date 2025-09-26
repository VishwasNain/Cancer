#!/bin/bash
set -e  # Exit on error

# Create target directory
TARGET_DIR=".vercel/python/lib/python3.9/site-packages"
mkdir -p "$TARGET_DIR"

# Install Python dependencies with pip's new resolver and no-cache-dir
pip install --upgrade pip
pip install --no-cache-dir --upgrade --target "$TARGET_DIR" -r requirements.txt

# Clean up unnecessary files to reduce deployment size
find "$TARGET_DIR" -type d -name "__pycache__" -exec rm -rf {} + || true
find "$TARGET_DIR" -type d -name "*.dist-info" -exec rm -rf {} + || true
find "$TARGET_DIR" -type d -name "tests" -exec rm -rf {} + || true
find "$TARGET_DIR" -type d -name "test" -exec rm -rf {} + || true
find "$TARGET_DIR" -type d -name "*.pyc" -delete || true
find "$TARGET_DIR" -type f -name "*.so" -not -name "_*" -delete || true

# Remove large unused files
rm -rf "$TARGET_DIR/pandas/tests" || true
rm -rf "$TARGET_DIR/numpy/tests" || true
rm -rf "$TARGET_DIR/scipy/tests" || true
rm -rf "$TARGET_DIR/matplotlib/tests" || true
rm -rf "$TARGET_DIR/sklearn/tests" || true

# Remove documentation and other non-essential files
find "$TARGET_DIR" -type f -name "*.txt" -not -name "LICENSE*" -not -name "METADATA" -delete || true
find "$TARGET_DIR" -type f -name "*.md" -delete || true
find "$TARGET_DIR" -type f -name "*.rst" -delete || true
find "$TARGET_DIR" -type f -name "*.html" -delete || true

# Optimize Python bytecode
python -m compileall -b "$TARGET_DIR"
find "$TARGET_DIR" -name "*.py" -delete

# Print final size
echo "Final deployment size:"
du -sh "$TARGET_DIR"
