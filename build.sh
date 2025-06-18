#!/bin/bash

# EZpanso Build Script for macOS
# Builds for Apple Silicon (native) and Intel (cross-compiled) architectures

set -e  # Exit on any error

# Configuration
VERSION="1.2.1"
APP_NAME="EZpanso"

# Build target selection
TARGET_ARCH="${1:-all}"  # Default to building all architectures

case "$TARGET_ARCH" in
    "arm64"|"apple-silicon")
        BUILD_TARGETS=("arm64")
        ;;
    "x86_64"|"intel")
        BUILD_TARGETS=("x86_64")
        ;;
    "all"|"both")
        BUILD_TARGETS=("arm64" "x86_64")
        ;;
    *)
        echo "❌ Invalid target: $TARGET_ARCH"
        echo "Usage: $0 [arm64|apple-silicon|x86_64|intel|all|both]"
        exit 1
        ;;
esac

DMG_NAME="${APP_NAME}-${VERSION}-${ARCH_NAME}.dmg"

echo "🚀 Building $APP_NAME for macOS..."
echo "📋 Version: $VERSION"
echo "🎯 Targets: ${BUILD_TARGETS[*]}"

# Build function for specific architecture
build_for_arch() {
    local target_arch="$1"
    
    case "$target_arch" in
        "arm64")
            ARCH_NAME="AppleSilicon"
            SPEC_FILE="EZpanso-arm64.spec"
            FEATURES_MSG="Full YAML comment preservation supported"
            ;;
        "x86_64")
            ARCH_NAME="Intel"
            SPEC_FILE="EZpanso-intel.spec"
            FEATURES_MSG="Basic YAML support (no comment preservation)"
            ;;
    esac
    
    local dmg_name="${APP_NAME}-${VERSION}-${ARCH_NAME}.dmg"
    
    echo ""
    echo "🔨 Building for $target_arch ($ARCH_NAME)..."
    echo "⚙️  Features: $FEATURES_MSG"
    
    # Clean build environment
    cleanup_build
    
    # Install dependencies
    install_dependencies "$target_arch"
    
    # Build app
    build_app "$target_arch"
    
    # Create DMG
    create_dmg "$target_arch" "$dmg_name"
    
    echo "✅ $ARCH_NAME build complete: $dmg_name"
}

# Cleanup function
cleanup_build() {
    echo "🧹 Cleaning build environment..."
    rm -rf build/ dist/ ${APP_NAME}-${VERSION}-*.dmg
    
    if [ -f "scripts/cleanup.py" ]; then
        python3 scripts/cleanup.py
    else
        rm -rf __pycache__/ **/__pycache__/ *.pyc **/*.pyc
    fi
}

# Install dependencies function
install_dependencies() {
    local target_arch="$1"
    echo "📦 Installing dependencies for $target_arch..."
    
    if [ "$target_arch" = "x86_64" ]; then
        # Special handling for Intel cross-compilation
        echo "   Configuring for Intel cross-compilation..."
        pip uninstall -y ruamel.yaml ruamel.yaml.clib 2>/dev/null || true
        pip install --no-binary=PyYAML PyYAML==6.0.1 --force-reinstall --no-deps
        pip install PyQt6==6.6.0 --force-reinstall --no-deps
    else
        # Standard installation for Apple Silicon
        poetry install --only=main
    fi
}

# Build app function
build_app() {
    local target_arch="$1"
    echo "🔨 Building app bundle for $target_arch..."
    
    # Set spec file based on architecture
    if [ "$target_arch" = "arm64" ]; then
        local spec_file="EZpanso-arm64.spec"
    else
        local spec_file="EZpanso-intel.spec"
    fi
    
    poetry run pyinstaller "$spec_file" --clean
    
    if [ ! -d "dist/${APP_NAME}.app" ]; then
        echo "❌ Build failed: ${APP_NAME}.app not found in dist/"
        exit 1
    fi
    
    echo "✅ App bundle created successfully!"
    echo "📊 Size: $(du -sh dist/${APP_NAME}.app | cut -f1)"
}

# Create DMG function
create_dmg() {
    local target_arch="$1"
    local dmg_name="$2"
    
    if ! command -v create-dmg &> /dev/null; then
        echo "⚠️  create-dmg not found. Skipping DMG creation."
        echo "   Install with: brew install create-dmg"
        return
    fi
    
    echo "📦 Creating DMG installer for $target_arch..."
    
    # Prepare for distribution
    xattr -cr "dist/${APP_NAME}.app" 2>/dev/null || true
    
    # Create temporary folder
    mkdir -p dmg_temp
    cp -R "dist/${APP_NAME}.app" dmg_temp/
    
    # Set volume name based on architecture
    if [ "$target_arch" = "arm64" ]; then
        local vol_name="$APP_NAME (Apple Silicon)"
    else
        local vol_name="$APP_NAME (Intel)"
    fi
    
    # Create DMG
    create-dmg \
        --volname "$vol_name" \
        --volicon "icon.iconset/icon_512x512.png" \
        --window-pos 200 120 \
        --window-size 800 450 \
        --icon-size 100 \
        --icon "${APP_NAME}.app" 200 190 \
        --hide-extension "${APP_NAME}.app" \
        --app-drop-link 600 185 \
        --format UDZO \
        "$dmg_name" \
        "dmg_temp/"
    
    rm -rf dmg_temp/
    echo "✅ DMG created: $dmg_name"
}

# Cleanup function
cleanup_build() {
    echo "� Cleaning build environment..."
    rm -rf build/ dist/ ${APP_NAME}-${VERSION}-*.dmg
    
    if [ -f "scripts/cleanup.py" ]; then
        python3 scripts/cleanup.py
    else
        rm -rf __pycache__/ **/__pycache__/ *.pyc **/*.pyc
    fi
}

# Main execution
main() {
    echo "🚀 Starting EZpanso build process..."
    
    for target_arch in "${BUILD_TARGETS[@]}"; do
        build_for_arch "$target_arch"
    done
    
    echo ""
    echo "🎉 All builds complete!"
    echo "📁 App bundles and DMG files created:"
    ls -la ${APP_NAME}-${VERSION}-*.dmg 2>/dev/null || echo "   No DMG files found"
    
    # Test the last built app
    if [ -d "dist/${APP_NAME}.app" ]; then
        echo ""
        echo "🧪 Testing the app..."
        open "dist/${APP_NAME}.app"
    fi
    
    echo ""
    echo "🚀 EZpanso builds ready for distribution!"
}

# Allow running specific functions for debugging
if [ $# -eq 0 ]; then
    main
else
    case "$1" in
        "clean")     cleanup_build ;;
        "arm64"|"apple-silicon") 
                     BUILD_TARGETS=("arm64")
                     main ;;
        "x86_64"|"intel") 
                     BUILD_TARGETS=("x86_64")
                     main ;;
        "all"|"both") 
                     BUILD_TARGETS=("arm64" "x86_64")
                     main ;;
        *)           echo "Usage: $0 [clean|arm64|apple-silicon|x86_64|intel|all|both]" ;;
    esac
fi
