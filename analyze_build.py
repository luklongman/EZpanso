#!/usr/bin/env python3
"""
Build size analyzer - Check what's taking up space in the final build
"""

import os
import subprocess
from pathlib import Path

def analyze_app_bundle():
    """Analyze the contents of the app bundle."""
    app_path = Path('dist/EZpanso.app')
    if not app_path.exists():
        print("❌ App bundle not found. Run build first.")
        return
    
    print("📊 EZpanso.app Build Analysis")
    print("=" * 50)
    
    # Get total size
    result = subprocess.run(['du', '-sh', str(app_path)], capture_output=True, text=True)
    if result.returncode == 0:
        total_size = result.stdout.strip().split('\t')[0]
        print(f"🎯 Total app size: {total_size}")
    
    print("\n📁 Largest components:")
    
    # Find largest directories
    result = subprocess.run(['du', '-sh', str(app_path / 'Contents' / '*')], 
                          capture_output=True, text=True, shell=True)
    if result.returncode == 0:
        lines = result.stdout.strip().split('\n')
        sizes = []
        for line in lines:
            if line.strip():
                size, path = line.split('\t', 1)
                component = os.path.basename(path)
                sizes.append((size, component))
        
        # Sort by size (rough approximation)
        sizes.sort(key=lambda x: float(x[0].replace('M', '').replace('K', '').replace('B', '')), reverse=True)
        
        for size, component in sizes[:10]:
            print(f"   {size:>8} - {component}")
    
    # Check for specific large files
    print("\n🔍 Large files (>1MB):")
    result = subprocess.run(['find', str(app_path), '-type', 'f', '-size', '+1M'], 
                          capture_output=True, text=True)
    if result.returncode == 0:
        large_files = result.stdout.strip().split('\n')
        for file_path in large_files[:10]:  # Show top 10
            if file_path.strip():
                rel_path = file_path.replace(str(app_path) + '/', '')
                size_result = subprocess.run(['du', '-sh', file_path], capture_output=True, text=True)
                if size_result.returncode == 0:
                    size = size_result.stdout.strip().split('\t')[0]
                    print(f"   {size:>8} - {rel_path}")

def compare_with_previous():
    """Compare with previous build if available."""
    old_dmg = 'EZpanso-1.1.0.dmg'
    if os.path.exists(old_dmg):
        result = subprocess.run(['du', '-sh', old_dmg], capture_output=True, text=True)
        if result.returncode == 0:
            old_size = result.stdout.strip().split('\t')[0]
            print(f"\n📈 Comparison:")
            print(f"   v1.1.0 DMG: {old_size}")
            
            # Current app size
            app_path = Path('dist/EZpanso.app')
            if app_path.exists():
                result = subprocess.run(['du', '-sh', str(app_path)], capture_output=True, text=True)
                if result.returncode == 0:
                    current_size = result.stdout.strip().split('\t')[0]
                    print(f"   v1.2.0 App: {current_size}")

def show_optimization_tips():
    """Show additional optimization tips."""
    print("\n💡 Additional Optimization Tips:")
    print("   1. Use architecture-specific builds instead of universal")
    print("   2. Excluded unused PyQt6 modules (already done)")
    print("   3. Removed Pillow dependency (already done)")
    print("   4. Enabled UPX compression (already done)")
    print("   5. Enabled binary stripping (already done)")
    print("   6. Consider using PyQt6-lite if available")
    print("   7. Use --onefile for even smaller distribution")

if __name__ == "__main__":
    analyze_app_bundle()
    compare_with_previous()
    show_optimization_tips()
