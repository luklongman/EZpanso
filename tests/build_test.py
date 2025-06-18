#!/usr/bin/env python3
"""
EZpanso Build Testing Script

This script helps test and validate build configurations for different platforms.
It performs sanity checks on the build system and the resulting artifacts.
"""

import os
import sys
import subprocess
import shutil
import argparse
from typing import Dict, List, Tuple

# Import from build.py to reuse functionality
try:
    from build import (
        get_system_info, log_info, log_error, log_success, 
        log_warning, run_command
    )
except ImportError:
    print("Error: Could not import from build.py. Make sure you're in the correct directory.")
    sys.exit(1)

def check_spec_file(spec_path: str) -> Tuple[bool, List[str]]:
    """
    Check if a spec file is valid by verifying its syntax and structure.
    
    Args:
        spec_path: Path to the spec file
        
    Returns:
        Tuple of (is_valid, issues)
    """
    if not os.path.exists(spec_path):
        return False, [f"Spec file {spec_path} does not exist"]
    
    issues = []
    
    # Basic file read check
    try:
        with open(spec_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        return False, [f"Failed to read spec file: {e}"]
    
    # Check for essential PyInstaller components
    essential_components = ['Analysis', 'PYZ', 'EXE', 'COLLECT']
    for component in essential_components:
        if component not in content:
            issues.append(f"Missing essential component: {component}")
    
    # Check for platform-specific components
    if "BUNDLE" in content and not (sys.platform == 'darwin'):
        issues.append("Warning: BUNDLE directive is present but not on macOS")
    
    # Check for syntax errors by attempting to compile the spec file
    try:
        compile(content, spec_path, 'exec')
    except SyntaxError as e:
        issues.append(f"Syntax error in spec file: {e}")
        return False, issues
    
    # If no critical issues found, return True
    return len(issues) == 0, issues

def validate_build_artifacts(system_info: Dict, build_dir: str = "dist") -> Tuple[bool, List[str]]:
    """
    Validate that the expected build artifacts exist.
    
    Args:
        system_info: Dictionary with system information
        build_dir: Directory containing build artifacts
        
    Returns:
        Tuple of (is_valid, issues)
    """
    issues = []
    
    if not os.path.exists(build_dir):
        return False, [f"Build directory {build_dir} does not exist"]
    
    if system_info["is_macos"]:
        app_path = os.path.join(build_dir, "EZpanso.app")
        if not os.path.exists(app_path):
            issues.append(f"macOS app bundle not found: {app_path}")
        else:
            # Check for essential components in the app bundle
            exe_path = os.path.join(app_path, "Contents/MacOS/EZpanso")
            if not os.path.exists(exe_path):
                issues.append(f"Executable not found in app bundle: {exe_path}")
            
            # Check Info.plist
            info_plist = os.path.join(app_path, "Contents/Info.plist")
            if not os.path.exists(info_plist):
                issues.append(f"Info.plist not found: {info_plist}")
    
    elif system_info["is_windows"]:
        exe_path = os.path.join(build_dir, "EZpanso/EZpanso.exe")
        if not os.path.exists(exe_path):
            issues.append(f"Windows executable not found: {exe_path}")
    
    else:  # Linux
        bin_path = os.path.join(build_dir, "EZpanso/EZpanso")
        if not os.path.exists(bin_path):
            issues.append(f"Linux binary not found: {bin_path}")
    
    # Check if the build has the necessary dependencies
    return len(issues) == 0, issues

def test_build_process(spec_file: str, system_info: Dict) -> Tuple[bool, List[str]]:
    """
    Test the build process by running PyInstaller with the specified spec file.
    
    Args:
        spec_file: Path to the spec file
        system_info: Dictionary with system information
        
    Returns:
        Tuple of (success, issues)
    """
    issues = []
    
    # Validate spec file first
    spec_valid, spec_issues = check_spec_file(spec_file)
    if not spec_valid:
        return False, [f"Invalid spec file: {spec_file}"] + spec_issues
    
    # Clean build environment
    clean_dirs = ["build", "dist"]
    for dir_path in clean_dirs:
        if os.path.exists(dir_path):
            try:
                shutil.rmtree(dir_path)
                log_success(f"Cleaned {dir_path}/")
            except Exception as e:
                issues.append(f"Failed to clean {dir_path}: {e}")
    
    # Find PyInstaller
    pyinstaller_path = shutil.which("pyinstaller")
    if not pyinstaller_path:
        pyinstaller_path = shutil.which("pyinstaller3")
    
    if not pyinstaller_path:
        return False, ["PyInstaller not found in PATH"]
    
    # Run PyInstaller with the spec file
    log_info(f"Testing build with spec file: {spec_file}")
    cmd = [pyinstaller_path, "--clean", spec_file]
    log_info(f"Running command: {' '.join(cmd)}")
    
    exit_code, output = run_command(cmd)
    
    if exit_code != 0:
        issues.append(f"PyInstaller failed with exit code {exit_code}")
        issues.append(output)
        return False, issues
    
    # Validate the build artifacts
    artifacts_valid, artifact_issues = validate_build_artifacts(system_info)
    if not artifacts_valid:
        issues.extend(artifact_issues)
        return False, issues
    
    # If we get here, the build test was successful
    return True, issues

def run_smoke_test(system_info: Dict) -> Tuple[bool, List[str]]:
    """
    Run a basic smoke test on the built application.
    
    Args:
        system_info: Dictionary with system information
        
    Returns:
        Tuple of (success, issues)
    """
    issues = []
    
    if system_info["is_macos"]:
        app_path = "dist/EZpanso.app"
        if not os.path.exists(app_path):
            return False, [f"App bundle not found: {app_path}"]
        
        # Run the app and immediately kill it after a short delay
        cmd = ["open", app_path]
        log_info(f"Running smoke test: {' '.join(cmd)}")
        
        try:
            # Launch the app
            subprocess.Popen(cmd)
            
            # Wait a short time
            import time
            time.sleep(2)
            
            # Check if the process is running
            ps_cmd = ["pgrep", "-f", "EZpanso"]
            exit_code, output = run_command(ps_cmd)
            
            if exit_code != 0:
                issues.append("App did not start successfully")
            else:
                # Kill the process
                kill_cmd = ["pkill", "-f", "EZpanso"]
                run_command(kill_cmd)
        except Exception as e:
            issues.append(f"Smoke test failed: {e}")
            return False, issues
    
    elif system_info["is_windows"]:
        exe_path = "dist/EZpanso/EZpanso.exe"
        if not os.path.exists(exe_path):
            return False, [f"Executable not found: {exe_path}"]
        
        # On Windows, use a different approach to test
        # This is a placeholder - needs Windows-specific implementation
        log_warning("Windows smoke test not fully implemented")
        
    else:  # Linux
        bin_path = "dist/EZpanso/EZpanso"
        if not os.path.exists(bin_path):
            return False, [f"Binary not found: {bin_path}"]
        
        # On Linux, test launching the app (assuming X11/Wayland is available)
        cmd = [bin_path]
        log_info(f"Running smoke test: {' '.join(cmd)}")
        
        try:
            # Launch the app
            process = subprocess.Popen(cmd)
            
            # Wait a short time
            import time
            time.sleep(2)
            
            # Check if the process is still running
            if process.poll() is None:
                # Process is still running, terminate it
                process.terminate()
            else:
                # Process exited quickly, check exit code
                exit_code = process.returncode
                if exit_code != 0:
                    issues.append(f"App exited with code: {exit_code}")
        except Exception as e:
            issues.append(f"Smoke test failed: {e}")
            return False, issues
    
    return len(issues) == 0, issues

def main() -> int:
    """
    Main entry point for the build testing script.
    
    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    parser = argparse.ArgumentParser(description="EZpanso Build Testing Script")
    parser.add_argument("--spec", help="Test a specific spec file")
    parser.add_argument("--validate-only", action="store_true", help="Only validate spec files without building")
    parser.add_argument("--smoke-test", action="store_true", help="Run a smoke test on the built application")
    parser.add_argument("--all", action="store_true", help="Test all spec files for the current platform")
    
    args = parser.parse_args()
    
    # If no arguments provided, default to --all
    if not args.spec and not args.validate_only and not args.smoke_test and not args.all:
        args.all = True
    
    # Get system information
    system_info = get_system_info()
    
    log_info("Testing EZpanso build configuration")
    log_info(f"System: {system_info['system']} ({system_info['arch']})")
    log_info(f"Python: {system_info['python_version']}")
    
    success = True
    
    # Determine which spec files to test
    spec_files = []
    if args.spec:
        spec_files = [args.spec]
    elif args.all:
        # Get the appropriate spec file for the current platform
        if system_info["is_macos"]:
            if system_info["is_apple_silicon"]:
                spec_files = ["EZpanso-arm64.spec"]
            else:
                spec_files = ["EZpanso-intel.spec"]
        elif system_info["is_windows"]:
            spec_files = ["EZpanso-windows.spec"]
        else:  # Linux
            spec_files = ["EZpanso-linux.spec"]
    
    # Validate and optionally test each spec file
    for spec_file in spec_files:
        log_info(f"Testing spec file: {spec_file}")
        
        # Check if the spec file exists
        if not os.path.exists(spec_file):
            log_error(f"Spec file does not exist: {spec_file}")
            success = False
            continue
        
        # Validate the spec file
        valid, issues = check_spec_file(spec_file)
        if valid:
            log_success(f"Spec file validation passed: {spec_file}")
        else:
            log_error(f"Spec file validation failed: {spec_file}")
            for issue in issues:
                log_error(f"  - {issue}")
            success = False
        
        # If we're only validating, or if validation failed, skip the build test
        if args.validate_only or not valid:
            continue
        
        # Test the build process
        build_success, build_issues = test_build_process(spec_file, system_info)
        if build_success:
            log_success(f"Build test passed: {spec_file}")
        else:
            log_error(f"Build test failed: {spec_file}")
            for issue in build_issues:
                log_error(f"  - {issue}")
            success = False
    
    # Run smoke test if requested
    if args.smoke_test or args.all:
        if os.path.exists("dist"):
            smoke_success, smoke_issues = run_smoke_test(system_info)
            if smoke_success:
                log_success("Smoke test passed")
            else:
                log_error("Smoke test failed")
                for issue in smoke_issues:
                    log_error(f"  - {issue}")
                success = False
        else:
            log_warning("Skipping smoke test: No build artifacts found in dist/")
    
    # Final summary
    if success:
        log_success("All tests passed successfully!")
    else:
        log_error("One or more tests failed. See above for details.")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
