# EZpanso 1.2.1 - Easy editor for Espanso

<div>
  <img src="https://github.com/user-attachments/assets/cb893176-d625-42fd-b332-e72b8827cec4" alt="EZpanso-icon" width="160" align="left" style="margin-right: 20px; margin-top: -20px;" />
  <div>
    <p style="margin-top: 30px;">A minimal GUI app for managing your <a href="https://espanso.org/">Espanso</a> text expansion matches, particularly useful for looking up and editing simple matches across YAML files. Built with PyQt6 & PyYAML/ruamel.yaml. DMG available for Apple Silicon macOS. Python installation available across platforms. Visit <a href="CHANGELOG.md">CHANGELOG.md</a> for detailed release notes.</p>
  </div>
</div>
<br clear="all" />

https://github.com/user-attachments/assets/89aba5da-6636-417d-a75f-37485189e83b

## Features

| User flow | description | macOS | Windows/Linux | Version |
|:------|:-------------|:-------|:---------------|:---------|
| **Auto-Load** | Auto-Load Espanso match files and packages at default folder path |  |  | |
| **Locate** | Or customize folder path at settings| ⌘+, | Ctrl+, | 1.2.0+ |
| **Find & Sort** | Filter quickly and view table with sortable columns | ⌘+F | Ctrl+F | |
| **Edit Simple Matches** | Edit in place with undo/redo support | ⌘+Z / ⇧⌘+Z | Ctrl+Z / Ctrl+Y | |
| **Create** | Add new matches with duplicate detection | ⌘+N | Ctrl+N | |
| **Support Multi-line** | Use `\n` for line breaks and `\t` for tabs |  |  | |
| **Delete** | Remove matches safely with confirmation dialogs | Delete | Backspace | |
| **Protect Dynamic Matches** | Display matches with variables or conditions in gray and prevent editing |  |  | 1.1.0+ |
| **Preserve YAML** | Maintain original YAML structure and comments thanks to ruamel.yaml | ⌘+S | Ctrl+S | 1.2.1+ |
| **Access YAML** | Open current YAML file for advanced editing | ⌘+O | Ctrl+O | 1.2.0+ |
| **Refresh Data** | Update files and entries after save | ⌘+R | Ctrl+R | 1.2.1+ |
| **Warn About Packages** | Show warning dialog when editing package files |  |  | 1.2.0+ |

## 📥 Installation

### macOS (Apple Silicon)

1. Download `EZpanso-1.2.1-arm64.dmg` from [Releases](https://github.com/luklongman/EZpanso/releases)
2. Open the DMG and drag EZpanso to Applications
3. Launch EZpanso

### All Platforms (Python Installation)

**Requirements:** Python 3.11+

```bash
# Clone the repository
git clone https://github.com/luklongman/EZpanso.git
cd EZpanso

# Option 1: Install with pip and requirements.txt
pip install -r requirements.txt
python main.py

# Option 2: Install with Poetry
poetry install
poetry run python main.py
```

**Dependencies:**

- PyQt6
- PyYAML
- ruamel.yaml *(Added in v1.2.1 for comment preservation)*

### 🔧 Configuration

By default, EZpanso finds your Espanso directory at:

- **macOS**: `~/Library/Application Support/espanso/match`
- **Linux**: `~/.config/espanso/match`
- **Windows**: `%APPDATA%\espanso\match`

To customize the folder path, go to settings.

### Espanso File Format

EZpanso expects standard Espanso YAML format:

```yaml
matches:
  - trigger: ":hello"
    replace: "Hello, World!"
  - trigger: ":email"
    replace: "user@example.com"
```

### 🛡️ Safety Reminder

Although there are confirmations for save and delete operations, it's highly recommended to backup your Espanso configuration before making significant changes.

### Architecture

EZpanso follows a simple and monolithic architecture:

- **main.py** - Single file containing all application logic, GUI components, and data handling
- **EZpanso.spec** - PyInstaller configuration for app bundling  
- **pyproject.toml** - Project dependencies and metadata

## 🤝 Contributing

EZpanso is pretty much done and I've learnt a lot. I am happy to revisit when major update is required. I hope the python installation is good enough for non Apple Silicon users. Feel free to contribute, submit issues and pull requests.

## ⚖️ License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Espanso](https://espanso.org/) - The amazing text expander.
- [EspansoEdit](https://ee.qqv.com.au/) - Windows Freeware editor and utility suite for Espanso by [EeAdmin](https://www.reddit.com/user/EeAdmin/), who provided valuable feedback upon inital release
- [PyQt6](https://riverbankcomputing.com/software/pyqt/) - Python GUI framework
- [PyYAML](https://pyyaml.org/) - For YAML handling
- [ruamel.yaml](yaml.dev/doc/ruamel.yaml/) - Preserve YAML comments.

**by [Longman](https://www.instagram.com/l.ongman) • June 2025**
