# macOS Gatekeeper Workaround Guide

## The Problem

When you download and try to open EZpanso on macOS, you might see this error:

> **"EZpanso" is damaged and can't be opened. You should move it to the Trash.**

This is **NOT** because the app is actually damaged. It's because macOS Gatekeeper is being overly protective of unsigned applications.

## Why This Happens

- EZpanso is not code-signed with an expensive Apple Developer certificate ($99/year)
- macOS flags any unsigned app downloaded from the internet as potentially dangerous
- This is a security feature, but can be safely bypassed for trusted applications

## Solutions (Choose One)

### Option 1: Automated Fix Script ⭐ **Recommended**

1. Download and run our fix script:

   ```bash
   curl -L https://raw.githubusercontent.com/yourusername/EZpanso/main/scripts/fix_gatekeeper_issue.sh -o fix_gatekeeper.sh
   chmod +x fix_gatekeeper.sh
   sudo ./fix_gatekeeper.sh
   ```

2. Or if you have the EZpanso source code:

   ```bash
   cd /path/to/EZpanso
   sudo scripts/fix_gatekeeper_issue.sh
   ```

### Option 2: Manual Terminal Command

Open Terminal and run:

```bash
sudo xattr -rd com.apple.quarantine /Applications/EZpanso.app
```

### Option 3: GUI Method

1. **Right-click** on EZpanso.app
2. Select **"Open"** (not double-click)
3. Click **"Open"** again when macOS warns you
4. The app will now open normally forever

### Option 4: System Preferences

1. Try to open EZpanso (it will fail)
2. Go to **System Preferences** → **Security & Privacy**
3. Click **"Open Anyway"** next to the EZpanso warning
4. Enter your password if prompted

## For Advanced Users

If you want to verify the app hasn't been tampered with:

```bash
# Check if app has quarantine attribute
xattr /Applications/EZpanso.app

# View all extended attributes
xattr -l /Applications/EZpanso.app

# Remove only the quarantine attribute (safest)
sudo xattr -d com.apple.quarantine /Applications/EZpanso.app
```

## Why We Don't Code Sign

- Apple charges $99/year for Developer ID certificates
- This is a free, open-source project
- The app is safe - you can review the source code
- Many legitimate Mac apps use these same workarounds

## Security Note

Only use these methods with software you trust. EZpanso is open-source, so you can:

- Review the code on GitHub
- Build it yourself from source
- Report any security concerns

## Troubleshooting

**Still having issues?**

1. Make sure you copied EZpanso to `/Applications/` (not running from Downloads)
2. Try restarting your Mac after applying the fix
3. Check that you have admin permissions on your Mac
4. If using Terminal, make sure you include `sudo` for the commands

**Permission denied errors?**

- Make sure you're running commands with `sudo`
- Verify you have admin access on your Mac
- Try the GUI method instead

## Future Updates

Once you've bypassed Gatekeeper for EZpanso:

- Future updates will open normally
- You won't need to repeat these steps
- Unless you completely reinstall or move the app

---

**Need help?** Open an issue on our GitHub repository with details about your macOS version and the exact error you're seeing.
