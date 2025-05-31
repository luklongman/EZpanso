"""
YAML Espanso Configuration Reader and Display Tool

This script reads espanso YAML configuration files and displays the text expansion 
matches in a clean tabular format. 

Features:
- Displays trigger and replacement text for each match
- Optional variable details display (hidden by default for cleaner output)
- Summary statistics including variable type counts
- Handles different types of espanso variables (date, random, shell)

Usage:
    python yaml-experiment-20250601.py

The script will read 'test.yml' and display matches with variables hidden by default.
To show variable details, modify the function call or use show_vars=True parameter.
"""

from tabulate import tabulate
import yaml

def read_yaml(filepath):
    """Reads a YAML file and returns its content as a Python dictionary."""
    try:
        with open(filepath, 'r') as file:
            data = yaml.safe_load(file)  # Use safe_load for security
        return data
    except FileNotFoundError:
        print(f"Error: File not found at {filepath}")
        return None
    except yaml.YAMLError as e:
        print(f"Error parsing YAML in {filepath}: {e}")
        return None

# Example usage:
yaml_data = read_yaml("test.yml")
# Uncomment the line below to print the raw YAML data
# if yaml_data:
#     print(yaml_data)


def format_variable(var):
    """Format a single variable for display."""
    var_name = var.get("name", "")
    var_type = var.get("type", "")
    params = var.get("params", {})
    
    if var_type == "random" and "choices" in params:
        choices = params["choices"]
        sample = choices[:3]  # Show first 3 choices
        return f"{var_name} ({var_type}): {', '.join(sample)}..."
    elif var_type == "date" and "format" in params:
        format_str = params["format"]
        return f"{var_name} ({var_type}): format='{format_str}'"
    elif var_type == "shell" and "cmd" in params:
        cmd = params["cmd"]
        return f"{var_name} ({var_type}): cmd='{cmd}'"
    else:
        return f"{var_name} ({var_type})"


def count_variable_types(matches):
    """Count variables by type."""
    var_types = {}
    for match in matches:
        if "vars" in match and match["vars"]:
            for var in match["vars"]:
                var_type = var.get("type", "unknown")
                var_types[var_type] = var_types.get(var_type, 0) + 1
    return var_types


def display_matches_table(yaml_data, match_key="matches", show_vars=False):
    """
    Presents key-value pairs from a specific section of the YAML data in a table format.
    
    Args:
        yaml_data: The parsed YAML data
        match_key: The key to look for in the YAML data (default: "matches")
        show_vars: Whether to show the variables column (default: False)
    """
    if not yaml_data or match_key not in yaml_data:
        print(f"No '{match_key}' section found in the YAML data.")
        return
    
    matches = yaml_data[match_key]
    
    if isinstance(matches, dict):
        # Simple key-value pairs
        table_data = list(matches.items())
        print(tabulate(table_data, headers=["Key", "Value"], tablefmt="grid"))
        return
    
    if not isinstance(matches, list):
        print(f"'{match_key}' in YAML is not a list or dictionary of matches.")
        return
    
    # Process matches list
    table_data = []
    for match in matches:
        row = {
            "Trigger": match.get("trigger", ""),
            "Replace": match.get("replace", "")
        }
        
        # Add vars column if requested
        if show_vars:
            if "vars" in match and match["vars"]:
                vars_info = [format_variable(var) for var in match["vars"]]
                row["Vars"] = "\n".join(vars_info)
            else:
                row["Vars"] = ""
        
        table_data.append(row)
    
    # Display results
    print(f"\nEspanso Text Expansion Matches in {match_key}:\n")
    print(tabulate(table_data, headers="keys", tablefmt="grid"))
    
    # Print summary statistics
    print(f"\nTotal matches: {len(table_data)}")
    
    matches_with_vars = sum(1 for match in matches if "vars" in match and match["vars"])
    if matches_with_vars > 0:
        print(f"Matches with variables: {matches_with_vars}")
        
        var_types = count_variable_types(matches)
        if var_types:
            print("\nVariable types:")
            for var_type, count in var_types.items():
                print(f"- {var_type}: {count}")
    
    if not show_vars and matches_with_vars > 0:
        print("\nNote: Use show_vars=True to see variable details.")

# Example usage (show basic table by default, or with variables):
if yaml_data:
    display_matches_table(yaml_data, match_key="matches")
    
    # Uncomment to show variables:
    # display_matches_table(yaml_data, match_key="matches", show_vars=True)