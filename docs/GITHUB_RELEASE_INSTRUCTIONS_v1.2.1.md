# GitHub Release Instructions for EZpanso v1.2.1

## Release Steps

1. **Go to GitHub repository**
   - Navigate to the repository page

2. **Create new release**
   - Click on "Releases" in the right sidebar
   - Click "Draft a new release" or "Create a new release"

3. **Set up release information**
   - Tag version: `v1.2.1`
   - Release title: `EZpanso v1.2.1`
   - Description: Copy content from CHANGELOG.md for version 1.2.1 (provided below)

4. **Upload asset**
   - Upload the `EZpanso-1.2.1-arm64.dmg` file from project root

5. **Publish release**
   - Click "Publish release"

## Release Description Content

```markdown
## [1.2.1] - 2025-06-17

### Fixed

- 🔧 **File Loading Robustness** - Fixed critical bug where files with empty matches were not loaded into the UI dropdown
- 🎯 **UI Population** - Enhanced file loading to ensure all valid YAML files appear in the file selector, even if they contain no matches
- 📱 **Initialization Order** - Improved UI initialization sequence to handle edge cases where file loading occurs before UI setup
- 🖊️ **Edit Persistence** - Edit operations are now correctly handled and saved to file

### Added

- 🔄 **Refresh button** - Added a button to reload the file list in the UI, ensuring all valid files are displayed.
- 🔍 **Unique ID tracking** - Implemented unique ID tracking for each entry in the YAML to ensure correct file handling.
- 🧪 **Testing suite** - Added a testing suite for file loading and UI population to ensure robustness against edge cases.

### Removed

- ❌ **Intel Build Support** - Temporarily removed support for Intel builds in this version due to technical issues are resolved.

### Technical

- Improved `_load_single_yaml_file` to load files even when matches array is empty
- Enhanced `_load_all_yaml_files` to populate file selector with deferred loading support
- Added error handling for file loading and UI population edge cases
- Updated version references throughout build scripts and documentation
```

## Download Instructions

Include the following download instructions in the GitHub release description:

```markdown
## 📥 Download

- **Apple Silicon (M1/M2/M3) Macs**: Download the `EZpanso-1.2.1-arm64.dmg` file attached to this release

## 🔧 Installation

1. Download the DMG file for Apple Silicon
2. Open the DMG and drag EZpanso to Applications
3. Launch EZpanso from Launchpad or Applications folder

Intel build support will be restored in a future update once technical issues are resolved.
```
