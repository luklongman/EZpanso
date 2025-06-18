#!/usr/bin/env python3
"""
Test script to check if ruamel.yaml can be installed and used under Rosetta emulation.
"""

import tempfile
import os
import subprocess
import sys
import shutil
import platform

def main():
    print(f"Testing ruamel.yaml installation under x86_64 emulation")
    print(f"Current architecture: {platform.machine()}")
    
    # Create a temporary directory for testing
    temp_dir = tempfile.mkdtemp()
    venv_path = os.path.join(temp_dir, 'test_venv')
    
    print(f'Creating test venv in: {venv_path}')
    
    try:
        # Create virtual environment under x86_64
        subprocess.run([sys.executable, '-m', 'venv', venv_path], check=True)
        
        # Install ruamel.yaml in the venv
        pip_path = os.path.join(venv_path, 'bin', 'pip')
        python_path = os.path.join(venv_path, 'bin', 'python')
        
        print('Installing ruamel.yaml...')
        result = subprocess.run([pip_path, 'install', 'ruamel.yaml'], 
                               capture_output=True, text=True, timeout=120)
        
        if result.returncode == 0:
            print('✅ Installation SUCCESS')
            
            # Test import
            import_result = subprocess.run([python_path, '-c', 'import ruamel.yaml; print("Import SUCCESS")'], 
                                         capture_output=True, text=True)
            
            if import_result.returncode == 0:
                print(f'✅ {import_result.stdout.strip()}')
                
                # Test basic functionality
                func_test = subprocess.run([python_path, '-c', '''
import ruamel.yaml
from ruamel.yaml import YAML

yaml = YAML()
yaml.preserve_quotes = True

# Test data
test_data = {"matches": [{"trigger": ":test", "replace": "Hello World"}]}

# Test round-trip
import io
stream = io.StringIO()
yaml.dump(test_data, stream)
result = stream.getvalue()
print("Basic functionality test: SUCCESS")
print(f"Output preview: {result[:50]}...")
'''], capture_output=True, text=True)
                
                if func_test.returncode == 0:
                    print(f'✅ {func_test.stdout.strip()}')
                else:
                    print(f'❌ Functionality test failed: {func_test.stderr}')
            else:
                print(f'❌ Import test failed: {import_result.stderr}')
                
        else:
            print(f'❌ Installation FAILED: {result.stderr}')
            
    except subprocess.TimeoutExpired:
        print('❌ Installation timed out')
    except Exception as e:
        print(f'❌ Error: {e}')
    finally:
        # Cleanup
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
            print(f'Cleaned up temporary directory: {temp_dir}')

if __name__ == '__main__':
    main()
