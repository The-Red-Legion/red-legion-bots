#!/usr/bin/env python3
"""
Fix test return statements to use proper assertions
"""
import re
import os

def fix_test_returns(file_path):
    """Fix return True/False statements in test functions"""
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Replace return True with assert True
    content = re.sub(r'(\s+)return True\s*$', r'\1assert True  # Test passed', content, flags=re.MULTILINE)
    
    # Replace return False with assert False + message
    content = re.sub(r'(\s+)return False\s*$', r'\1assert False, "Test failed"', content, flags=re.MULTILINE)
    
    with open(file_path, 'w') as f:
        f.write(content)
    
    print(f"Fixed {file_path}")

# Fix all test files
test_files = [
    'tests/test_validation.py',
    'tests/test_modular_system.py',
    'tests/test_advanced_system.py'
]

for test_file in test_files:
    if os.path.exists(test_file):
        fix_test_returns(test_file)
        print(f"✅ Fixed return statements in {test_file}")
    else:
        print(f"❌ File not found: {test_file}")
