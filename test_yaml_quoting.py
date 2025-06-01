#!/usr/bin/env python3
"""
Test script to verify YAML quoting functionality in EZpanso
"""
import sys
import os
sys.path.append('/Users/longman/Documents/myCode/EZpanso')

from main import EZpanso

def test_yaml_quoting():
    """Test the YAML quoting functionality."""
    app = EZpanso()
    
    # Test cases for _needs_yaml_quoting
    test_cases = [
        # (input, expected_needs_quoting)
        ("simple text", False),
        ("text with \\n newline", True),
        ("text with \\t tab", True),
        ("text with actual\nnewline", True),
        ("text with actual\ttab", True),
        ("'starts with quote", True),
        ("\"starts with double quote", True),
        ("[starts with bracket", True),
        ("text with * asterisk", True),
        ("text with & ampersand", True),
        ("text with ! exclamation", True),
        ("text with % percent", True),
        ("text with # hash", True),
        ("text with ` backtick", True),
        ("text with @ at sign", True),
        ("normal email@domain.com", True),  # Contains @
        ("simple.text", False),
        ("", False),  # Empty string
    ]
    
    print("Testing _needs_yaml_quoting function:")
    for text, expected in test_cases:
        result = app._needs_yaml_quoting(text)
        status = "✓" if result == expected else "✗"
        print(f"{status} '{text}' -> {result} (expected {expected})")
    
    # Test cases for _format_yaml_value
    print("\nTesting _format_yaml_value function:")
    format_test_cases = [
        ("simple text", "simple text"),
        ("text with \\n", "'text with \\n'"),
        ("text with 'quote", "'text with ''quote'"),
        ("normal text", "normal text"),
        ("@special", "'@special'"),
    ]
    
    for text, expected in format_test_cases:
        result = app._format_yaml_value(text)
        status = "✓" if result == expected else "✗"
        print(f"{status} '{text}' -> '{result}' (expected '{expected}')")
    
    # Test cases for _get_display_value
    print("\nTesting _get_display_value function:")
    display_test_cases = [
        ("simple text", "simple text"),
        ("'quoted text'", "quoted text"),
        ("'text with ''quotes'''", "text with 'quotes'"),
        ("normal text", "normal text"),
    ]
    
    for text, expected in display_test_cases:
        result = app._get_display_value(text)
        status = "✓" if result == expected else "✗"
        print(f"{status} '{text}' -> '{result}' (expected '{expected}')")

if __name__ == "__main__":
    test_yaml_quoting()
