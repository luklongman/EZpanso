#!/bin/bash

# EZpanso Code Signing Script for macOS Distribution
# This script signs the app bundle to prevent macOS Gatekeeper issues

set -e

# Configuration
APP_PATH="$1"
SIGNING_IDENTITY="${CODESIGN_IDENTITY:-Developer ID Application}"
ENABLE_HARDENED_RUNTIME="${ENABLE_HARDENED_RUNTIME:-true}"
ENTITLEMENTS_FILE="${ENTITLEMENTS_FILE:-scripts/entitlements.plist}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔐 EZpanso Code Signing Script${NC}"
echo "================================================="

# Validate input
if [ -z "$APP_PATH" ]; then
    echo -e "${RED}❌ Error: App path not provided${NC}"
    echo "Usage: $0 <path-to-app-bundle> [signing-identity]"
    echo "Example: $0 dist/EZpanso.app"
    exit 1
fi

if [ ! -d "$APP_PATH" ]; then
    echo -e "${RED}❌ Error: App bundle not found at: $APP_PATH${NC}"
    exit 1
fi

# Override signing identity if provided as second argument
if [ -n "$2" ]; then
    SIGNING_IDENTITY="$2"
fi

echo -e "${BLUE}App Path:${NC} $APP_PATH"
echo -e "${BLUE}Signing Identity:${NC} $SIGNING_IDENTITY"

# Check if we're in ad-hoc signing mode (for development)
if [ "$SIGNING_IDENTITY" = "-" ] || [ "$SIGNING_IDENTITY" = "adhoc" ]; then
    echo -e "${YELLOW}⚠️  Using ad-hoc signing (development only)${NC}"
    SIGNING_IDENTITY="-"
    CODESIGN_FLAGS="--force --deep"
else
    echo -e "${GREEN}✅ Using developer certificate signing${NC}"
    CODESIGN_FLAGS="--force --deep --options runtime"
    
    # Add entitlements if file exists
    if [ -f "$ENTITLEMENTS_FILE" ]; then
        CODESIGN_FLAGS="$CODESIGN_FLAGS --entitlements $ENTITLEMENTS_FILE"
        echo -e "${BLUE}Entitlements:${NC} $ENTITLEMENTS_FILE"
    fi
fi

# Function to sign a single file or bundle
sign_item() {
    local item="$1"
    local item_name=$(basename "$item")
    
    echo -e "${BLUE}🔏 Signing:${NC} $item_name"
    
    if codesign $CODESIGN_FLAGS --sign "$SIGNING_IDENTITY" "$item"; then
        echo -e "${GREEN}  ✅ Signed successfully${NC}"
    else
        echo -e "${RED}  ❌ Failed to sign${NC}"
        return 1
    fi
}

# Main signing process
echo -e "\n${BLUE}📝 Starting code signing process...${NC}"

# Sign all executables and frameworks inside the app bundle first
echo -e "\n${BLUE}🔍 Finding and signing internal components...${NC}"

# Find and sign all executable files, frameworks, and dylibs
find "$APP_PATH" -type f \( -name "*.dylib" -o -name "*.so" -o -perm +111 \) -exec file {} \; | \
    grep -E "(Mach-O|dynamically linked)" | \
    cut -d: -f1 | \
    while read -r executable; do
        if [ -f "$executable" ]; then
            sign_item "$executable"
        fi
    done

# Sign any frameworks
find "$APP_PATH" -name "*.framework" -type d | while read -r framework; do
    sign_item "$framework"
done

# Finally, sign the main app bundle
echo -e "\n${BLUE}🎯 Signing main app bundle...${NC}"
sign_item "$APP_PATH"

# Verify the signature
echo -e "\n${BLUE}🔍 Verifying code signature...${NC}"
if codesign --verify --deep --strict "$APP_PATH"; then
    echo -e "${GREEN}✅ Code signature verification passed${NC}"
else
    echo -e "${RED}❌ Code signature verification failed${NC}"
    exit 1
fi

# Display signature information
echo -e "\n${BLUE}📋 Signature Information:${NC}"
codesign --display --verbose=4 "$APP_PATH" 2>&1 | head -10

# Check for Gatekeeper compliance
echo -e "\n${BLUE}🛡️  Gatekeeper Assessment:${NC}"
if spctl --assess --type exec "$APP_PATH" 2>&1; then
    echo -e "${GREEN}✅ App will be accepted by Gatekeeper${NC}"
else
    echo -e "${YELLOW}⚠️  App may be rejected by Gatekeeper${NC}"
    echo -e "${YELLOW}   This is normal for ad-hoc signed apps${NC}"
fi

echo -e "\n${GREEN}🎉 Code signing process completed!${NC}"
echo "================================================="

# Provide user guidance
echo -e "\n${BLUE}📖 Distribution Notes:${NC}"
if [ "$SIGNING_IDENTITY" = "-" ]; then
    echo -e "${YELLOW}⚠️  Ad-hoc signed app:${NC}"
    echo "   • This app is for development/testing only"
    echo "   • Users will need to bypass Gatekeeper manually"
    echo "   • Run: sudo xattr -rd com.apple.quarantine /path/to/EZpanso.app"
else
    echo -e "${GREEN}✅ Developer signed app:${NC}"
    echo "   • App should work without Gatekeeper issues"
    echo "   • Users may still see security dialogs on first run"
    echo "   • Consider notarization for best user experience"
fi

echo -e "\n${BLUE}💡 For production distribution:${NC}"
echo "   1. Use a valid Developer ID certificate"
echo "   2. Consider notarizing the app with Apple"
echo "   3. Test on a clean macOS system"
