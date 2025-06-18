#!/bin/bash

# EZpanso Separate Architecture Build Script for macOS
# Implements the recommended approach for building separate Apple Silicon and Intel apps
# with proper virtual environments, and notarization support

set -e  # Exit on any error

# Configuration
VERSION="1.2.1"
APP_NAME="EZpanso"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

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
    "clean")
        cleanup_all
        exit 0
        ;;
    *)
        log_error "Invalid target: $TARGET_ARCH"
        echo "Usage: $0 [arm64|apple-silicon|x86_64|intel|all|both|clean]"
        exit 1
        ;;
esac

log_info "Building $APP_NAME for macOS..."
log_info "Version: $VERSION"
log_info "Targets: ${BUILD_TARGETS[*]}"

# Create build directory structure
setup_build_structure() {
    log_info "Setting up build directory structure..."
    
    mkdir -p builds/{arm64,x86_64}/{dist,dmg}
    mkdir -p final_releases
    
    log_success "Build structure created"
}

# Cleanup function for all builds
cleanup_all() {
    log_info "Cleaning all build artifacts..."
    
    rm -rf builds/
    rm -rf final_releases/*.dmg
    rm -rf *.zip
    rm -rf build/ dist/
    
    # Remove Python cache files
    find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
    find . -name "*.pyc" -delete 2>/dev/null || true
    
    log_success "All build artifacts cleaned"
}

# Install dependencies for specific architecture
install_dependencies() {
    local target_arch="$1"
    
    log_info "Installing dependencies for $target_arch using Poetry..."
    
    if [ "$target_arch" = "x86_64" ]; then
        # For Intel, use Rosetta with Poetry
        log_info "Installing under Rosetta for Intel compatibility..."
        arch -x86_64 poetry install --only=main
    else
        # For Apple Silicon, use Poetry normally
        poetry install --only=main
    fi
    
    # Verify installation with Poetry
    if [ "$target_arch" = "x86_64" ]; then
        arch -x86_64 poetry run python -c "import PyQt6.QtCore; print(f'PyQt6 version: {PyQt6.QtCore.PYQT_VERSION_STR}')"
        arch -x86_64 poetry run python -c "import yaml; print(f'PyYAML available')"
        arch -x86_64 poetry run python -c "import ruamel.yaml; print(f'ruamel.yaml available')" || log_warning "ruamel.yaml not available (fallback to PyYAML)"
    else
        poetry run python -c "import PyQt6.QtCore; print(f'PyQt6 version: {PyQt6.QtCore.PYQT_VERSION_STR}')"
        poetry run python -c "import yaml; print(f'PyYAML available')"
        poetry run python -c "import ruamel.yaml; print(f'ruamel.yaml available')" || log_warning "ruamel.yaml not available (fallback to PyYAML)"
    fi
    
    log_success "Dependencies installed for $target_arch"
}

# Build application for specific architecture
build_app() {
    local target_arch="$1"
    local build_dir="builds/${target_arch}"
    
    log_info "Building application for $target_arch..."
    
    # Set spec file based on architecture
    if [ "$target_arch" = "arm64" ]; then
        local spec_file="EZpanso-arm64.spec"
        local arch_name="AppleSilicon"
    else
        local spec_file="EZpanso-intel.spec"
        local arch_name="Intel"
    fi
    
    # Clean previous build
    rm -rf "$build_dir/dist" "$build_dir/build"
    
    # Build with PyInstaller using Poetry
    if [ "$target_arch" = "x86_64" ]; then
        # Use Rosetta for Intel build
        arch -x86_64 poetry run pyinstaller "$spec_file" \
            --clean \
            --distpath "$build_dir/dist" \
            --workpath "$build_dir/build"
    else
        # Native Apple Silicon build
        poetry run pyinstaller "$spec_file" \
            --clean \
            --distpath "$build_dir/dist" \
            --workpath "$build_dir/build"
    fi
    
    if [ ! -d "$build_dir/dist/${APP_NAME}.app" ]; then
        log_error "Build failed: ${APP_NAME}.app not found in $build_dir/dist/"
        exit 1
    fi
    
    # Rename the app to include architecture
    mv "$build_dir/dist/${APP_NAME}.app" "$build_dir/dist/${APP_NAME}-${arch_name}.app"
    
    log_success "App bundle created: ${APP_NAME}-${arch_name}.app"
    log_info "Size: $(du -sh "$build_dir/dist/${APP_NAME}-${arch_name}.app" | cut -f1)"
}

# Create DMG for specific architecture
create_dmg() {
    local target_arch="$1"
    local build_dir="builds/${target_arch}"
    
    if [ "$target_arch" = "arm64" ]; then
        local arch_name="AppleSilicon"
        local vol_name="$APP_NAME (Apple Silicon)"
    else
        local arch_name="Intel"
        local vol_name="$APP_NAME (Intel)"
    fi
    
    local app_path="$build_dir/dist/${APP_NAME}-${arch_name}.app"
    local dmg_path="final_releases/${APP_NAME}-${VERSION}-${arch_name}.dmg"
    local temp_dmg_dir="$build_dir/dmg"
    
    if ! command -v create-dmg &> /dev/null; then
        log_warning "create-dmg not found. Install with: brew install create-dmg"
        log_info "Creating simple DMG with hdiutil..."
        
        # Fallback to hdiutil
        rm -rf "$temp_dmg_dir"
        mkdir -p "$temp_dmg_dir"
        cp -R "$app_path" "$temp_dmg_dir/"
        
        hdiutil create -volname "$vol_name" -srcfolder "$temp_dmg_dir" -ov -format UDZO "$dmg_path"
        
    else
        log_info "Creating DMG for $arch_name with create-dmg..."
        
        # Prepare temporary folder
        rm -rf "$temp_dmg_dir"
        mkdir -p "$temp_dmg_dir"
        cp -R "$app_path" "$temp_dmg_dir/"
        
        # Create DMG with create-dmg
        create-dmg \
            --volname "$vol_name" \
            --volicon "icon.iconset/icon_512x512.png" \
            --window-pos 200 120 \
            --window-size 800 450 \
            --icon-size 100 \
            --icon "${APP_NAME}-${arch_name}.app" 200 190 \
            --hide-extension "${APP_NAME}-${arch_name}.app" \
            --app-drop-link 600 185 \
            --format UDZO \
            "$dmg_path" \
            "$temp_dmg_dir/"
    fi
    
    rm -rf "$temp_dmg_dir"
    
    log_success "DMG created: $(basename "$dmg_path")"
    log_info "Size: $(du -sh "$dmg_path" | cut -f1)"
}

# Build for specific architecture (main function)
build_for_arch() {
    local target_arch="$1"
    
    if [ "$target_arch" = "arm64" ]; then
        local arch_name="Apple Silicon"
    else
        local arch_name="Intel"
    fi
    
    log_info "Starting $arch_name build process..."
    
    # Install dependencies
    install_dependencies "$target_arch"
    
    # Build application
    build_app "$target_arch"
    
    # Create DMG
    create_dmg "$target_arch"
    
    log_success "$arch_name build completed successfully!"
}

# Main execution
main() {
    log_info "Starting EZpanso separate architecture build process..."
    
    # Setup build structure
    setup_build_structure
    
    # Build for each target architecture
    for target_arch in "${BUILD_TARGETS[@]}"; do
        build_for_arch "$target_arch"
        echo ""
    done
    
    # Summary
    log_success "All builds completed!"
    echo ""
    log_info "Final releases:"
    ls -la final_releases/*.dmg 2>/dev/null || log_warning "No DMG files found in final_releases/"
    
    echo ""
    log_info "Build artifacts structure:"
    tree builds/ -L 3 2>/dev/null || find builds/ -type d 2>/dev/null || log_warning "No build artifacts found"
    
    echo ""
    log_success "EZpanso separate architecture builds ready for distribution!"
}

# Execute main function
main
