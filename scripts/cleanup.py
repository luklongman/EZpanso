#!/usr/bin/env python3
"""
Cleanup script to remove unnecessary files and optimize disk space usage.
Run this before building to reduce the overall project size.
"""

import os
import shutil
import glob
from pathlib import Path

def cleanup_pycache():
    """Remove all __pycache__ directories and .pyc files."""
    print("🧹 Removing __pycache__ directories...")
    for root, dirs, files in os.walk('.'):
        # Remove __pycache__ directories
        if '__pycache__' in dirs:
            cache_dir = os.path.join(root, '__pycache__')
            print(f"  Removing {cache_dir}")
            shutil.rmtree(cache_dir)
            dirs.remove('__pycache__')  # Don't traverse into removed directory
        
        # Remove .pyc files
        for file in files:
            if file.endswith('.pyc'):
                pyc_file = os.path.join(root, file)
                print(f"  Removing {pyc_file}")
                os.remove(pyc_file)

def cleanup_build_artifacts():
    """Remove build and dist directories."""
    print("🧹 Removing build artifacts...")
    artifacts = ['build', 'dist', '*.dmg']
    
    for artifact in artifacts:
        if '*' in artifact:
            # Handle glob patterns
            for file in glob.glob(artifact):
                print(f"  Removing {file}")
                if os.path.isdir(file):
                    shutil.rmtree(file)
                else:
                    os.remove(file)
        else:
            # Handle directory names
            if os.path.exists(artifact):
                print(f"  Removing {artifact}/")
                shutil.rmtree(artifact)

def cleanup_coverage_files():
    """Remove test coverage files."""
    print("🧹 Removing coverage files...")
    coverage_items = ['htmlcov', '.coverage', 'coverage.xml', '.pytest_cache']
    
    for item in coverage_items:
        if os.path.exists(item):
            print(f"  Removing {item}")
            if os.path.isdir(item):
                shutil.rmtree(item)
            else:
                os.remove(item)

def cleanup_macos_files():
    """Remove macOS system files."""
    print("🧹 Removing macOS system files...")
    for root, dirs, files in os.walk('.'):
        for file in files:
            if file == '.DS_Store':
                ds_file = os.path.join(root, file)
                print(f"  Removing {ds_file}")
                os.remove(ds_file)

def optimize_icon_set():
    """Keep only the necessary icon sizes."""
    print("🎨 Optimizing icon set...")
    icon_dir = Path('icon.iconset')
    if icon_dir.exists():
        # Keep only essential sizes: 16, 32, 128, 256, 512 (and their @2x versions)
        essential_icons = {
            'icon_16x16.png', 'icon_16x16@2x.png',
            'icon_32x32.png', 'icon_32x32@2x.png', 
            'icon_128x128.png', 'icon_128x128@2x.png',
            'icon_256x256.png', 'icon_256x256@2x.png',
            'icon_512x512.png', 'icon_512x512@2x.png'
        }
        
        for icon_file in icon_dir.iterdir():
            if icon_file.is_file() and icon_file.name not in essential_icons:
                print(f"  Removing unused icon: {icon_file}")
                icon_file.unlink()

def show_size_comparison():
    """Show directory sizes before and after cleanup."""
    total_size = 0
    for root, dirs, files in os.walk('.'):
        # Skip hidden directories and files
        dirs[:] = [d for d in dirs if not d.startswith('.')]
        
        for file in files:
            if not file.startswith('.'):
                file_path = os.path.join(root, file)
                try:
                    total_size += os.path.getsize(file_path)
                except (OSError, FileNotFoundError):
                    pass
    
    size_mb = total_size / (1024 * 1024)
    print(f"📊 Current project size: {size_mb:.1f} MB")

def main():
    """Run all cleanup operations."""
    print("🚀 Starting EZpanso project cleanup...")
    print()
    
    # Show initial size
    show_size_comparison()
    print()
    
    # Run cleanup operations
    cleanup_pycache()
    cleanup_build_artifacts()
    cleanup_coverage_files()
    cleanup_macos_files()
    optimize_icon_set()
    
    print()
    print("✅ Cleanup complete!")
    
    # Show final size
    show_size_comparison()
    print()
    print("💡 Tip: Run 'poetry install --no-dev' to skip development dependencies")
    print("📦 Ready for optimized build with: ./build_macos.sh")

if __name__ == "__main__":
    main()
