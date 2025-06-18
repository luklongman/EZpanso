# GitHub Copilot Instructions for EZpanso

## Project Overview

EZpanso is a modern GUI application for managing Espanso text expansion snippets built with PyQt6 and PyYAML. The application provides a user-friendly interface for editing, creating, and managing YAML-based text expansion files.

## Python Coding Standards

This project follows **PEP 8** (Python Enhancement Proposal 8) as the primary coding standard, with the following specific guidelines:

### Code Style
- **Line Length**: Maximum 88 characters (Black formatter compatible)
- **Indentation**: 4 spaces (no tabs)
- **Quotes**: Double quotes for strings, single quotes for character literals
- **Import Organization**: Follow PEP 8 import order (standard library, third-party, local)
- **Naming Conventions**:
  - Classes: PascalCase (`EZpanso`, `FileData`)
  - Functions/Methods: snake_case (`_setup_ui`, `_load_yaml_files`)
  - Constants: UPPER_SNAKE_CASE (`MAX_UNDO_STEPS`)
  - Private methods: Leading underscore (`_internal_method`)

### Type Hints
- Use type hints for all function signatures and class attributes
- Import types from `typing` module when needed
- Use `Optional[T]` for nullable types
- Define type aliases for complex types (e.g., `FileData = Dict[str, List[Dict[str, Any]]]`)

### Documentation
- Use docstrings for all public methods and classes
- Follow Google-style docstrings format
- Include type information in docstrings when helpful
- Document complex algorithms and business logic
- Update `README.md` and `CHANGELOG.md` for significant changes
- Use `Context7` to reference PyQt6 and PyYAML documentation for specific methods and classes

### Error Handling
- Use specific exception types rather than bare `except:`
- Handle PyQt6-specific exceptions appropriately
- Provide meaningful error messages to users
- Log errors for debugging purposes

## Architecture Guidelines

### Single Responsibility Principle
- Each method should have a single, well-defined purpose
- Separate UI logic from business logic where possible
- Keep data manipulation separate from presentation

### PyQt6 Best Practices
- Use signals and slots for communication between components
- Implement proper event handling
- Follow Qt's parent-child object model
- Use Qt's built-in data types and structures when appropriate
- Always use `yaml.safe_load()` instead of `yaml.load()` for security
- Block signals during bulk UI updates to prevent cascading events
- Use `QSettings` for persistent application settings
- Implement proper resource cleanup in `closeEvent()`

### File Structure
- Keep the monolithic structure for simplicity
- Group related methods together
- Use clear section comments to organize code
- Maintain consistent indentation and spacing

## Dependencies and External Libraries

### Core Dependencies
- **PyQt6**: GUI framework - refer to official documentation for best practices
- **PyYAML**: YAML parsing and generation - ensure proper handling of special characters
- **Python Standard Library**: Use built-in modules when possible

### Development Dependencies
- **PyInstaller**: For building standalone applications
- **pytest**: For unit testing

## Code Quality Guidelines

### Testing
- Test files are located at `tests/`
- Write unit tests for critical business logic
- Mock external dependencies (file system, settings)
- Test edge cases and error conditions
- Maintain test coverage for core functionality

### Performance
- Use efficient data structures (lists, dicts) appropriately
- Avoid unnecessary file I/O operations
- Cache frequently accessed data
- Optimize UI updates to prevent blocking

### Security
- Validate user input before processing
- Sanitize file paths to prevent directory traversal
- Handle YAML parsing safely to prevent code injection
- Backup user data before making changes

## Specific Guidelines for EZpanso

### YAML Handling
- **Security**: Always use `yaml.safe_load()` instead of `yaml.load()` to prevent code injection
- Preserve original file structure and comments when possible
- Handle special characters (newlines, tabs) properly using escape sequences
- Validate YAML syntax before saving to prevent corruption
- Provide clear error messages for malformed files
- Use UTF-8 encoding for all file operations
- Implement atomic file writes (write to temp file, then rename) for data safety

### GUI Design
- Maintain consistent styling across components
- Use appropriate widget types for data input
- Implement keyboard shortcuts for common actions
- Provide visual feedback for user actions

### Data Management
- Track file modifications accurately
- Implement undo/redo functionality
- Handle concurrent file access gracefully
- Validate data integrity before operations

### Cross-Platform Compatibility
- Use cross-platform file path handling
- Test on multiple operating systems
- Handle platform-specific differences gracefully
- Use appropriate keyboard shortcuts for each platform

## Code Review Checklist

When reviewing code changes:

