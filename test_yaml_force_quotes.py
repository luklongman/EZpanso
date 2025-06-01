#!/usr/bin/env python3
import yaml

def test_force_double_quotes():
    """Test how to force PyYAML to always use double quotes."""
    
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
    
    print("Test 1: default_style='\"'")
    print("=" * 50)
    output1 = yaml.dump(test_data, sort_keys=False, allow_unicode=True, default_style='"')
    print(output1)
    
    print("\nTest 2: custom Dumper with forced double quotes")
    print("=" * 50)
    
    class DoubleQuotedDumper(yaml.SafeDumper):
        def represent_str(self, data):
            if '\n' in data or '\t' in data or data.startswith((':', '[', '{', '"', "'", '>', '|', '*', '&', '!', '%', '#', '`', '@')):
                return self.represent_scalar('tag:yaml.org,2002:str', data, style='"')
            return self.represent_scalar('tag:yaml.org,2002:str', data, style='"')
    
    DoubleQuotedDumper.add_representer(str, DoubleQuotedDumper.represent_str)
    
    output2 = yaml.dump(test_data, Dumper=DoubleQuotedDumper, sort_keys=False, allow_unicode=True)
    print(output2)
    
    print("\nTest 3: Force quotes for all strings")
    print("=" * 50)
    
    class ForceQuoteDumper(yaml.SafeDumper):
        def represent_str(self, data):
            # Always use double quotes for all strings
            return self.represent_scalar('tag:yaml.org,2002:str', data, style='"')
    
    ForceQuoteDumper.add_representer(str, ForceQuoteDumper.represent_str)
    
    output3 = yaml.dump(test_data, Dumper=ForceQuoteDumper, sort_keys=False, allow_unicode=True)
    print(output3)

if __name__ == "__main__":
    test_force_double_quotes()
