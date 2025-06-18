# Changelog

All notable changes to EZpanso will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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

## [1.2.0] - 2025-06-03

### Added

- 📂 **Open File Button** - Added "Open" button next to the dropdown list to open the current file for advanced editing in the system's default editor
- ⌨️ **Open File Shortcut** - Added `Cmd+O` (macOS) / `Ctrl+O` keyboard shortcut to open current file for advanced editing
  
- 🏗️ **Separated build Intel and Apple Silicon**
  
### Improved

- 📝 **YAML Formatting** - Enhanced YAML output formatting to avoid unnecessary double quotes wrapping by default, resulting in cleaner and more readable YAML files
- 🔧 **Unified Preferences Dialog** - Consolidated About, Settings, and Links into a single comprehensive Preferences dialog for better user experience
- 🔄 **Button Text Update** - Changed "New" button to "New match" for better clarity
- 🎨 **Enhanced Dialog Design** - Improved design for readability and consistency across all dialogs
- ⚡ **Better UI Layout** - Reorganized UI components for improved proportions and usability
- 🏗️ **Streamlined App Naming** - Both Intel and Apple Silicon versions now install as "EZpanso.app" for cleaner user experience, with architecture differentiation in preferences and DMG naming

### Technical

- Added `_open_current_file` method using QDesktopServices to open files with system default editor
- Updated keyboard shortcuts setup to include Open functionality
- Enhanced UI layout with properly formatted Open button including shortcut display
- Updated YAML serialization settings for improved output formatting
- Refactored menubar setup to use platform-appropriate menu handling (application menu on macOS, single menu on other platforms)
- Restructured preferences dialog to combine multiple sections (About, Settings, Links) into one cohesive interface
- Implemented comprehensive dialog styling system for consistent user experience
- Enhanced input validation and user feedback throughout the application
- Added architecture detection and display in preferences dialog (shows "Intel" or "Apple Silicon")
- Created streamlined `build_current_arch.sh` script for individual users to build for their specific architecture
- Maintained separate DMG naming (`EZpanso-1.2.0-Intel.dmg` vs `EZpanso-1.2.0-AppleSilicon.dmg`) for clear distribution

## [1.1.0] - 2025-06-02

### Fixed

- 🍎 **macOS Compatibility** - Fixed "application is not supported on this Mac" error by building universal binary for both Intel and Apple Silicon architectures
- 🛡️ **Dialog Workflow** - Dialog stays open when validation fails, allowing users to fix issues without starting over
- 💾 **File Modification Tracking** - Improved save operations to only save modified files
- 🎯 **User Experience** - Enhanced workflow when dealing with duplicate triggers or empty fields

### Technical

- Built with universal2 target architecture for full macOS compatibility
- Rebuilt PyYAML from source to support universal binary creation
- Improved error handling and user feedback in match creation dialogs

## [1.0.0] - 2025-06-01

### Added

- 🎉 **Initial release of EZpanso**
- 📂 **Automatic Espanso directory detection** for macOS and Linux
- 🔍 **Smart file loading** with recursive YAML discovery
- ✏️ **In-place editing** for simple trigger/replace pairs
- 🛡️ **Complex snippet protection** - Advanced snippets with variables are protected from editing
- 🗑️ **Safe deletion** with confirmation dialogs
- 💾 **Structure-preserving saves** - Original YAML formatting and comments maintained
- 🚫 **Duplicate prevention** - Real-time checking for duplicate triggers
- ⌨️ **Keyboard shortcuts** for all major actions (New, Save, Find, Delete, Undo/Redo)
- 🔄 **Undo/Redo system** with operation history
- 🎯 **Smart sorting** - Editable entries first, then alphabetical
- 🔍 **Real-time filtering** with search box
- 📱 **Cross-platform support** for macOS, Linux, and Windows
- 🎨 **Native UI** built with PyQt6 for responsive experience
- 📦 **macOS app bundle** with proper icon and DMG installer

### Features

- **File Management**
  - Automatic detection of standard Espanso directories
  - Custom folder selection option
  - Smart display names for package.yml files (shows parent folder)
  - Support for nested directories and complex package structures

- **Snippet Editing**
  - Double-click to edit triggers and replacements
  - Real-time validation and error reporting
  - Escape sequence support (\n for newlines, \t for tabs)
  - Multi-line replacement text support
  - Protection for complex snippets (variables, forms, conditions)

- **Safety Features**
  - Confirmation dialogs before saving or deleting
  - Modification tracking with visual indicators (asterisk in title)
  - Original YAML structure preservation
  - Backup-safe file operations

- **User Experience**
  - Responsive table with adjustable columns
  - Context menus for quick actions
  - Comprehensive keyboard shortcut support
  - Clear error messages and user feedback
  - Professional macOS app bundle with proper icon

### Technical

- **Architecture**: Single-file Python application for simplicity
- **Dependencies**: PyQt6, PyYAML, Poetry for management
- **Build System**: PyInstaller with custom spec for macOS
- **Icon Support**: Full iconset with multiple resolutions
- **File Format**: Preserves YAML structure and comments

### Known Limitations

- Complex snippets (with variables, forms, etc.) are read-only
- Windows and Linux app bundles not yet available (use Python installation)
- No dark mode support yet
- Limited to basic trigger/replace editing

## [Unreleased]

### Planned

- Windows and Linux app bundles
- Dark mode support
- Snippet templates and categories
- Import/export functionality
- Enhanced search with regex support
- Plugin system for custom snippet types