1. **Functionality**: Does the code work as intended?
2. **Style**: Does it follow PEP 8 and project conventions?
3. **Performance**: Are there any obvious performance issues?
4. **Security**: Are there any security vulnerabilities?
5. **Testing**: Are there adequate tests for the changes?
6. **Documentation**: Is the code properly documented?
7. **Compatibility**: Does it work across supported platforms?

## Common Patterns

### Error Handling Pattern
```python
try:
    # risky operation
    result = some_operation()
    return result
except SpecificException as e:
    # log error and provide user feedback
    self._show_error("Operation failed", str(e))
    return None
```

### PyQt6 Signal Connection Pattern
```python
# Connect signals in setup methods
self.widget.signal.connect(self._handler_method)

def _handler_method(self, *args):
    """Handle widget signal with proper error handling."""
    try:
        # handle the signal
        pass
    except Exception as e:
        self._handle_error(e)
```

### File Operation Pattern
```python
def _save_file(self, file_path: str, data: Any) -> bool:
    """Save data to file with proper error handling."""
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            # write data
            pass
        return True
    except (IOError, OSError) as e:
        self._show_error("Save failed", str(e))
        return False
```

## Development Workflow

1. **Before Making Changes**:
   - Read relevant documentation using Context7
   - Understand the existing code structure
   - Plan the changes to minimize impact

2. **During Development**:
   - Write tests for new functionality
   - Follow coding standards consistently
   - Test on multiple platforms if possible

3. **Before Committing**:
   - Run all tests
   - Check code style compliance
   - Update documentation if needed
   - Test the application manually

## Resources

- [PEP 8 Style Guide](https://peps.python.org/pep-0008/)
- [PyQt6 Documentation](https://doc.qt.io/qtforpython/)
- [PyYAML Documentation](https://pyyaml.org/wiki/PyYAMLDocumentation)
- [Python Type Hints](https://docs.python.org/3/library/typing.html)

## Notes for Copilot

- Always consider cross-platform compatibility
- Prioritize user experience and data safety
- Use Context7 to reference PyQt6 and PyYAML documentation
- Consider the monolithic architecture when suggesting changes
- Test suggestions thoroughly before implementation

Be concise and to-the-point in your responses. Avoid verbose explanations unless requested.

## Current Code Quality Assessment and Improvement Areas

### Strengths
- Clean separation of concerns with well-named helper methods
- Good use of PyQt6 signals and slots pattern
- Comprehensive undo/redo functionality
- Cross-platform keyboard shortcut handling
- Proper error handling with user-friendly dialogs
- Type annotations already present

### Areas for Improvement

#### 1. Method Length and Complexity
- Some methods like `_setup_ui()` and `_show_package_warning()` are quite long
- Consider breaking them into smaller, focused methods
- Extract inline CSS styling into constants or separate files

#### 2. Signal Blocking Best Practices
```python
# Current practice (good):
self.table.blockSignals(True)
# ... bulk updates ...
self.table.blockSignals(False)

# Consider adding try/finally for safety:
try:
    self.table.blockSignals(True)
    # ... bulk updates ...
finally:
    self.table.blockSignals(False)
```

#### 3. Resource Management
- Consider using context managers for file operations
- Implement proper cleanup in `closeEvent()`
- Add memory usage optimization for large YAML files

#### 4. Error Handling Enhancements
```python
# Consider more specific exception handling:
try:
    with open(file_path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
except yaml.YAMLError as e:
    self._show_error("YAML Error", f"Invalid YAML syntax: {e}")
except FileNotFoundError:
    self._show_error("File Error", f"File not found: {file_path}")
except PermissionError:
    self._show_error("Permission Error", f"Cannot access file: {file_path}")
```

#### 5. Performance Optimizations
- Cache frequently accessed settings
- Use `QTimer.singleShot()` for deferred UI updates
- Consider using `QStandardItemModel` for large datasets
- Implement lazy loading for file list population

#### 6. Code Organization Suggestions
- Extract CSS constants to a separate section
- Group related methods with clear section comments
- Consider splitting large methods into logical sub-methods
- Use dataclasses for complex data structures

#### 7. Testing Coverage
- Add unit tests for core business logic
- Mock file system operations in tests
- Test cross-platform functionality
- Add integration tests for complete workflows

#### 8. Documentation Improvements
- Add more detailed docstrings for complex methods
- Document expected file formats and structures
- Add examples in docstrings for key methods
- Document error conditions and return values

Be concise and to-the-point in your responses. Avoid verbose explanations unless requested.
