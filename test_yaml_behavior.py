#!/usr/bin/env python3
import yaml

def test_yaml_behavior():
    """Test how PyYAML handles different strings automatically."""
    
    # Test data with various special characters
    test_data = {
        'matches': [
            {'trigger': ':simple', 'replace': 'simple text'},
            {'trigger': ':newline', 'replace': 'line1\nline2'},
            {'trigger': ':tab', 'replace': 'before\tafter'},
            {'trigger': ':special', 'replace': '[brackets] & symbols'},
            {'trigger': ':quotes', 'replace': 'text with "quotes"'},
            {'trigger': ':mixed', 'replace': 'multi\nline with "quotes" and [brackets]'},
        ]
    }
    
    print("Testing PyYAML automatic quoting behavior:")
    print("=" * 50)
    
    # Dump to YAML and see how it handles quoting
    yaml_output = yaml.dump(test_data, sort_keys=False, allow_unicode=True)
    print("YAML Output:")
    print(yaml_output)
    print("=" * 50)
    
    # Load it back and verify round-trip
    loaded_data = yaml.safe_load(yaml_output)
    print("Round-trip verification:")
    for original_match, loaded_match in zip(test_data['matches'], loaded_data['matches']):
        orig_trigger = original_match['trigger']
        orig_replace = original_match['replace']
        load_trigger = loaded_match['trigger'] 
        load_replace = loaded_match['replace']
        
        trigger_ok = orig_trigger == load_trigger
        replace_ok = orig_replace == load_replace
        
        print(f"Trigger: {repr(orig_trigger)} → {repr(load_trigger)} {'✓' if trigger_ok else '✗'}")
        print(f"Replace: {repr(orig_replace)} → {repr(load_replace)} {'✓' if replace_ok else '✗'}")
        print()

if __name__ == "__main__":
    test_yaml_behavior()
