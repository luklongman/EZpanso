# !/usr/bin/env python3

# CONSOLIDATION PLAN

"""
Reorganization plan for EZpanso tests folder.

Current naming: test_*and debug_*
Proposed naming: *_test.py and*_debug.py

===================

## Core Test Files (keep these)

1. main_test.py (from test_main.py) - 795 lines - Primary test suite
2. cross_platform_test.py (from test_cross_platform.py) - 418 lines - Platform tests
3. yaml_handler_test.py (consolidate yaml-related tests) - ~600 lines
4. bug_fixes_test.py (consolidate bug-specific tests) - ~300 lines

## Files to MERGE

==================

### Into yaml_handler_test.py

- test_comment_preservation.py (235 lines)
- test_complete.py (91 lines)
- test_yaml_saving.py (105 lines)
- test_ezpanso_implementation.py (216 lines) - workflow with YAML
Total: ~650 lines

### Into bug_fixes_test.py

- test_bug_fixes.py (89 lines)
- test_inplace_editing_fix.py (164 lines)
- test_real_file.py (160 lines) - real file edge cases
Total: ~415 lines

### REMOVE (redundant)

- test_comprehensive.py (408 lines) - overlaps with test_main.py

## Debug Files Consolidation

=============================

### Keep as utilities (rename with _debug.py suffix)

1. escape_debug.py (from debug_escape.py) - escape sequence testing
2. yaml_debug.py (merge debug_yaml_quotes.py + debug_quotes.py + debug_flow.py)
3. integration_debug.py (merge debug_integration.py + debug_gui.py + debug_file_loading.py)

## Final Structure

===================
tests/
├── README.md
├── __init__.py
├── main_test.py                    # Primary comprehensive test suite
├── cross_platform_test.py          # Platform-specific tests
├── yaml_handler_test.py            # All YAML-related functionality
├── bug_fixes_test.py               # Bug verification and edge cases
├── debug/
│   ├── __init__.py
│   ├── escape_debug.py             # Escape sequence debugging
│   ├── yaml_debug.py               # YAML parsing/formatting debugging
│   └── integration_debug.py        # GUI and integration debugging

## BENEFITS

=========
# CONSOLIDATION PLAN
1. Clearer naming convention (*_test.py,*_debug.py)
2. Reduced from 10 test files to 4 focused test files
3. Reduced from 7 debug files to 3 consolidated debug utilities
4. Eliminated redundancy (test_comprehensive.py overlaps test_main.py)
5. Better organization by functionality rather than historical development
6. Easier to run specific test categories
7. Reduced maintenance overhead

## IMPLEMENTATION

===============

1. Rename files following the new convention
2. Consolidate related functionality
3. Update imports and references
4. Update README.md with new structure
5. Update any CI/CD references
"""
