#!/usr/bin/env python3
"""
EZpanso Project Cleanup Script

Cleans up temporary files, build artifacts, and other generated content
before creating a distribution build.
"""

import os
import shutil
import glob
from pathlib import Path


def remove_pycache():
    """Remove all __pycache__ directories recursively."""
    print("🧹 Removing __pycache__ directories...")
    for root, dirs, files in os.walk('.'):
        if '__pycache__' in dirs:
            pycache_path = os.path.join(root, '__pycache__')
            print(f"   Removing: {pycache_path}")
            shutil.rmtree(pycache_path)
            dirs.remove('__pycache__')


def remove_pyc_files():
    """Remove all .pyc files recursively."""
    print("🧹 Removing .pyc files...")
    pyc_files = glob.glob('**/*.pyc', recursive=True)
    for pyc_file in pyc_files:
        try:
            print(f"   Removing: {pyc_file}")
            os.remove(pyc_file)
        except (OSError, FileNotFoundError) as e:
            print(f"   Warning: Could not remove {pyc_file}: {e}")


def remove_build_artifacts():
    """Remove build and distribution artifacts."""
    print("🧹 Removing build artifacts...")
    artifacts = ['build/', 'dist/', '*.egg-info/']
    
    for pattern in artifacts:
        for item in glob.glob(pattern):
            if os.path.isdir(item):
                print(f"   Removing directory: {item}")
                shutil.rmtree(item)
            else:
                print(f"   Removing file: {item}")
                os.remove(item)


def remove_temp_files():
    """Remove temporary files and directories."""
    print("🧹 Removing temporary files...")
    temp_patterns = [
        '*.dmg',
        'dmg_temp*/',
        '.DS_Store',
        '**/.DS_Store',
        '*.tmp',
        '*.temp',
        'temp_*',
    ]
    
    for pattern in temp_patterns:
        for item in glob.glob(pattern, recursive=True):
            try:
                if os.path.isdir(item):
                    print(f"   Removing directory: {item}")
                    shutil.rmtree(item)
                else:
                    print(f"   Removing file: {item}")
                    os.remove(item)
            except (OSError, PermissionError) as e:
                print(f"   Warning: Could not remove {item}: {e}")


def remove_pytest_cache():
    """Remove pytest cache directories."""
    print("🧹 Removing pytest cache...")
    pytest_dirs = glob.glob('**/.pytest_cache', recursive=True)
    for pytest_dir in pytest_dirs:
        print(f"   Removing: {pytest_dir}")
        shutil.rmtree(pytest_dir)


def main():
    """Run all cleanup operations."""
    print("🚀 Starting EZpanso project cleanup...")
    
    # Change to script directory
    script_dir = Path(__file__).parent.parent
    os.chdir(script_dir)
    
    try:
        remove_pycache()
        remove_pyc_files()
        remove_build_artifacts()
        remove_temp_files()
        remove_pytest_cache()
        
        print("✅ Project cleanup completed successfully!")
        
    except Exception as e:
        print(f"❌ Cleanup failed: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
