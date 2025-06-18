#!/bin/bash

# EZpanso Multi-Architecture Build Script for macOS
# This script creates separate .app bundles for Intel and Apple Silicon

set -e  # Exit on any error

echo "🚀 Building EZpanso for macOS (Multi-Architecture Build)..."

# Function to create DMG
create_dmg_for_arch() {
    local arch=$1
    local app_name=$2
    local dmg_name=$3
    
    if command -v create-dmg &> /dev/null; then
        echo "📦 Creating DMG installer for $arch..."
        
        # Create temporary folder for DMG contents
        mkdir -p "dmg_temp_$arch"
        cp -R "dist/$app_name" "dmg_temp_$arch/EZpanso.app"
        
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
            "$dmg_name" \
            "dmg_temp_$arch/"
        
        # Clean up
        rm -rf "dmg_temp_$arch/"
        
        echo "✅ DMG created: $dmg_name"
    else
        echo "⚠️  create-dmg not found. Skipping DMG creation for $arch."
        echo "   Install with: brew install create-dmg"
    fi
}

# Run cleanup script first
echo "🧹 Running project cleanup..."
python3 scripts/cleanup.py

# Clean previous builds
echo "🗑️  Ensuring clean build environment..."
rm -rf build/ dist/ *.dmg

# Install dependencies (production only for smaller build)
echo "📦 Installing production dependencies..."
poetry install --only=main

# Build Intel version
echo "🔨 Building Intel (x86_64) app bundle..."
poetry run pyinstaller EZpanso-intel.spec --clean

# Check if Intel build was successful and rename it
if [ ! -d "dist/EZpanso.app" ]; then
    echo "❌ Intel build failed: EZpanso.app not found in dist/"
    exit 1
fi

# Rename Intel app for distinction
mv "dist/EZpanso.app" "dist/EZpanso-Intel.app"
echo "✅ Intel app bundle created successfully!"

# Build Apple Silicon version
echo "🔨 Building Apple Silicon (arm64) app bundle..."
poetry run pyinstaller EZpanso-arm64.spec --clean

# Check if Apple Silicon build was successful and rename it
if [ ! -d "dist/EZpanso.app" ]; then
    echo "❌ Apple Silicon build failed: EZpanso.app not found in dist/"
    exit 1
fi

# Rename Apple Silicon app for distinction
mv "dist/EZpanso.app" "dist/EZpanso-AppleSilicon.app"

echo "✅ Apple Silicon app bundle created successfully!"

# Show final build sizes
echo "📊 Build size analysis:"
echo "   Intel app bundle: $(du -sh dist/EZpanso-Intel.app | cut -f1)"
echo "   Apple Silicon app bundle: $(du -sh dist/EZpanso-AppleSilicon.app | cut -f1)"

# Create DMGs for both architectures
create_dmg_for_arch "Intel" "EZpanso-Intel.app" "EZpanso-1.2.1-Intel.dmg"
create_dmg_for_arch "Apple Silicon" "EZpanso-AppleSilicon.app" "EZpanso-1.2.1-AppleSilicon.dmg"

echo "🎉 Multi-architecture build complete!"
echo "📁 App bundles (both named EZpanso.app but different architectures):"
echo "   Intel: dist/EZpanso-Intel.app"
echo "   Apple Silicon: dist/EZpanso-AppleSilicon.app"
echo "📦 DMG installers:"
echo "   Intel: EZpanso-1.2.1-Intel.dmg"
echo "   Apple Silicon: EZpanso-1.2.1-AppleSilicon.dmg"

# Test the appropriate app based on current architecture
ARCH=$(uname -m)
if [ "$ARCH" = "arm64" ]; then
    echo "🧪 Testing the Apple Silicon app..."
    open dist/EZpanso-AppleSilicon.app
else
    echo "🧪 Testing the Intel app..."
    open dist/EZpanso-Intel.app
fi

echo "✨ EZpanso builds are ready for distribution!"
echo "🔄 You now have separate optimized builds for each architecture."
