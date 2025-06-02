# Changelog

All notable changes to EZpanso will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
