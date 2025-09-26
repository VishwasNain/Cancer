#!/bin/bash
set -e  # Exit on error

echo "Starting Vercel build process..."

# Create target directory
TARGET_DIR=".vercel/python/lib/python3.9/site-packages"
mkdir -p "$TARGET_DIR"

# Install Python dependencies with pip's new resolver and no-cache-dir
echo "Installing Python dependencies..."
python -m pip install --upgrade pip
python -m pip install --no-cache-dir --upgrade --target "$TARGET_DIR" -r requirements.txt

# Clean up unnecessary files to reduce deployment size
echo "Cleaning up unnecessary files..."

# Remove test directories
find "$TARGET_DIR" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find "$TARGET_DIR" -type d -name "*.dist-info" -exec rm -rf {} + 2>/dev/null || true
find "$TARGET_DIR" -type d -name "tests" -exec rm -rf {} + 2>/dev/null || true
find "$TARGET_DIR" -type d -name "test" -exec rm -rf {} + 2>/dev/null || true

# Remove compiled Python files
find "$TARGET_DIR" -name "*.pyc" -delete 2>/dev/null || true
find "$TARGET_DIR" -name "*.pyo" -delete 2>/dev/null || true
find "$TARGET_DIR" -name "*.pyd" -delete 2>/dev/null || true

# Remove large test directories from common packages
for pkg in pandas numpy scipy matplotlib sklearn torch tensorflow; do
    find "$TARGET_DIR" -type d -path "*/$pkg/test*" -exec rm -rf {} + 2>/dev/null || true
done

# Remove documentation and other non-essential files
find "$TARGET_DIR" -type f -name "*.txt" -not -name "LICENSE*" -not -name "METADATA" -delete 2>/dev/null || true
find "$TARGET_DIR" -type f -name "*.md" -delete 2>/dev/null || true
find "$TARGET_DIR" -type f -name "*.rst" -delete 2>/dev/null || true
find "$TARGET_DIR" -type f -name "*.html" -delete 2>/dev/null || true
find "$TARGET_DIR" -type f -name "*.jpg" -delete 2>/dev/null || true
find "$TARGET_DIR" -type f -name "*.png" -delete 2>/dev/null || true
find "$TARGET_DIR" -type f -name "*.gif" -delete 2>/dev/null || true

# Optimize Python bytecode
echo "Optimizing bytecode..."
python -m compileall -b "$TARGET_DIR" 2>/dev/null || true
find "$TARGET_DIR" -name "*.py" -not -name "__init__.py" -delete 2>/dev/null || true

# Create __init__.py files in all directories to make them proper Python packages
find "$TARGET_DIR" -type d -not -name "__pycache__" -exec touch {}/__init__.py \; 2>/dev/null || true

# Print final size
echo "Final deployment size:"
du -sh "$TARGET_DIR" || true

echo "Build process completed successfully!"
