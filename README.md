# EZpanso

**Managing Espanso matches made even easier.**

A modern, intuitive GUI application for managing your [Espanso](https://espanso.org/) text expansion snippets. Built with PyQt6 for a native, responsive experience across platforms.

![EZpanso Screenshot](screenshot.png)

## ✨ Features

### 🎯 Core Workflow
- **📂 Open** - Automatic detection of Espanso match files and packages
- **🔍 Find & Sort** - Quick filtering and intelligent sorting of matches  
- **✏️ Edit** - In-place editing for simple trigger/replace pairs
- **🗑️ Delete** - Safe deletion with confirmation dialogs
- **💾 Save** - Preserve original YAML structure and comments

### 🚀 Smart Features
- **Duplicate Prevention** - Real-time checking prevents duplicate triggers
- **Complex Match Protection** - Advanced snippets (with variables, conditions) are protected from accidental modification
- **Undo/Redo** - Full operation history with keyboard shortcuts
- **Multi-platform** - Works on macOS, Linux, and Windows

### ⚡ Keyboard Shortcuts
- `Cmd+N` (macOS) / `Ctrl+N` - New snippet
- `Cmd+S` (macOS) / `Ctrl+S` - Save all changes  
- `Cmd+F` (macOS) / `Ctrl+F` - Find/filter snippets
- `Cmd+Z` (macOS) / `Ctrl+Z` - Undo
- `Cmd+Shift+Z` (macOS) / `Ctrl+Y` - Redo
- `Delete` / `Backspace` - Delete selected snippets

## 📥 Installation

### Download (Recommended)

**macOS:**
1. Download the latest `EZpanso-x.x.x.dmg` from [Releases](https://github.com/luklongman/EZpanso/releases)
2. Open the DMG and drag EZpanso to Applications
3. Launch EZpanso from Launchpad or Applications folder

**Windows & Linux:**
Coming soon! For now, use the Python installation method below.

### Python Installation

If you have Python 3.11+ installed:

```bash
# Clone the repository
git clone https://github.com/luklongman/EZpanso.git
cd EZpanso

# Install with Poetry (recommended)
poetry install
poetry run ezpanso

# Or install with pip
pip install -r requirements.txt
python main.py
```

## 🚀 Quick Start

1. **Launch EZpanso** - The app automatically detects your Espanso configuration
2. **Select a file** - Choose from the dropdown to view/edit matches
3. **Edit snippets** - Double-click any trigger or replacement text to edit
4. **Add new snippets** - Click "New" or press `Cmd+N`
5. **Save changes** - Press `Cmd+S` when ready to save

### 🎯 Pro Tips
- Use `\n` for line breaks and `\t` for tabs in replacements
- Complex snippets (with variables, forms, etc.) are shown in gray and protected
- The asterisk (*) in the title indicates unsaved changes
- Right-click selected rows for quick delete options

## 🔧 Configuration

EZpanso automatically finds your Espanso directory:
- **macOS**: `~/Library/Application Support/espanso/match`
- **Linux**: `~/.config/espanso/match` 
- **Windows**: `%APPDATA%\espanso\match`

To use a custom directory, go to **File → Set Custom Folder**.

## 🛡️ Safety Features

- **Non-destructive editing** - Original YAML structure and comments are preserved
- **Complex snippet protection** - Advanced Espanso features remain untouched
- **Confirmation dialogs** - All save operations require explicit confirmation
- **Backup recommended** - Always backup your Espanso config before major edits

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

## 🏗️ Development

### Building from Source

**Requirements:**
- Python 3.11+
- Poetry (recommended) or pip

**Setup:**
```bash
git clone https://github.com/luklongman/EZpanso.git
cd EZpanso
poetry install
```

**Run in development:**
```bash
poetry run python main.py
```

**Build macOS app:**
```bash
./build_macos.sh
```

### Architecture

EZpanso follows a clean, modular architecture:

- **main.py** - Main application entry point and UI logic
- **EZpanso.spec** - PyInstaller configuration for app bundling
- **pyproject.toml** - Project dependencies and metadata

## 🤝 Contributing

Contributions are welcome! Please feel free to submit issues and pull requests.

### Development Guidelines
- Follow PEP 8 style guidelines
- Add tests for new features
- Update documentation as needed
- Test on multiple platforms when possible

## 📋 Roadmap

- [ ] Windows and Linux app bundles
- [ ] Snippet templates and categories
- [ ] Import/export functionality
- [ ] Dark mode support
- [ ] Plugin system for custom snippet types

## ⚖️ License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Espanso](https://espanso.org/) - The amazing text expander that makes this tool necessary
- [PyQt6](https://riverbankcomputing.com/software/pyqt/) - For the excellent GUI framework
- [PyYAML](https://pyyaml.org/) - For robust YAML handling

## 📞 Support

- 🐛 **Issues**: [GitHub Issues](https://github.com/luklongman/EZpanso/issues)
- 💬 **Discussions**: [GitHub Discussions](https://github.com/luklongman/EZpanso/discussions)
- 🌐 **Website**: [EZpanso on GitHub](https://github.com/luklongman/EZpanso)

---

**Made with ❤️ by [Longman](https://www.instagram.com/l.ongman) • June 2025**
