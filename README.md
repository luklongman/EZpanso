# EZpanso - Easy editor for Espanso

<div>
  <img src="https://github.com/user-attachments/assets/cb893176-d625-42fd-b332-e72b8827cec4" alt="EZpanso-icon" width="120" align="left" style="margin-right: 20px;" />
  <div style="padding-left: 20px;">
    <p>A minimal GUI app for managing your <a href="https://espanso.org/">Espanso</a> text expansion matches, particularly useful for looking up and editing simple matches across YAML files. Built with PyQt6 & PyYAML/ruamel.yaml. DMG available for Apple Silicon MacOS. Python installation available across platforms. Visit <a href="CHANGELOG.md">CHANGELOG.md</a> for detailed release notes.</p>
  </div>
</div>
<br clear="all" />

<https://github.com/user-attachments/assets/774fa2c8-ad27-42ca-85c5-8342e2a99802>

## ✨ Features

- **Open Match Files** - Espanso match files and packages at default or custom folderpath.
- **Find & Sort** - Quick filter and sortable columns
- **Edit** - In-place editing for simple matches with full undo/redo support
- **Create** - Make new matches with duplicate prevention
- **Delete** - Safe deletion with confirmation dialogs
- **Multi-line Replacement** - Support `\n` for line breaks and `\t` for tabs
- **Save** - Preserve original YAML structure and comments *(with **ruamel.yaml** in v1.2.1)*
- **Dynamic Match Protection** - Matches with variables or conditions are shown in gray and not editable
- **Package Safety** - Warning dialog when editing package files

## ⚡ Keyboard Shortcuts

- `Cmd+N` (macOS) / `Ctrl+N` - New match
- `Cmd+S` (macOS) / `Ctrl+S` - Save all changes  
- `Cmd+F` (macOS) / `Ctrl+F` - Find matches
- `Cmd+Z` (macOS) / `Ctrl+Z` - Undo
- `Cmd+Shift+Z` (macOS) / `Ctrl+Y` - *Redo*
- `Delete` / `Backspace` - Delete selected matches
- `Cmd+O` (macOS) / `Ctrl+O` - Open current file for advanced editing *(Added in v1.2.0)*
- `Cmd+R` (macOS) / `Ctrl+R` - Refresh files and entries *(Added in v1.2.1)*

## 📥 Installation

### macOS (Apple Silicon)

1. Download the Apple Silicon DMG: `EZpanso-1.2.1-arm64.dmg`
   - Available from [Releases](https://github.com/luklongman/EZpanso/releases)
2. Open the DMG and drag EZpanso to Applications
3. Launch EZpanso from Launchpad or Applications folder

> **⚠️ macOS Security Notice**: If you see **"EZpanso is damaged and can't be opened"**, this is a normal macOS security warning for unsigned apps. See our [macOS Gatekeeper Workaround Guide](docs/MACOS_GATEKEEPER_WORKAROUND.md) for easy solutions.

### All Platforms (pip installation)

**Requirements:** Python 3.11+

```bash
# Install directly from pip (recommended)
pip install ezpanso

# Run the application
ezpanso
```

Alternatively, install from source:

```bash
# Clone the repository
git clone https://github.com/luklongman/EZpanso.git
cd EZpanso

# Install with pip
pip install -e .

# Or with Poetry 
poetry install
poetry run ezpanso
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

### Quick Start

```bash
git clone https://github.com/luklongman/EZpanso.git
cd EZpanso
poetry install

# Run in development
poetry run python main.py
```

### Building

```bash
# Build for Apple Silicon (full features including comment preservation)
./build_apple_silicon.sh
```

### Development Scripts

```bash
# Clean build artifacts
python scripts/cleanup.py

# Analyze build size
python scripts/analyze_build.py

# Run tests
pytest test.py -v
```

For detailed development information, see [DEVELOPMENT.md](DEVELOPMENT.md).

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
