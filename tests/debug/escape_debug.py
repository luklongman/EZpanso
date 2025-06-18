#!/usr/bin/env python3
"""
Escape Sequence Debug Utilities for EZpanso.

Debug utilities for testing escape sequence handling edge cases.
"""

def _process_escape_sequences_old(value: str) -> str:
    """Old version."""
    if not isinstance(value, str):
        return str(value)
    processed_value = value.replace('\\n', '\n').replace('\\t', '\t')
    return processed_value

def _process_escape_sequences_new(value: str) -> str:
    """New version with backslash handling."""
    if not isinstance(value, str):
        return str(value)
    # Handle literal backslashes first to avoid double processing
    processed_value = value.replace('\\\\', '\x00')  # Temporary placeholder
    processed_value = processed_value.replace('\\n', '\n').replace('\\t', '\t')
    processed_value = processed_value.replace('\x00', '\\')  # Restore literal backslashes
    return processed_value

def _get_display_value(value: str) -> str:
    """Get the display value for UI, converting actual newlines/tabs to escape sequences."""
    if not isinstance(value, str):
        return str(value)
    # First escape literal backslashes, then convert actual newlines/tabs to escape sequences
    display_value = value.replace('\\', '\\\\')  # Escape literal backslashes first
    display_value = display_value.replace('\n', '\\n').replace('\t', '\\t')
    return display_value

def test_escape_sequences():
    """Test escape sequence edge cases."""
    print("=== Testing Escape Sequence Functions ===\n")
    
    # Test cases that are problematic
    test_cases = [
        "Simple text",
        "Text\\nwith\\nnewlines", 
        "Text\\twith\\ttabs",
        "Mixed\\nand\\tescapes",
        "Literal\\\\backslash",
        "Complex\\\\n\\tcase",  # This should be: literal \, literal n, actual tab
        "",
        "\\n",
        "\\t", 
        "\\\\",
        "\\\\\\n",  # literal backslash + escaped newline
        "Path\\\\to\\\\file",  # Windows-style path
        "Quote: \\\"Hello\\\"",  # Escaped quotes
    ]
    
    print("Old vs New Implementation Comparison:")
    print("-" * 60)
    
    for test in test_cases:
        old_result = _process_escape_sequences_old(test)
        new_result = _process_escape_sequences_new(test)
        
        print(f"Input:  '{test}'")
        print(f"Old:    '{old_result}'")
        print(f"New:    '{new_result}'")
        print(f"Match:  {old_result == new_result}")
        print()
    
    print("\nDisplay Value Testing:")
    print("-" * 30)
    
    actual_values = [
        "Hello\nWorld",
        "Tab\tSeparated\tValues", 
        "Mixed\nand\ttypes",
        "Literal\\backslash",
        "",
        "\n",
        "\t",
        "\\",
    ]
    
    for actual in actual_values:
        display = _get_display_value(actual)
        processed_back = _process_escape_sequences_new(display)
        
        print(f"Actual:     '{repr(actual)}'")
        print(f"Display:    '{display}'")
        print(f"Processed:  '{repr(processed_back)}'")
        print(f"Round-trip: {actual == processed_back}")
        print()

if __name__ == '__main__':
    test_escape_sequences()
