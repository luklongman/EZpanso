#!/usr/bin/env python3
"""
Demonstrate the difference between PyYAML and ruamel.yaml for comment preservation.

This script shows exactly what happens to comments during EZpanso's save operation.
"""

import tempfile
import os
import yaml

# Test with PyYAML (old behavior)
def test_pyyaml_behavior():
    """Test PyYAML behavior - loses comments."""
    print("=== PyYAML Behavior (OLD) ===")
    
    yaml_with_comments = """# Main comment
matches:
  # Comment about email
  - trigger: :email
    replace: user@example.com  # inline comment
  - trigger: :test
    replace: Hello World
"""
    
    print("Original YAML:")
    print(yaml_with_comments)
    
    # Load and save with PyYAML
    data = yaml.safe_load(yaml_with_comments)
    result = yaml.dump(data, sort_keys=False, allow_unicode=True, default_style=None)
    
    print("\nAfter PyYAML load/dump:")
    print(result)
    print("="*50)

# Test with ruamel.yaml (new behavior)
def test_ruamel_behavior():
    """Test ruamel.yaml behavior - preserves comments."""
    print("\n=== ruamel.yaml Behavior (NEW) ===")
    
    try:
        from ruamel.yaml import YAML
        yaml_handler = YAML()
        yaml_handler.preserve_quotes = True
        yaml_handler.map_indent = 2
        yaml_handler.sequence_indent = 4
        yaml_handler.sequence_dash_offset = 2
        
        yaml_with_comments = """# Main comment
matches:
  # Comment about email
  - trigger: :email
    replace: user@example.com  # inline comment
  - trigger: :test
    replace: Hello World
"""
        
        print("Original YAML:")
        print(yaml_with_comments)
        
        # Load and save with ruamel.yaml
        from io import StringIO
        data = yaml_handler.load(StringIO(yaml_with_comments))
        
        # Simulate editing
        if data and 'matches' in data:
            data['matches'][0]['replace'] = 'newemail@example.com'
        
        output = StringIO()
        yaml_handler.dump(data, output)
        result = output.getvalue()
        
        print("\nAfter ruamel.yaml load/edit/dump:")
        print(result)
        print("="*50)
        
    except ImportError:
        print("ruamel.yaml not available")

def test_real_espanso_file():
    """Test with actual Espanso file structure."""
    print("\n=== Real Espanso File Test ===")
    
    # This mimics the user's actual base.yml structure
    espanso_yaml = """# Comment in the head
matches:
- trigger: :~/
  replace: ✓
- trigger: :~=
  replace: ≈
- trigger: :cmd
  replace: ⌘
#adding random comment here
- trigger: :today
  replace: '{{mytoday}}'
  vars:
  - name: mytoday
    type: date
    params:
      format: '%b %d, %Y (%a)'
- trigger: :td
  replace: '{{mydate}}'
  vars: #adding another comment
  - name: mydate
    type: date
    params:
      format: '%Y%m%d'
"""
    
    print("Espanso-style YAML with comments:")
    print(espanso_yaml)
    
    # Test PyYAML
    print("\nPyYAML result (comments lost):")
    data = yaml.safe_load(espanso_yaml)
    pyyaml_result = yaml.dump(data, sort_keys=False, allow_unicode=True, default_style=None)
    print(pyyaml_result)
    
    # Test ruamel.yaml
    try:
        from ruamel.yaml import YAML
        yaml_handler = YAML()
        yaml_handler.preserve_quotes = True
        
        print("ruamel.yaml result (comments preserved):")
        from io import StringIO
        data = yaml_handler.load(StringIO(espanso_yaml))
        
        output = StringIO()
        yaml_handler.dump(data, output)
        ruamel_result = output.getvalue()
        print(ruamel_result)
        
    except ImportError:
        print("ruamel.yaml not available for this test")
    
    print("="*50)

def main():
    """Run all demonstration tests."""
    print("YAML Comment Preservation Demonstration")
    print("This shows the difference between PyYAML and ruamel.yaml")
    print("="*70)
    
    test_pyyaml_behavior()
    test_ruamel_behavior()
    test_real_espanso_file()
    
    print("\nSUMMARY:")
    print("- PyYAML: Fast but strips ALL comments")
    print("- ruamel.yaml: Slower but preserves comments and formatting")
    print("- EZpanso now uses ruamel.yaml when available")

if __name__ == "__main__":
    main()
