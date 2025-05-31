# EZpanso - Espanso Manager

A minimal GUI app for managing Espanso text expansion snippets with focus on simplicity and reliability.

## Overview

EZpanso provides an intuitive interface to view, edit, and manage your Espanso YAML configuration files without the complexity of dealing with raw YAML syntax. The application follows a 7-step core workflow designed for efficiency and safety.

## Current Features

### ✅ Core Functionality (Implemented)

**File Management:**

- Automatic detection of Espanso directories (`~/Library/Application Support/espanso/match` on macOS, `~/.config/espanso/match` on Linux)
- Recursive loading of all YAML files including subfolders
- Smart display names (shows parent folder for `package.yml` files)
- File selector dropdown for easy navigation

**Snippet Viewing & Editing:**

- Clean table interface with Trigger/Replace columns
- In-place editing with real-time validation
- Duplicate trigger detection and prevention
- Visual indication of complex snippets (grayed out, non-editable)
- Automatic preservation of complex YAML structures

**Data Safety:**

- Modification tracking with visual indicators (asterisk in title)
- Confirmation dialogs before saving
- Preservation of existing YAML structure and comments
- Backup-safe file operations

**User Experience:**

- Responsive table with adjustable column widths
- Clear error messages and warnings
- Cross-platform compatibility (macOS, Linux, Windows)

### 🔒 Safety Features

- **Complex Snippet Protection**: Snippets with variables, conditions, or advanced features are automatically detected and protected from accidental modification
- **Duplicate Prevention**: Real-time checking prevents duplicate triggers within the same file
- **Structure Preservation**: All non-match YAML content is preserved during saves
- **Confirmation Required**: All save operations require explicit user confirmation

## Technical Architecture

### Core Components

```python
class CoreEZpanso(QMainWindow):
    """Main application class implementing the 7-step workflow"""
```

**Data Model:**

- `FileData = Dict[str, List[Dict[str, Any]]]` - Simple dictionary structure
- File path → List of match dictionaries mapping
- No external dependencies beyond PyQt6 and PyYAML

**Key Methods:**

- `_load_all_yaml_files()` - Discovers and loads all Espanso files
- `_populate_table()` - Renders snippets with appropriate protections
- `_on_item_changed()` - Handles real-time editing with validation
- `_save_all_files()` - Safely persists changes back to original files

### Dependencies

```
Python 3.8+
PyQt6
PyYAML
```

## Installation & Usage

### Quick Start

1. **Install Dependencies:**

   ```bash
   pip install PyQt6 PyYAML
   ```

2. **Run Application:**

   ```bash
   python main.py
   ```

3. **Edit Snippets:**
   - Select a file from the dropdown
   - Click any trigger or replace text to edit
   - Changes are tracked automatically
   - Click "Save All" when ready

### File Structure Requirements

EZpanso expects the standard Espanso directory structure:

```
~/Library/Application Support/espanso/match/  (macOS)
~/.config/espanso/match/                       (Linux)
```

Files should contain standard Espanso YAML format:

```yaml
matches:
  - trigger: ":hello"
    replace: "Hello, World!"
  - trigger: ":email"
    replace: "user@example.com"
```

## Contributing

EZpanso is designed to be simple and maintainable. When contributing:

1. **Follow the 7-step workflow pattern** established in the core
2. **Maintain backward compatibility** with existing Espanso files
3. **Add comprehensive error handling** for new features
4. **Keep dependencies minimal** - avoid adding new requirements unless essential
5. **Test cross-platform** - ensure features work on all supported platforms

## License

[Specify your license here]

## Support

For issues, feature requests, or questions:

- Create an issue in the project repository
- Ensure you include your OS, Python version, and steps to reproduce any problems

---

**Current Status**: Core functionality complete and stable  
**Next Release**: v0.2.0 with enhanced editing features  
**Last Updated**: June 1, 2025
