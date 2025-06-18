# Test Configuration for EZpanso

This directory contains all tests for the EZpanso application following a standardized naming convention with `*_test.py` for tests and `*_debug.py` for debug utilities.

## Test Files

### Core Tests
- `main_test.py` - **Primary test suite** - Comprehensive core application tests (38 test cases)
- `cross_platform_test.py` - Cross-platform compatibility and keyboard shortcut tests
- `yaml_handler_test.py` - **YAML functionality** - Comment preservation, fallback behavior, and YAML processing
- `bug_fixes_test.py` - **Bug verification** - TSM errors, in-place editing fixes, and edge cases

### Debug Utilities
- `debug/escape_debug.py` - Escape sequence handling debug utilities
- `debug/yaml_debug.py` - YAML parsing, formatting, and quoting debug utilities  
- `debug/integration_debug.py` - GUI, file loading, and integration debug utilities

## Running Tests

### Run All Tests
```bash
pytest tests/
```

### Run Main Test Suite (Primary)
```bash
pytest tests/main_test.py -v
```

### Run Specific Test Categories
```bash
# Core functionality
pytest tests/main_test.py

# YAML handling
pytest tests/yaml_handler_test.py

# Bug fixes and edge cases
pytest tests/bug_fixes_test.py

# Cross-platform compatibility
pytest tests/cross_platform_test.py
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

## Test Structure

The test suite covers:
- **Core Application**: Window initialization, data structures, helper methods
- **YAML Handler**: Comment preservation, fallback behavior, file operations
- **Bug Fixes**: TSM error fixes, in-place editing fixes, data consistency
- **Cross-Platform**: Keyboard shortcuts, file paths, platform detection
- **Edge Cases**: Malformed YAML, complex structures, escape sequences

## File Organization

### Consolidated from Previous Structure:
- **Removed redundancy**: `test_comprehensive.py` overlapped with `main_test.py`
- **Merged related functionality**:
  - YAML tests: `test_comment_preservation.py` + `test_complete.py` + `test_yaml_saving.py` + `test_ezpanso_implementation.py` → `yaml_handler_test.py`
  - Bug tests: `test_bug_fixes.py` + `test_inplace_editing_fix.py` + `test_real_file.py` → `bug_fixes_test.py`
- **Standardized naming**: `test_*` → `*_test.py`, `debug_*` → `*_debug.py`
- **Consolidated debug utilities**: 7 debug files → 3 focused debug utilities

## Benefits of New Structure

1. **Clear naming convention** - Easier to identify test files vs debug utilities
2. **Reduced file count** - 10 test files → 4 focused test suites
3. **Better organization** - Tests grouped by functionality rather than historical development
4. **Eliminated redundancy** - No overlapping test coverage
5. **Easier maintenance** - Fewer files to update and maintain
6. **Focused testing** - Each file has a clear, specific purpose
- **Application Core**: Initialization, UI components, file loading
- **Data Operations**: Match detection, editing, saving, undo/redo
- **Cross-Platform**: Keyboard shortcuts, file paths, directory detection
- **Bug Fixes**: TSM errors, escape sequence handling, table synchronization
- **Real-World**: Integration with actual Espanso files

## Running Tests

From the project root directory:

```bash
# Run all tests
python -m pytest tests/

# Run specific test file
python -m pytest tests/test_main.py

# Run with verbose output
python -m pytest tests/ -v

# Run cross-platform tests specifically
python -m pytest tests/test_cross_platform.py
```

## Debug Scripts

The `debug/` directory contains various debugging utilities:

- `debug_escape.py` - Test escape sequence handling
- `debug_flow.py` - Debug application flow and logic
- `debug_integration.py` - Integration testing utilities
- `debug_quotes.py` - Debug quote handling in YAML
- `debug_yaml_quotes.py` - YAML quote parsing debugging

These can be run directly:

```bash
python tests/debug/debug_escape.py
```
