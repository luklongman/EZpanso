# Contributing to EZpanso

Thank you for your interest in contributing to EZpanso! This document provides guidelines for contributing to the project.

## 🚀 Quick Start

1. **Fork** the repository on GitHub
2. **Clone** your fork locally
3. **Create** a new branch for your feature/fix
4. **Make** your changes
5. **Test** your changes thoroughly
6. **Submit** a pull request

## 🛠️ Development Setup

### Prerequisites
- Python 3.11+
- Poetry (recommended) or pip

### Setup
```bash
git clone https://github.com/yourusername/EZpanso.git
cd EZpanso
poetry install
```

### Running the App
```bash
poetry run python main.py
```

## 📝 Coding Guidelines

### Code Style
- Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) style guidelines
- Use meaningful variable and function names
- Add docstrings for classes and functions
- Keep functions small and focused

### Code Structure
- Main application logic in `main.py`
- Keep the single-file architecture for simplicity
- Use Qt best practices for GUI components

## 🧪 Testing

### Manual Testing
Before submitting a PR, please test:
- App startup and file loading
- Creating, editing, and deleting snippets
- Saving changes to YAML files
- Keyboard shortcuts
- Error handling

### Test Files
If you add new features, consider adding test YAML files to verify functionality.

## 🐛 Bug Reports

When reporting bugs, please include:
- **Environment**: OS, Python version, PyQt6 version
- **Steps to reproduce** the issue
- **Expected behavior** vs actual behavior
- **Error messages** (if any)
- **Sample YAML files** that trigger the issue (if applicable)

## ✨ Feature Requests

When requesting features:
- Explain the **use case** and **problem** it solves
- Provide **examples** of how it would work
- Consider **backwards compatibility**
- Keep the **simplicity** principle in mind

## 📦 Platform-Specific Considerations

### macOS
- Test app bundle creation with `./build_macos.sh`
- Verify icon display and app signing

### Linux
- Test with different desktop environments
- Check file path handling

### Windows
- Test path separators and encoding
- Verify PyInstaller builds (when available)

## 🔄 Pull Request Process

1. **Branch naming**: Use descriptive names like `feature/add-dark-mode` or `fix/duplicate-triggers`
2. **Commit messages**: Write clear, concise commit messages
3. **Description**: Explain what your PR does and why
4. **Testing**: Describe how you tested your changes
5. **Documentation**: Update README.md if needed

## 📋 Areas for Contribution

We welcome contributions in these areas:

### High Priority
- **Windows/Linux app bundling** - PyInstaller configs for other platforms
- **Dark mode support** - UI theming system
- **Unit tests** - Automated testing framework

### Medium Priority
- **Snippet templates** - Predefined snippet categories
- **Import/export** - Backup and restore functionality
- **Performance optimizations** - Large file handling

### Low Priority
- **Plugin system** - Extensibility for custom snippet types
- **Localization** - Multi-language support
- **Advanced search** - Regex and tag-based filtering

## 🤝 Code of Conduct

- Be respectful and inclusive
- Focus on constructive feedback
- Help others learn and grow
- Keep discussions on-topic

## 📞 Getting Help

- **Issues**: For bugs and feature requests
- **Discussions**: For questions and general discussion
- **Email**: For private matters

Thank you for contributing to EZpanso! 🎉
