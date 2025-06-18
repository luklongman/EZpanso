#!/usr/bin/env python3
"""
Simple test to check ruamel.yaml availability under different architectures.
"""

import platform
import subprocess
import sys

print("=" * 50)
print("YAML Package Cross-Compilation Test")
print("=" * 50)

print(f"Current architecture: {platform.machine()}")

# Test 1: Check current environment
print("\n--- Test 1: Current Environment ---")
try:
    import yaml
    print("✅ PyYAML available")
except ImportError:
    print("❌ PyYAML not available")

try:
    import ruamel.yaml
    print("✅ ruamel.yaml available")
except ImportError:
    print("❌ ruamel.yaml not available")

# Test 2: Check under Rosetta
print("\n--- Test 2: Under Rosetta (x86_64) ---")
try:
    result = subprocess.run([
        'arch', '-x86_64', 'python3', '-c', 
        '''
import platform
print(f"Arch: {platform.machine()}")

try:
    import yaml
    print("PyYAML: ✅")
except ImportError:
    print("PyYAML: ❌")

try:
    import ruamel.yaml
    print("ruamel.yaml: ✅")
except ImportError:
    print("ruamel.yaml: ❌")
'''
    ], capture_output=True, text=True, timeout=10)
    
    if result.returncode == 0:
        print(result.stdout.strip())
    else:
        print(f"Error: {result.stderr}")
        
except subprocess.TimeoutExpired:
    print("❌ Test timed out")
except Exception as e:
    print(f"❌ Error: {e}")

print("\n--- Conclusion ---")
print("Based on this test, we can determine the correct dependency strategy.")
