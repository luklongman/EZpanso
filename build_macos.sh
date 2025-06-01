#!/bin/bash

# EZpanso Build Script for macOS
# This script creates a distributable .app bundle and .dmg file

set -e  # Exit on any error

echo "🚀 Building EZpanso for macOS..."

# Clean previous builds
echo "🧹 Cleaning previous builds..."
rm -rf build/ dist/ *.dmg

# Install dependencies
echo "📦 Installing dependencies..."
poetry install

# Build the app using PyInstaller
echo "🔨 Building app bundle..."
poetry run pyinstaller EZpanso.spec --clean

# Check if build was successful
if [ ! -d "dist/EZpanso.app" ]; then
    echo "❌ Build failed: EZpanso.app not found in dist/"
    exit 1
fi

echo "✅ App bundle created successfully!"

# Create DMG (optional, requires create-dmg)
if command -v create-dmg &> /dev/null; then
    echo "📦 Creating DMG installer..."
    
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
        "EZpanso-1.0.0.dmg" \
        "dmg_temp/"
    
    # Clean up
    rm -rf dmg_temp/
    
    echo "✅ DMG created: EZpanso-1.0.0.dmg"
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
