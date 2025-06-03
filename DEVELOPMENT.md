# EZpanso Development Guide

## 🏗️ Building

### Quick Build (Current Architecture)

```bash
./build_current_arch.sh
```

### Multi-Architecture Build (Distribution)

```bash
./build_multi_arch.sh
```

## 🧹 Development Scripts

### Cleanup Before Build

```bash
python scripts/cleanup.py
```

### Analyze Build Size

```bash
python scripts/analyze_build.py
```

## 🧪 Testing

### Run Tests

```bash
pytest test.py -v
```

### Manual Testing

```bash
poetry run python main.py
```

## 📁 Project Structure

```
├── main.py                    # Main application code
├── EZpanso*.spec             # PyInstaller specs for different architectures
├── build_*.sh                # Build scripts
├── scripts/                  # Development utilities
│   ├── cleanup.py            # Clean build artifacts
│   └── analyze_build.py      # Analyze build size
├── icon.iconset/             # Icon source files
├── icon.icns                 # Compiled icon
└── test.py                   # Test suite
```

## 🔧 Configuration Files

- `pyproject.toml` - Project dependencies and metadata
- `requirements.txt` - Pip-compatible dependencies
- `poetry.lock` - Locked dependency versions

## 🚀 Release Process

1. Update version in `pyproject.toml`
2. Update `CHANGELOG.md`
3. Update `README.md`
4. Run multi-architecture build
5. Create GitHub release with DMG assets
6. Update release notes

## 💡 Development Tips

- Use `poetry` for dependency management
- Test on both Intel and Apple Silicon if possible
- Keep the main.py monolithic for simplicity
- Preserve YAML structure in file operations
- Test with real Espanso configurations
