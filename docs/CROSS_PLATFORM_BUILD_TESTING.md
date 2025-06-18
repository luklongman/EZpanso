# Cross-Platform Build Testing Guide for EZpanso

This guide explains how to properly test the EZpanso build system across different platforms.

## Prerequisites

Before testing, ensure you have:

1. Python 3.6+ installed
2. PyInstaller installed (`pip install pyinstaller`)
3. PyQt6 installed (`pip install PyQt6`)
4. PyYAML installed (`pip install PyYAML`)
5. ruamel.yaml installed (`pip install ruamel.yaml`) - optional but recommended

## Available Spec Files

EZpanso now includes platform-specific spec files:

- `EZpanso-arm64.spec` - For macOS on Apple Silicon (M1/M2)
- `EZpanso-intel.spec` - For macOS on Intel processors
- `EZpanso-windows.spec` - For Windows (all architectures)
- `EZpanso-linux.spec` - For Linux (all architectures)

## Testing Process

We've created a test script (`test_build.py`) to help validate builds. Here's how to use it:

### 1. Basic Validation

To validate a spec file without building (quick check):

```bash
./test_build.py --validate-only --spec EZpanso-arm64.spec
```

This will check the spec file for syntax errors and ensure it has all required components.

### 2. Full Build Testing

To test the full build process for your current platform:

```bash
./test_build.py --all
```

This will:

1. Detect your platform
2. Select the appropriate spec file
3. Validate the spec file
4. Run a test build
5. Verify the build artifacts
6. Perform a smoke test on the built application

### 3. Testing Specific Spec Files

To test a specific spec file (regardless of platform):

```bash
./test_build.py --spec EZpanso-windows.spec
```

### 4. Smoke Testing

To run just the smoke test on previously built artifacts:

```bash
./test_build.py --smoke-test
```

## Cross-Platform Testing Matrix

For comprehensive cross-platform testing, you should perform the following tests:

| Platform | Spec File | Command |
|----------|-----------|---------|
| macOS (Apple Silicon) | EZpanso-arm64.spec | `./test_build.py --all` |
| macOS (Intel) | EZpanso-intel.spec | `./test_build.py --all` |
| Windows | EZpanso-windows.spec | `python test_build.py --all` |
| Linux | EZpanso-linux.spec | `./test_build.py --all` |

## Platform-Specific Notes

### macOS

- The build process requires appropriate code signing for distribution
- To test notarization, you need a developer account
- The `--smoke-test` will launch and quickly close the app to verify it runs

### Windows

- You may need to adjust paths in the spec file for Windows path conventions
- Windows testing works best with Python installed via the official installer
- The `file_version_info.txt` file is used for Windows exe metadata

### Linux

- Different Linux distributions may require additional libraries
- Consider testing on Ubuntu and at least one other major distribution
- The .desktop file is not created automatically but is needed for desktop integration

## Tips for Successful Cross-Platform Builds

1. **Clean Between Builds**: Always run `./build.py --clean` before switching platforms
2. **Verify Dependencies**: Ensure all dependencies are installed with `./build.py --deps`
3. **Check File Sizes**: Unusually large builds may indicate unnecessary libraries
4. **Test User Experience**: Launch and test the app manually to verify functionality
5. **Version Consistency**: Ensure version numbers are consistent across all spec files

## Troubleshooting Common Issues

### Issue: "ImportError" in built application

Solution: Check your `hiddenimports` in the spec file - you may be missing a required module.

### Issue: Missing icons or resources

Solution: Verify the paths in the `datas` section of your spec file.

### Issue: "This app is damaged" on macOS

Solution: You need proper code signing and notarization for macOS distribution.

### Issue: DLL missing errors on Windows

Solution: Add the missing DLL to the `binaries` section of your spec file.

## Final Verification Checklist

Before releasing a build, verify:

- [ ] Application launches successfully
- [ ] All features work as expected
- [ ] File sizes are reasonable
- [ ] Application icon displays correctly
- [ ] About/version information is correct
- [ ] App integrates properly with the OS (dock, taskbar, etc.)

By following this guide, you can ensure that EZpanso builds correctly across all supported platforms.
