#!/usr/bin/env python3
"""
Build and Release Script for EZpanso v1.2

This script automates the process of building the app, 
creating a DMG, and preparing a release.
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path
from datetime import datetime

# Configuration
VERSION = "1.2.0"
APP_NAME = "EZpanso"
DMG_NAME = f"{APP_NAME}-{VERSION}.dmg"

def run_command(command, description=None, exit_on_error=True):
    """Run a shell command and handle errors."""
    if description:
        print(f"🔄 {description}...")
    
    result = subprocess.run(command, capture_output=True, text=True, shell=True)
    
    if result.returncode != 0:
        print(f"❌ Error: {result.stderr}")
        if exit_on_error:
            sys.exit(1)
        return False
    
    return result.stdout.strip()

def check_environment():
    """Check if the environment is ready for building."""
    print("🔍 Checking environment...")
    
    # Check if pyinstaller is installed
    run_command("pip show pyinstaller", "Checking PyInstaller")
    
    # Check git status
    git_status = run_command("git status -s", "Checking git status")
    if git_status:
        print("⚠️  Warning: You have uncommitted changes:")
        print(git_status)
        response = input("Continue anyway? (y/n): ")
        if response.lower() != 'y':
            sys.exit(0)

def build_app():
    """Build the app using PyInstaller."""
    print("\n🏗️  Building application...")
    
    # Remove previous build if exists
    if os.path.exists("dist"):
        shutil.rmtree("dist")
    if os.path.exists("build"):
        shutil.rmtree("build")
    
    # Run PyInstaller
    build_cmd = "pyinstaller --windowed --name=EZpanso --icon=resources/icon.icns --clean main.py"
    run_command(build_cmd, "Running PyInstaller")
    
    # Check if build succeeded
    if not os.path.exists(f"dist/{APP_NAME}.app"):
        print("❌ Build failed!")
        sys.exit(1)
    
    print("✅ App built successfully")

def analyze_build():
    """Run the build analysis script."""
    print("\n📊 Analyzing build...")
    run_command("python analyze_build.py", "Analyzing build size")

def create_dmg():
    """Create a DMG file from the app."""
    print("\n📦 Creating DMG...")
    
    # Remove previous DMG if exists
    if os.path.exists(DMG_NAME):
        os.remove(DMG_NAME)
    
    # Create DMG
    dmg_cmd = f"hdiutil create -volname {APP_NAME} -srcfolder dist/{APP_NAME}.app -ov -format UDZO {DMG_NAME}"
    run_command(dmg_cmd, "Creating DMG")
    
    # Check if DMG was created
    if os.path.exists(DMG_NAME):
        size = run_command(f"du -h {DMG_NAME} | cut -f1", "Getting DMG size")
        print(f"✅ Created {DMG_NAME} ({size})")
    else:
        print("❌ Failed to create DMG")
        sys.exit(1)

def create_release_notes():
    """Create release notes for v1.2."""
    print("\n📝 Creating release notes...")
    
    notes_file = f"release_notes_v{VERSION}.md"
    with open(notes_file, "w") as f:
        f.write(f"# EZpanso v{VERSION} Release Notes\n\n")
        f.write(f"Released on: {datetime.now().strftime('%B %d, %Y')}\n\n")
        f.write("## What's New\n\n")
        f.write("- [Add key features and improvements here]\n\n")
        f.write("## Bug Fixes\n\n")
        f.write("- [Add bug fixes here]\n\n")
        f.write("## Known Issues\n\n")
        f.write("- [Add known issues here]\n\n")
    
    print(f"✅ Created {notes_file}")
    print("⚠️  Please edit the release notes with actual content before finalizing the release.")

def tag_release():
    """Tag the release in git."""
    print("\n🏷️  Tagging release...")
    
    tag_message = f"Release v{VERSION}"
    run_command(f'git tag -a "v{VERSION}" -m "{tag_message}"', "Creating git tag")
    
    print(f"✅ Created tag v{VERSION}")
    print("Note: You'll need to push the tag with 'git push origin v{VERSION}'")

def main():
    """Main function to build and release the app."""
    print(f"🚀 Building and releasing {APP_NAME} v{VERSION}")
    print("=" * 50)
    
    check_environment()
    build_app()
    analyze_build()
    create_dmg()
    create_release_notes()
    tag_release()
    
    print("\n🎉 Release preparation complete!")
    print(f"✅ App built: dist/{APP_NAME}.app")
    print(f"✅ DMG created: {DMG_NAME}")
    print(f"✅ Release notes created: release_notes_v{VERSION}.md")
    print(f"✅ Git tag created: v{VERSION}")
    print("\nNext steps:")
    print("1. Review and edit the release notes")
    print("2. Push the git tag: git push origin v{VERSION}")
    print("3. Upload the DMG to your release platform")

if __name__ == "__main__":
    main()
