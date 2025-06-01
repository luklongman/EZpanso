#!/usr/bin/env python3

def test_format_yaml_value(value: str) -> str:
    """Format a value for YAML by wrapping with double quotes."""
    if not value:  # Don't quote empty strings
        return value
    # Escape any double quotes in the value and wrap with double quotes
    escaped_value = value.replace('"', '\\"')
    return f'"{escaped_value}"'

def test_get_display_value(value: str) -> str:
    """Get the display value for UI, removing quotes if they were added for YAML."""
    # If value is quoted with double quotes, remove them for display
    if (value.startswith('"') and value.endswith('"') and len(value) >= 2):
        # Unescape any escaped double quotes
        unquoted = value[1:-1].replace('\\"', '"')
        return unquoted
    return value

def test_quoting_logic():
    """Test the simplified quoting logic."""
    test_cases = [
        "",  # Empty string
        "simple",  # Simple string
        "multi\nline",  # String with newline
        "tab\there",  # String with tab
        'contains "quotes"',  # String with double quotes
        ":email",  # YAML special character at start
        "[test]",  # YAML special characters
        "normal text",  # Normal text
    ]
    
    print("Testing simplified YAML quoting logic:")
    print("=" * 50)
    
    for test_value in test_cases:
        formatted = test_format_yaml_value(test_value)
        display = test_get_display_value(formatted)
        
        print(f"Original: {repr(test_value)}")
        print(f"Formatted: {repr(formatted)}")
        print(f"Display: {repr(display)}")
        print(f"Round-trip OK: {test_value == display}")
        print("-" * 30)

if __name__ == "__main__":
    test_quoting_logic()
