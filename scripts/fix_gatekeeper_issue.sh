#!/bin/bash

# Fix Gatekeeper Issue for EZpanso
# This script helps users bypass the "damaged and can't be opened" error
# without requiring expensive code signing certificates

echo "EZpanso Gatekeeper Fix Script"
echo "============================="
echo ""

# Check if EZpanso.app exists in Applications
if [ ! -d "/Applications/EZpanso.app" ]; then
    echo "❌ EZpanso.app not found in /Applications/"
    echo "Please make sure EZpanso is installed in your Applications folder first."
    exit 1
fi

echo "🔍 Found EZpanso.app in Applications folder"
echo ""

# Remove quarantine attribute
echo "🔧 Removing quarantine attribute..."
sudo xattr -rd com.apple.quarantine /Applications/EZpanso.app 2>/dev/null

if [ $? -eq 0 ]; then
    echo "✅ Successfully removed quarantine attribute"
else
    echo "ℹ️  No quarantine attribute found (this is normal)"
fi

# Remove extended attributes that might cause issues
echo "🔧 Cleaning extended attributes..."
sudo xattr -c /Applications/EZpanso.app 2>/dev/null

echo ""
echo "🎉 EZpanso should now open without issues!"
echo ""
echo "💡 If you still have problems, try:"
echo "   1. Right-click EZpanso.app → Open"
echo "   2. Click 'Open' when macOS warns about the developer"
echo "   3. Go to System Preferences → Security & Privacy → Allow EZpanso"
echo ""
echo "📝 This is a one-time fix. You won't need to run this again unless you reinstall EZpanso."
