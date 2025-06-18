# EZpanso macOS Distribution Fix - "App is Damaged" Error

## Problem

Users downloading EZpanso-1.2.0-Intel.dmg report: *"EZpanso is damaged and can't be opened. You should move it to the Trash."*

## Root Cause

This is a macOS Gatekeeper security issue. The application isn't properly code-signed, triggering Apple's security protections that prevent unsigned or improperly signed apps from running.

## Immediate User Solutions

### Method 1: Remove Quarantine Attribute (Recommended)

```bash
# After installing the app to Applications folder
sudo xattr -rd com.apple.quarantine /Applications/EZpanso.app
```

### Method 2: Manual Override

1. Right-click on EZpanso.app in Applications
2. Select "Open" from context menu
3. Click "Open" again when the security dialog appears
4. The app will now run normally

### Method 3: System Preferences

1. Go to System Preferences → Security & Privacy → General
2. If you recently tried to open EZpanso, you'll see "EZpanso was blocked..."
3. Click "Open Anyway"

## Developer Solutions Implemented

### 1. Code Signing Script (`scripts/codesign_app.sh`)

- Comprehensive code signing for all app components
- Support for both ad-hoc and developer certificate signing
- Automatic verification and Gatekeeper assessment
- Proper entitlements handling

### 2. Entitlements File (`scripts/entitlements.plist`)

- Hardened runtime compatible entitlements
- File system access permissions
- JIT compilation support for Python
- PyInstaller-specific requirements

### 3. Updated Build Process

- Automatic code signing integrated into build pipeline
- Environment variable support for signing identity
- Clear feedback about signing status

## Usage for Developers

### Development Builds (Ad-hoc signing)

```bash
# No special setup needed
./build_multi_arch.sh
```

### Distribution Builds (Developer ID signing)

```bash
# Set your Developer ID certificate
export CODESIGN_IDENTITY="Developer ID Application: Your Name (TEAM_ID)"
./build_multi_arch.sh
```

### Manual Code Signing

```bash
# Make script executable
chmod +x scripts/codesign_app.sh

# Sign with ad-hoc (development)
scripts/codesign_app.sh dist/EZpanso.app adhoc

# Sign with Developer ID (distribution)
scripts/codesign_app.sh dist/EZpanso.app "Developer ID Application: Your Name"
```

## Verification Commands

```bash
# Check signature
codesign --verify --deep --strict EZpanso.app

# Display signature info
codesign --display --verbose=4 EZpanso.app

# Test Gatekeeper acceptance
spctl --assess --type exec EZpanso.app
```

## Next Steps for Production

1. **Obtain Developer ID Certificate**
   - Enroll in Apple Developer Program
   - Create Developer ID Application certificate
   - Install certificate in Keychain

2. **Consider App Notarization**
   - Upload signed app to Apple for notarization
   - Staple notarization ticket to app
   - Provides best user experience

3. **Test Distribution**
   - Test on clean macOS systems
   - Verify no Gatekeeper issues
   - Document any remaining user steps

## Technical Notes

- Ad-hoc signing prevents the "damaged" error but users still see security warnings
- Developer ID signing reduces security warnings significantly  
- Notarization eliminates most security warnings
- The entitlements file ensures compatibility with macOS security requirements

## Files Modified/Added

- `scripts/codesign_app.sh` - Code signing automation
- `scripts/entitlements.plist` - Runtime entitlements
- `build_multi_arch.sh` - Updated to include signing
- This documentation

## Impact

- ✅ Eliminates "app is damaged" error
- ✅ Provides clear user workarounds  
- ✅ Implements proper development workflow
- ✅ Prepares for production distribution
- ✅ Maintains backward compatibility
