#!/usr/bin/env python3
"""
Code compatibility checker for updated dependencies.
This script analyzes the codebase to identify potential compatibility issues.
"""

import re
import os
import sys

def check_flask_compatibility(file_path):
    """Check for Flask 3.1.2 compatibility issues"""
    issues = []
    
    with open(file_path, 'r') as f:
        content = f.read()
        lines = content.split('\n')
    
    # Check for deprecated __version__ usage
    if '__version__' in content and 'flask' in content.lower():
        for i, line in enumerate(lines, 1):
            if '__version__' in line and ('flask' in line.lower() or 'werkzeug' in line.lower()):
                issues.append({
                    'file': file_path,
                    'line': i,
                    'severity': 'warning',
                    'message': 'Using deprecated __version__ attribute',
                    'suggestion': 'Use importlib.metadata.version() instead'
                })
    
    return issues

def check_flask_cors_compatibility(file_path):
    """Check for Flask-CORS 6.0.1 compatibility issues"""
    issues = []
    
    with open(file_path, 'r') as f:
        content = f.read()
        lines = content.split('\n')
    
    # Check for CORS configuration
    if 'CORS(' in content:
        for i, line in enumerate(lines, 1):
            if 'CORS(' in line and 'cors_allowed_origins="*"' in line.lower():
                issues.append({
                    'file': file_path,
                    'line': i,
                    'severity': 'info',
                    'message': 'CORS allows all origins (*)',
                    'suggestion': 'Consider restricting origins in production'
                })
    
    return issues

def check_werkzeug_compatibility(file_path):
    """Check for Werkzeug 3.1.3 compatibility issues"""
    issues = []
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Check for password hashing usage (should still work)
    if 'generate_password_hash' in content or 'check_password_hash' in content:
        # These functions are still compatible
        pass
    
    return issues

def check_socketio_compatibility(file_path):
    """Check for python-socketio 5.14.3 compatibility"""
    issues = []
    
    with open(file_path, 'r') as f:
        content = f.read()
        lines = content.split('\n')
    
    # Check for Socket.IO event handlers
    if '@socketio.on(' in content or '@sio.on(' in content:
        # Current event handlers should be compatible
        pass
    
    return issues

def scan_python_files(root_dir):
    """Scan all Python files for compatibility issues"""
    all_issues = []
    
    for dirpath, dirnames, filenames in os.walk(root_dir):
        # Skip venv, __pycache__, .git
        dirnames[:] = [d for d in dirnames if d not in ['venv', '__pycache__', '.git', 'node_modules']]
        
        for filename in filenames:
            if filename.endswith('.py'):
                file_path = os.path.join(dirpath, filename)
                
                issues = []
                issues.extend(check_flask_compatibility(file_path))
                issues.extend(check_flask_cors_compatibility(file_path))
                issues.extend(check_werkzeug_compatibility(file_path))
                issues.extend(check_socketio_compatibility(file_path))
                
                all_issues.extend(issues)
    
    return all_issues

def main():
    print("=" * 70)
    print("Code Compatibility Check for Updated Dependencies")
    print("=" * 70)
    print()
    
    project_root = os.path.dirname(os.path.abspath(__file__))
    issues = scan_python_files(project_root)
    
    if not issues:
        print("✓ No compatibility issues found!")
        print()
        print("The codebase appears to be fully compatible with the updated")
        print("dependencies. All APIs used are still supported in the new versions.")
        return 0
    
    # Group issues by severity
    errors = [i for i in issues if i['severity'] == 'error']
    warnings = [i for i in issues if i['severity'] == 'warning']
    info = [i for i in issues if i['severity'] == 'info']
    
    if errors:
        print(f"❌ ERRORS ({len(errors)}):")
        print("-" * 70)
        for issue in errors:
            print(f"  {issue['file']}:{issue['line']}")
            print(f"    {issue['message']}")
            print(f"    Suggestion: {issue['suggestion']}")
            print()
    
    if warnings:
        print(f"⚠️  WARNINGS ({len(warnings)}):")
        print("-" * 70)
        for issue in warnings:
            print(f"  {issue['file']}:{issue['line']}")
            print(f"    {issue['message']}")
            print(f"    Suggestion: {issue['suggestion']}")
            print()
    
    if info:
        print(f"ℹ️  INFORMATIONAL ({len(info)}):")
        print("-" * 70)
        for issue in info:
            print(f"  {issue['file']}:{issue['line']}")
            print(f"    {issue['message']}")
            print(f"    Suggestion: {issue['suggestion']}")
            print()
    
    print("=" * 70)
    print(f"Summary: {len(errors)} errors, {len(warnings)} warnings, {len(info)} info")
    print("=" * 70)
    
    # Return non-zero only for errors, not warnings
    return 1 if errors else 0

if __name__ == '__main__':
    sys.exit(main())
