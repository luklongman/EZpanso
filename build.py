#!/usr/bin/env python3
"""
EZpanso Build Script

A simplified build script for EZpanso that builds only for Apple Silicon (ARM64) architecture.
For all other platforms, pip installation is recommended.
"""

import os
import sys
import subprocess
import platform
import shutil
import argparse
from typing import List, Optional, Tuple


# Configuration
APP_NAME = "EZpanso"
VERSION = "1.2.1"
# We only need the ARM64 spec file now
SPEC_FILE = "EZpanso-arm64.spec"

class Colors:
    """Terminal colors for output formatting."""
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_colored(text: str, color: str) -> None:
    """Print colored text to the terminal."""
    print(f"{color}{text}{Colors.END}")

def check_system() -> dict:
    """
    Check the system architecture and OS.
    
    Returns:
        Dictionary with system information
    """
    system = platform.system().lower()
    machine = platform.machine().lower()
    
    is_macos = system == "darwin"
    is_apple_silicon = is_macos and machine == "arm64"
    
    if not is_macos or not is_apple_silicon:
        print_colored(
            "Warning: This build script is now optimized only for Apple Silicon (ARM64).",
            Colors.YELLOW
        )
        print_colored(
            "For other platforms, please use pip installation: pip install ezpanso",
            Colors.YELLOW
        )
        if not is_macos:
            sys.exit(1)
    
    return {
        "is_macos": is_macos,
        "is_apple_silicon": is_apple_silicon,
        "system": system,
        "machine": machine
    }

def run_command(cmd: List[str], cwd: Optional[str] = None) -> Tuple[int, str, str]:
    """
    Run a command and return exit code, stdout, and stderr.
    
    Args:
        cmd: Command to run as a list of strings
        cwd: Working directory
        
    Returns:
        Tuple of (exit_code, stdout, stderr)
    """
    process = subprocess.Popen(
        cmd, 
        stdout=subprocess.PIPE, 
        stderr=subprocess.PIPE,
        cwd=cwd,
        text=True
    )
    stdout, stderr = process.communicate()
    return process.returncode, stdout, stderr

def check_pyinstaller() -> bool:
    """
    Check if PyInstaller is installed.
    
    Returns:
        True if PyInstaller is installed, False otherwise
    """
    return_code, _, _ = run_command(["pyinstaller", "--version"])
    return return_code == 0

def build_app() -> bool:
    """
    Build the application using PyInstaller.
    
    Returns:
        True if build was successful, False otherwise
    """
    print_colored(f"Building {APP_NAME} v{VERSION} for Apple Silicon...", Colors.BLUE)
    
    # Clean dist and build directories
    for directory in ["dist", "build"]:
        if os.path.exists(directory):
            shutil.rmtree(directory)
    
    # Build the app
    cmd = ["pyinstaller", SPEC_FILE]
    return_code, stdout, stderr = run_command(cmd)
    
    if return_code != 0:
        print_colored("Build failed:", Colors.RED)
        print(stderr)
        return False
    
    print_colored(f"{APP_NAME} build completed successfully!", Colors.GREEN)
    return True

def create_dmg() -> bool:
    """
    Create a DMG file for macOS distribution.
    
    Returns:
        True if DMG creation was successful, False otherwise
    """
    print_colored("Creating DMG...", Colors.BLUE)
    
    app_path = f"dist/{APP_NAME}.app"
    dmg_name = f"{APP_NAME}-{VERSION}-arm64.dmg"
    
    if not os.path.exists(app_path):
        print_colored(f"Error: {app_path} not found", Colors.RED)
        return False
        
    # Create DMG
    cmd = [
        "hdiutil", "create", 
        "-volname", APP_NAME, 
        "-srcfolder", app_path, 
        "-ov", "-format", "UDZO", 
        dmg_name
    ]
    
    return_code, stdout, stderr = run_command(cmd)
    
    if return_code != 0:
        print_colored("DMG creation failed:", Colors.RED)
        print(stderr)
        return False
    
    print_colored(f"DMG created: {dmg_name}", Colors.GREEN)
    return True

def main():
    """Main entry point for the build script."""
    parser = argparse.ArgumentParser(description=f'Build {APP_NAME} for Apple Silicon')
    parser.add_argument('--dmg', action='store_true', help='Create a DMG file after building')
    args = parser.parse_args()
    
    # Check system
    check_system()
    
    # Check PyInstaller
    if not check_pyinstaller():
        print_colored("PyInstaller not found. Please install it with:", Colors.RED)
        print("pip install pyinstaller")
        return 1
    
    # Build app
    if not build_app():
        return 1
    
    # Create DMG if requested
    if args.dmg:
        if not create_dmg():
            return 1
    
    print_colored(f"{APP_NAME} v{VERSION} build process completed successfully!", Colors.GREEN)
    print_colored("Find your app in the 'dist' directory.", Colors.BLUE)
    return 0

if __name__ == "__main__":
    sys.exit(main())
