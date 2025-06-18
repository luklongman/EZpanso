#!/bin/bash

# EZpanso Code Signing and Notarization Configuration Helper
# This script helps set up the necessary credentials for code signing and notarization

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

# Check if running on macOS
if [[ "$OSTYPE" != "darwin"* ]]; then
    log_error "This script is only for macOS"
    exit 1
fi

echo "EZpanso Code Signing and Notarization Setup"
echo "==========================================="
echo ""

# Check for Developer ID certificates
log_info "Checking for Developer ID certificates..."
DEV_IDS=$(security find-identity -v -p codesigning | grep "Developer ID Application" || true)

if [ -z "$DEV_IDS" ]; then
    log_warning "No Developer ID Application certificates found"
    echo ""
    echo "To code sign your applications, you need a Developer ID Application certificate from Apple."
    echo "1. Join the Apple Developer Program (https://developer.apple.com/programs/)"
    echo "2. Create a Developer ID Application certificate in your Apple Developer account"
    echo "3. Download and install the certificate in your macOS Keychain"
    echo ""
else
    log_success "Found Developer ID Application certificates:"
    echo "$DEV_IDS"
    echo ""
    
    # Extract the first certificate identity
    FIRST_CERT=$(echo "$DEV_IDS" | head -n 1 | sed 's/.*) //' | sed 's/ ".*"//')
    log_info "You can use this certificate identity:"
    echo "DEVELOPER_ID=\"$FIRST_CERT\""
    echo ""
fi

# Check for notarization setup
log_info "Checking notarization setup..."

# Check if xcrun notarytool is available
if ! command -v xcrun &> /dev/null; then
    log_error "Xcode command line tools not found. Install with: xcode-select --install"
else
    log_success "Xcode command line tools available"
fi

# Check for existing notarization profiles
log_info "Checking for notarization profiles..."
PROFILES=$(xcrun notarytool store-credentials --list 2>/dev/null || true)

if [ -z "$PROFILES" ]; then
    log_warning "No notarization profiles found"
    echo ""
    echo "To notarize your applications, you need to set up a notarization profile:"
    echo "1. Generate an app-specific password in your Apple ID account"
    echo "2. Run: xcrun notarytool store-credentials --apple-id your@email.com --team-id YOUR_TEAM_ID --password YOUR_APP_SPECIFIC_PASSWORD"
    echo "3. Choose a profile name (e.g., 'EZpanso-Profile')"
    echo ""
else
    log_success "Found notarization profiles:"
    echo "$PROFILES"
    echo ""
fi

# Check current build_separate.sh configuration
log_info "Checking current build script configuration..."

if [ -f "build_separate.sh" ]; then
    CURRENT_DEV_ID=$(grep "DEVELOPER_ID=" build_separate.sh | head -n 1)
    CURRENT_PROFILE=$(grep "NOTARIZATION_PROFILE=" build_separate.sh | head -n 1)
    
    echo "Current configuration:"
    echo "$CURRENT_DEV_ID"
    echo "$CURRENT_PROFILE"
    echo ""
    
    if echo "$CURRENT_DEV_ID" | grep -q "Your Name"; then
        log_warning "Developer ID not configured in build_separate.sh"
    fi
    
    if echo "$CURRENT_PROFILE" | grep -q "EZpanso-Profile"; then
        log_warning "Notarization profile not configured in build_separate.sh"
    fi
fi

# Provide configuration instructions
echo ""
log_info "Configuration Instructions:"
echo "=========================="
echo ""
echo "1. Edit build_separate.sh and update these variables:"
echo "   DEVELOPER_ID=\"Developer ID Application: Your Name (TEAM_ID)\""
echo "   NOTARIZATION_PROFILE=\"Your-Profile-Name\""
echo ""
echo "2. To set up notarization profile:"
echo "   xcrun notarytool store-credentials --apple-id your@email.com --team-id YOUR_TEAM_ID --password YOUR_APP_SPECIFIC_PASSWORD"
echo ""
echo "3. Test your setup:"
echo "   ./build_separate.sh arm64"
echo ""

# Offer to open relevant documentation
echo ""
read -p "Open Apple Developer documentation for code signing? (y/n): " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    open "https://developer.apple.com/documentation/security/notarizing_macos_software_before_distribution"
fi

log_success "Setup complete! Update build_separate.sh with your credentials."
