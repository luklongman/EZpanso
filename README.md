# EZpanso

**Easy editor for Espanso**

<img src="https://github.com/user-attachments/assets/171a0cfc-f1e6-4070-94a0-eb83ef7c1163" alt="icon_512x512@2x" width="25%" />

A minimal GUI app for managing your [Espanso](https://espanso.org/) text expansion matches, particularly useful for looking up and editing simple matches across YAML files. Built with PyYAML & PyQt6. Available across platforms.

<https://github.com/user-attachments/assets/47499f82-af35-42ba-9cab-21e8aa332cc5>

## 🆕 Update v1.1 (Jun 02, 2025)

### 🍎 macOS Compatibility Fixed

- **Universal Binary Support** - Fixed "application is not supported on this Mac" error by building universal binary for both Intel and Apple Silicon architectures
- **Full macOS Support** - Now works on all Mac systems including older Intel Macs and new Apple Silicon Macs

### 🐛 Bug Fixes

- Fixed dialog workflow for creating new matches with validation errors
- Improved file modification tracking for better save operations
- Enhanced user experience when dealing with duplicate triggers or empty fields

## ✨ Features

- **📂 Open Match Files** - Espanso match files and packages at default or custom folderpath.
- **🔍 Find & Sort** - Quick filter and sortable columns
- **📄 Multi-line Replacement** - Support `\n` for line breaks and `\t` for tabs
- **✏️ Edit** - In-place editing for simple matches with full undo/redo support
- **🆕 Create** - Make new matches with duplicate prevention
- **🗑️ Delete** - Safe deletion with confirmation dialogs
- **💾 Save** - Preserve original YAML structure and comments
- **🛡️ Dynamic Match Protection** - Matches with variables or conditions are shown in gray and not editable
- **⚠️ Package Safety** - Warning dialog when editing package files with option to disable
- **🌍 Multi-platform** - Works on macOS, Linux, and Windows

### ⚡ Keyboard Shortcuts

- `Cmd+N` (macOS) / `Ctrl+N` - New match
- `Cmd+S` (macOS) / `Ctrl+S` - Save all changes  
- `Cmd+F` (macOS) / `Ctrl+F` - Find matches
- `Cmd+Z` (macOS) / `Ctrl+Z` - Undo
- `Cmd+Shift+Z` (macOS) / `Ctrl+Y` - *Redo*
- `Delete` / `Backspace` - Delete selected matches
- `Cmd+O` (macOS) / `Ctrl+O` - Set folder

## 📥 Installation

### macOS (Recommended)

1. Download the latest `EZpanso-1.1.0.dmg` from [Releases](https://github.com/luklongman/EZpanso/releases)
2. Open the DMG and drag EZpanso to Applications
3. Launch EZpanso from Launchpad or Applications folder

### Cross-Platform (Python)

**Requirements:** Python 3.11+

```bash
# 1. Clone the repository
git clone https://github.com/luklongman/EZpanso.git
cd EZpanso

# 2a. Install dependencies and run with pip
pip install -r requirements.txt
python main.py

# 2b. Or with Poetry 
poetry install
poetry run python main.py
```

**Dependencies:**

- PyQt6
- PyYAML

## 🔧 Configuration

EZpanso automatically finds your Espanso directory:

- **macOS**: `~/Library/Application Support/espanso/match`
- **Linux**: `~/.config/espanso/match`
- **Windows**: `%APPDATA%\espanso\match`

To use a custom directory, go to menubar for **Set Folder**.

### Espanso File Format

EZpanso expects standard Espanso YAML format:

```yaml
matches:
  - trigger: ":hello"
    replace: "Hello, World!"
  - trigger: ":email"
    replace: "user@example.com"
```

## 🛡️ Safety Reminder

Although there are confirmations for save and delete operations, it's highly recommended to backup your Espanso configuration before making significant changes.

## 🏗️ Development

### Building from Source

```bash
git clone https://github.com/luklongman/EZpanso.git
cd EZpanso
poetry install

# Run in development
poetry run python main.py

# Build macOS app
./build_macos.sh
```

### Architecture

EZpanso follows a simple and monolithic architecture:

- **main.py** - Single file containing all application logic, GUI components, and data handling
- **EZpanso.spec** - PyInstaller configuration for app bundling  
- **pyproject.toml** - Project dependencies and metadata

## 🤝 Contributing

EZpanso is pretty much done and I've learnt a lot. I am happy to revisit when major update is required. I hope the python installation is good enough for Windows and Linux users! Feel free to contribute, submit issues and pull requests.

## ⚖️ License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Espanso](https://espanso.org/) - The amazing text expander.
- [EspansoEdit](https://ee.qqv.com.au/) - Windows Freeware editor and utility suite for Espanso by [EeAdmin](https://www.reddit.com/user/EeAdmin/), who provided valuable feedback upon inital release
- [PyQt6](https://riverbankcomputing.com/software/pyqt/) - Python GUI framework
- [PyYAML](https://pyyaml.org/) - For YAML handling

**by [Longman](https://www.instagram.com/l.ongman) • June 2025**
