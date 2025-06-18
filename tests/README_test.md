# EZpanso Test Suite Documentation

## Overview

This document provides comprehensive information about the EZpanso test suite, including the test organization, naming conventions, and how to run different types of tests.

## Test Organization

The tests are organized with a consistent naming convention following the `*_test.py` pattern for test files and `*_debug.py` for debug utilities.

### Current Test Files Structure

```plaintext
tests/
├── core_tests.py (796 lines) - Primary test suite
├── bug_fixes_test.py (426 lines) - Bug verification & edge cases
├── cross_platform_test.py (419 lines) - Platform-specific tests
├── save_refresh_test.py (102 lines) - Table refresh tests
├── yaml_handler_test.py (300 lines) - All YAML functionality
├── yaml_simple_test.py (65 lines) - YAML availability tests
├── ruamel_install_test.py (121 lines) - Package installation tests
├── build_test.py (355 lines) - Build validation tests
├── pytest.ini - Test configuration
└── debug/
    ├── escape_debug.py (94 lines) - Escape sequence debugging
    ├── yaml_debug.py (175 lines) - YAML parsing/formatting debug
    └── integration_debug.py (~ lines) - GUI & integration debug
```

### Test Categories

The test suite covers the following categories:

1. **Core Application Tests**
   - `core_tests.py` - Comprehensive core application tests (38+ test cases)
   - `bug_fixes_test.py` - TSM errors, in-place editing fixes, and edge cases
   - `save_refresh_test.py` - Tests that table is properly refreshed after saving files

2. **YAML Handling Tests**
   - `yaml_handler_test.py` - Comment preservation, fallback behavior, and YAML processing
   - `yaml_simple_test.py` - Tests for PyYAML and ruamel.yaml across architectures

3. **Platform-specific Tests**
   - `cross_platform_test.py` - Tests for Windows, macOS, and Linux
   - `ruamel_install_test.py` - Tests ruamel.yaml installation on different architectures

4. **Build System Tests**
   - `build_test.py` - Tests PyInstaller specs and build configurations

5. **Debug Utilities**
   - `debug/escape_debug.py` - Escape sequence handling debug utilities
   - `debug/yaml_debug.py` - YAML parsing, formatting, and quoting debug utilities  
   - `debug/integration_debug.py` - GUI, file loading, and integration debug utilities

## Test Coverage Areas

The test suite covers the following functionality areas:

1. **Core Application Functionality**
   - Window initialization and UI components
   - Data structures and helper methods
   - File loading and processing
   - Table operations and signal handling
   - Undo/redo functionality

2. **YAML Processing**
   - Comment preservation
   - Fallback handling for different YAML libraries
   - File operations (read/write)
   - Escape sequence handling
   - Special character processing

3. **Bug Fixes and Edge Cases**
   - TSM (Table Selection Model) errors
   - In-place editing issues
   - Cross-platform compatibility issues
   - Complex YAML structures
   - Escape sequence edge cases

4. **Platform Compatibility**
   - Cross-architecture support (ARM64, x86_64)
   - OS-specific features (Windows, macOS, Linux)
   - Keyboard shortcuts and platform detection
   - File path handling
   - Architecture-specific package installation

5. **Build and Distribution**
   - PyInstaller configuration validation
   - Build artifact verification
   - Package dependencies
   - Cross-platform builds

## Running Tests

### Run All Tests

```bash
pytest tests/
```

### Run Specific Tests by Category

```bash
# Core application tests
pytest tests/core_tests.py

# Bug fixes and edge cases
pytest tests/bug_fixes_test.py

# YAML handling
pytest tests/yaml_handler_test.py

# Cross-platform compatibility
pytest tests/cross_platform_test.py

# Build system tests
pytest tests/build_test.py
```

### Run Specific Test Functions

```bash
# Run a specific test class
pytest tests/core_tests.py::TestUIComponents

# Run a specific test function
pytest tests/core_tests.py::TestUIComponents::test_setup_ui
```

### Run Debug Utilities

```bash
# Test escape sequence handling
python tests/debug/escape_debug.py

# Debug YAML processing
python tests/debug/yaml_debug.py

# Debug GUI and integration
python tests/debug/integration_debug.py
```

### Run Tests with Verbose Output

```bash
python -m pytest tests/ -v
```

## Test Reorganization History

### Previous Organization Issues

Prior to the reorganization, the test structure had several issues:

1. **Inconsistent naming** - Mix of `test_*.py` and other naming conventions
2. **Redundant tests** - Overlapping test functionality
3. **Fragmented coverage** - Related tests spread across multiple files
4. **Excessive debug files** - Too many specialized debug utilities
5. **Poor documentation** - Lack of clear guidance on test purpose and usage

### Reorganization Benefits

The current test organization provides several benefits:

1. **Consistent naming convention** - All test files follow `*_test.py` format
2. **Logical categorization** - Tests grouped by purpose
3. **Simplified structure** - Flat directory makes tests easier to find and run
4. **Comprehensive documentation** - Clear guidance on test purpose and usage
5. **Maintainable approach** - Easy to add new tests following established pattern
6. **Reduced Maintenance** - Fewer files to update and maintain
7. **Better Testing Workflow** - Clear categories for different types of testing
8. **Eliminated Redundancy** - No overlapping or duplicate test coverage

## Best Practices for Adding New Tests

1. **Follow naming convention** - Use `*_test.py` for test files and `*_debug.py` for debug utilities
2. **Use appropriate category** - Add tests to the appropriate file based on what they test
3. **Include docstrings** - Document what the test is verifying
4. **Use pytest fixtures** - Leverage existing fixtures for UI components, mocks, etc.
5. **Handle cross-platform issues** - Consider differences between Windows, macOS, and Linux
6. **Test both success and failure cases** - Ensure robustness against errors
7. **Maintain established structure** - Keep the flat directory organization

## Test Dependencies

- **pytest** - Primary testing framework
- **PyQt6** - Required for UI component testing
- **PyYAML/ruamel.yaml** - Required for YAML processing tests
- **unittest.mock** - Used for mocking components

## Future Recommendations

1. **Add test coverage measurement** to identify untested parts of the codebase
2. **Add type hints** to test functions for better code assistance
3. **Maintain the established naming convention** for all future tests
4. **Document test dependencies** in requirements-dev.txt or a similar file
5. **If tests grow significantly**, consider a well-documented category-based directory structure
