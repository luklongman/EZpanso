#!/bin/bash

# EZpa# Run cleanup script first
echo "🧹 Running project cleanup..."
python scripts/cleanup.py Build Script for macOS
# This script creates a distributable .app bundle and .dmg file

set -e  # Exit on any error

# Detect architecture
ARCH=$(uname -m)
if [ "$ARCH" = "arm64" ]; then
    ARCH_NAME="AppleSilicon"
    SPEC_FILE="EZpanso-arm64.spec"
else
    ARCH_NAME="Intel"
    SPEC_FILE="EZpanso-intel.spec"
fi

echo "🚀 Building EZpanso for macOS ($ARCH_NAME)..."

# Run cleanup script first
echo "🧹 Running project cleanup..."
python3 cleanup.py

# Clean previous builds (redundant after cleanup but ensures clean slate)
echo "🗑️  Ensuring clean build environment..."
rm -rf build/ dist/ *.dmg

# Install dependencies (production only for smaller build)
echo "📦 Installing production dependencies..."
poetry install --only=main

# Build the app using PyInstaller with architecture-specific spec
echo "🔨 Building optimized app bundle for $ARCH_NAME..."
poetry run pyinstaller $SPEC_FILE --clean

# Check if build was successful
if [ ! -d "dist/EZpanso.app" ]; then
    echo "❌ Build failed: EZpanso.app not found in dist/"
    exit 1
fi

echo "✅ App bundle created successfully!"

# Show final build size
echo "📊 Build size analysis:"
echo "   App bundle: $(du -sh dist/EZpanso.app | cut -f1)"
echo "   Executable: $(du -sh dist/EZpanso | cut -f1)"

# For DMG creation, use architecture in filename
DMG_NAME="EZpanso-1.2.0-$ARCH_NAME.dmg"

# Create DMG (optional, requires create-dmg)
if command -v create-dmg &> /dev/null; then
    echo "📦 Creating DMG installer for $ARCH_NAME..."
    
    # Create temporary folder for DMG contents
    mkdir -p dmg_temp
    cp -R dist/EZpanso.app dmg_temp/
    
    # Create the DMG
    create-dmg \
        --volname "EZpanso Installer" \
        --volicon "icon.iconset/icon_512x512.png" \
        --window-pos 200 120 \
        --window-size 800 450 \
        --icon-size 100 \
        --icon "EZpanso.app" 200 190 \
        --hide-extension "EZpanso.app" \
        --app-drop-link 600 185 \
        --format UDZO \
        "$DMG_NAME" \
        "dmg_temp/"
    
    # Clean up
    rm -rf dmg_temp/
    
    echo "✅ DMG created: $DMG_NAME"
else
    echo "⚠️  create-dmg not found. Skipping DMG creation."
    echo "   Install with: brew install create-dmg"
fi

echo "🎉 Build complete!"
echo "📁 App location: dist/EZpanso.app"

# Test the app
echo "🧪 Testing the app..."
open dist/EZpanso.app

echo "✨ EZpanso is ready for distribution!"
