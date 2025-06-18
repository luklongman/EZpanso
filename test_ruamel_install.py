#!/usr/bin/env python3
"""
Test ruamel.yaml installation on both architectures.
"""

import subprocess
import platform
import tempfile
import os
import shutil

def test_installation(arch_name, arch_prefix=[]):
    """Test ruamel.yaml installation for a specific architecture."""
    print(f"\n--- Testing {arch_name} Installation ---")
    
    # Create temporary venv
    temp_dir = tempfile.mkdtemp()
    venv_path = os.path.join(temp_dir, f'venv_{arch_name.lower()}')
    
    try:
        # Create venv
        cmd = arch_prefix + ['python3', '-m', 'venv', venv_path]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode != 0:
            print(f"❌ Failed to create venv: {result.stderr}")
            return False
            
        # Install ruamel.yaml
        pip_path = os.path.join(venv_path, 'bin', 'pip')
        python_path = os.path.join(venv_path, 'bin', 'python')
        
        print(f"Installing ruamel.yaml in {arch_name} environment...")
        install_cmd = [pip_path, 'install', 'ruamel.yaml']
        result = subprocess.run(install_cmd, capture_output=True, text=True, timeout=120)
        
        if result.returncode == 0:
            print("✅ Installation successful")
            
            # Test import and basic functionality
            test_code = '''
import platform
print(f"Python arch: {platform.machine()}")

import ruamel.yaml
from ruamel.yaml import YAML

yaml = YAML()
yaml.preserve_quotes = True
yaml.map_indent = 2

# Test basic functionality
data = {"test": "value", "matches": [{"trigger": ":hello", "replace": "world"}]}
import io
stream = io.StringIO()
yaml.dump(data, stream)
result = stream.getvalue()
print("✅ Basic YAML operations successful")
print(f"Sample output: {result.split()[0]}...")
'''
            
            test_result = subprocess.run([python_path, '-c', test_code], 
                                       capture_output=True, text=True, timeout=30)
            
            if test_result.returncode == 0:
                print(test_result.stdout.strip())
                return True
            else:
                print(f"❌ Functionality test failed: {test_result.stderr}")
                return False
        else:
            print(f"❌ Installation failed: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ Operation timed out")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    finally:
        # Cleanup
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)

def main():
    print("=" * 60)
    print("ruamel.yaml Cross-Architecture Installation Test")
    print("=" * 60)
    
    print(f"Host architecture: {platform.machine()}")
    
    # Test native architecture
    native_success = test_installation("Native (arm64)", [])
    
    # Test x86_64 under Rosetta
    rosetta_success = test_installation("Rosetta (x86_64)", ["arch", "-x86_64"])
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Native (arm64):     {'✅ SUCCESS' if native_success else '❌ FAILED'}")
    print(f"Rosetta (x86_64):   {'✅ SUCCESS' if rosetta_success else '❌ FAILED'}")
    
    if native_success and rosetta_success:
        print("\n🎉 CONCLUSION: ruamel.yaml works on BOTH architectures!")
        print("   The original assumption was incorrect.")
        print("   Both Intel and Apple Silicon builds CAN have comment preservation.")
    elif native_success and not rosetta_success:
        print("\n📊 CONCLUSION: Original assumption was CORRECT.")
        print("   Apple Silicon: Full features (ruamel.yaml)")
        print("   Intel: Limited features (PyYAML only)")
    elif not native_success and rosetta_success:
        print("\n🔄 CONCLUSION: Opposite of original assumption!")
        print("   Intel works better than Apple Silicon for ruamel.yaml")
    else:
        print("\n❌ CONCLUSION: ruamel.yaml installation issues on both architectures")

if __name__ == '__main__':
    main()
