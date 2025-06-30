#!/bin/bash
# Build script for SnapCircle backend on Render

echo "🔧 Building SnapCircle Backend..."

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo "✅ Backend build completed successfully!"
