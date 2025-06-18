#!/usr/bin/env python3
"""
YAML Debug Utilities for EZpanso.

Consolidates YAML parsing, formatting, and quoting debug utilities.
"""

import yaml
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

try:
    from yaml_handler import create_yaml_handler
    YAML_HANDLER_AVAILABLE = True
except ImportError:
    YAML_HANDLER_AVAILABLE = False

def test_yaml_quoting_behavior():
    """Test how YAML handles different quoting scenarios."""
    print("=== YAML Quoting Behavior Test ===\n")
    
    test_yaml = """
matches:
  - trigger: 'single_quoted'
    replace: content
  - trigger: "double_quoted"
    replace: content2
  - trigger: unquoted
    replace: content3
  - trigger: "quoted with spaces"
    replace: content4
  - trigger: 'quoted\\nwith\\nescapes'
    replace: content5
"""

    data = yaml.safe_load(test_yaml)
    print("YAML loaded data:")
    for i, match in enumerate(data['matches']):
        trigger = match['trigger']
        print(f"  Match {i}: trigger='{trigger}' (type: {type(trigger).__name__}, len: {len(trigger)})")
    
    print("\nYAML dump (default):")
    dumped = yaml.dump(data, sort_keys=False, allow_unicode=True)
    print(dumped)
    
    print("\nYAML dump (no quotes):")
    dumped_no_quotes = yaml.dump(data, sort_keys=False, allow_unicode=True, default_style=None)
    print(dumped_no_quotes)

def test_escape_sequences_in_yaml():
    """Test how YAML handles escape sequences."""
    print("\n=== YAML Escape Sequence Test ===\n")
    
    # Test data with escape sequences
    data = {
        'matches': [
            {'trigger': ':test', 'replace': 'Hello\\nWorld'},
            {'trigger': ':tab', 'replace': 'Col1\\tCol2'},
            {'trigger': ':mixed', 'replace': 'Line1\\nTab\\tHere'},
            {'trigger': ':literal', 'replace': 'Literal\\\\backslash'},
        ]
    }
    
    print("Original data:")
    for match in data['matches']:
        print(f"  {match['trigger']}: '{match['replace']}'")
    
    print("\nYAML dump:")
    dumped = yaml.dump(data, sort_keys=False, allow_unicode=True, default_style=None)
    print(dumped)
    
    print("Reloaded data:")
    reloaded = yaml.safe_load(dumped)
    for match in reloaded['matches']:
        print(f"  {match['trigger']}: '{match['replace']}' (repr: {repr(match['replace'])})")

def test_yaml_handler_behavior():
    """Test yaml_handler behavior vs standard PyYAML."""
    if not YAML_HANDLER_AVAILABLE:
        print("YAML handler not available, skipping test")
        return
    
    print("\n=== YAML Handler vs PyYAML Comparison ===\n")
    
    test_yaml = """# Comment
matches:
  - trigger: :test
    replace: |
      Multi-line
      content here
  - trigger: :simple
    replace: "simple value"
"""
    
    # Test with yaml_handler (comment preservation)
    handler_comments = create_yaml_handler(preserve_comments=True)
    handler_no_comments = create_yaml_handler(preserve_comments=False)
    
    print(f"Handler with comments: {handler_comments.backend}")
    print(f"Handler without comments: {handler_no_comments.backend}")
    print()
    
    # Parse with PyYAML
    pyyaml_data = yaml.safe_load(test_yaml)
    print("PyYAML parsed data:")
    print(f"Matches count: {len(pyyaml_data['matches'])}")
    for match in pyyaml_data['matches']:
        print(f"  {match['trigger']}: {repr(match['replace'])}")
    
    print("\nPyYAML dump:")
    pyyaml_dump = yaml.dump(pyyaml_data, sort_keys=False, allow_unicode=True, default_style=None)
    print(pyyaml_dump)

def test_data_flow():
    """Debug script to understand the data flow."""
    print("\n=== Data Flow Test ===\n")
    
    # Test how YAML handles quoted strings
    test_yaml = """
matches:
  - trigger: 'test'
    replace: content
  - trigger: test
    replace: content2
  - trigger: "test with spaces"
    replace: content3
"""

    data = yaml.safe_load(test_yaml)
    print("YAML loaded data:")
    for i, match in enumerate(data['matches']):
        print(f"  Match {i}: trigger='{match['trigger']}' (type: {type(match['trigger'])})")

    # Test escape sequence functions (if available)
    def _get_display_value(value: str) -> str:
        """Get the display value for UI, converting actual newlines/tabs to escape sequences."""
        if not isinstance(value, str):
            return str(value)
        # Convert actual newlines and tabs to escape sequences for display
        display_value = value.replace('\n', '\\n').replace('\t', '\\t')
        return display_value

    def _process_escape_sequences(value: str) -> str:
        """Convert escape sequences like \\n and \\t to actual characters."""
        if not isinstance(value, str):
            return str(value)
        # Convert escape sequences to actual characters
        processed_value = value.replace('\\n', '\n').replace('\\t', '\t')
        return processed_value

    print("\nEscape sequence testing:")
    test_values = [
        "Simple text",
        "Text with\\nnewlines",
        "Text with\\ttabs",
        "Mixed\\nand\\tescapes"
    ]
    
    for val in test_values:
        display = _get_display_value(val)
        processed = _process_escape_sequences(val)
        print(f"Original: '{val}'")
        print(f"Display:  '{display}'")
        print(f"Processed:'{processed}'")
        print()

if __name__ == '__main__':
    test_yaml_quoting_behavior()
    test_escape_sequences_in_yaml()
    test_yaml_handler_behavior()
    test_data_flow()
