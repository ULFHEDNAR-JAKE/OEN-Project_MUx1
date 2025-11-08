#!/usr/bin/env python3
"""
Validation script for requirements.txt
This validates that the requirements file is properly formatted and contains expected packages.
"""

import re
import sys

def validate_requirements(file_path):
    """Validate requirements.txt file format and content"""
    
    print("=" * 60)
    print("Validating requirements.txt")
    print("=" * 60)
    print()
    
    expected_packages = {
        'Flask': '3.1.2',
        'Flask-SocketIO': '5.5.1',
        'Flask-SQLAlchemy': '3.1.1',
        'Flask-CORS': '6.0.1',
        'python-socketio': '5.14.3',
        'Werkzeug': '3.1.3',
        'requests': '2.32.5',
        'python-engineio': '4.12.3'
    }
    
    all_valid = True
    found_packages = {}
    
    try:
        with open(file_path, 'r') as f:
            lines = f.readlines()
        
        # Parse requirements
        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
            # Match package==version format
            match = re.match(r'^([a-zA-Z0-9_-]+)==([0-9.]+)$', line)
            if not match:
                print(f"✗ Line {line_num}: Invalid format: {line}")
                all_valid = False
                continue
            
            package_name = match.group(1)
            version = match.group(2)
            found_packages[package_name] = version
        
        # Verify all expected packages are present
        print("Package Verification:")
        print("-" * 60)
        for package, expected_version in expected_packages.items():
            if package in found_packages:
                actual_version = found_packages[package]
                if actual_version == expected_version:
                    print(f"✓ {package:25} {actual_version}")
                else:
                    print(f"✗ {package:25} {actual_version} (expected {expected_version})")
                    all_valid = False
            else:
                print(f"✗ {package:25} MISSING")
                all_valid = False
        
        # Check for unexpected packages
        extra_packages = set(found_packages.keys()) - set(expected_packages.keys())
        if extra_packages:
            print(f"\n⚠ Unexpected packages found: {', '.join(extra_packages)}")
        
        print()
        print("=" * 60)
        if all_valid:
            print("✓ Requirements file is valid!")
            return 0
        else:
            print("✗ Requirements file has issues")
            return 1
            
    except FileNotFoundError:
        print(f"✗ File not found: {file_path}")
        return 1
    except Exception as e:
        print(f"✗ Error reading file: {e}")
        return 1

if __name__ == '__main__':
    file_path = 'requirements.txt'
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
    
    sys.exit(validate_requirements(file_path))
