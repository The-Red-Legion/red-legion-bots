#!/usr/bin/env python3
"""
Test script to validate slash command fixes.
Checks if command names are now Discord-compliant.
"""

import re
import sys
from pathlib import Path

def check_command_names():
    """Check all command names for Discord compliance."""
    print("🔍 Checking all command names for Discord compliance...")
    
    # Discord command name rules
    def is_valid_name(name):
        # 1-32 characters, lowercase, letters/numbers/underscores only
        pattern = r'^[a-z][a-z0-9_]{0,31}$'
        return bool(re.match(pattern, name))
    
    command_files = []
    invalid_commands = []
    valid_commands = []
    
    # Find all Python files in commands directory
    commands_dir = Path('src/commands')
    for file_path in commands_dir.rglob('*.py'):
        command_files.append(file_path)
    
    print(f"📁 Found {len(command_files)} command files")
    
    # Extract command names from files
    for file_path in command_files:
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            
            # Find app_commands.command decorators
            command_pattern = r'@app_commands\.command\(name="([^"]+)"'
            matches = re.findall(command_pattern, content)
            
            for cmd_name in matches:
                if is_valid_name(cmd_name):
                    valid_commands.append((cmd_name, file_path.name))
                else:
                    invalid_commands.append((cmd_name, file_path.name))
            
            # Find Group names
            group_pattern = r'super\(\).__init__\(\s*name=["\']([^"\']+)["\']'
            group_matches = re.findall(group_pattern, content)
            
            for group_name in group_matches:
                if is_valid_name(group_name):
                    valid_commands.append((f"{group_name} (group)", file_path.name))
                else:
                    invalid_commands.append((f"{group_name} (group)", file_path.name))
        
        except Exception as e:
            print(f"⚠️ Error reading {file_path}: {e}")
    
    # Report results
    print(f"\n📊 RESULTS:")
    print(f"✅ Valid commands: {len(valid_commands)}")
    print(f"❌ Invalid commands: {len(invalid_commands)}")
    
    if invalid_commands:
        print(f"\n❌ INVALID COMMANDS FOUND:")
        for cmd_name, file_name in invalid_commands:
            print(f"  - '{cmd_name}' in {file_name}")
        return False
    
    if valid_commands:
        print(f"\n✅ ALL VALID COMMANDS:")
        for cmd_name, file_name in valid_commands:
            print(f"  - '{cmd_name}' in {file_name}")
    
    print(f"\n🎉 All command names are Discord-compliant!")
    return True

def check_command_structure():
    """Check command group registration structure."""
    print(f"\n🏗️ Checking command group registration structure...")
    
    subcommand_files = [
        'src/commands/events_subcommand.py',
        'src/commands/market_subcommand.py', 
        'src/commands/loans_subcommand.py',
        'src/commands/join_subcommand.py'
    ]
    
    issues = []
    
    for file_path in subcommand_files:
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            
            # Check for proper Cog class
            if 'commands.Cog' not in content:
                issues.append(f"{file_path}: Missing Cog class")
            
            # Check for proper group registration (class attribute)
            if 'commands.Cog' in content and 'Group()' not in content:
                issues.append(f"{file_path}: Missing proper group registration")
            
            # Check for proper setup function
            if 'await bot.add_cog(' not in content:
                issues.append(f"{file_path}: Missing proper cog registration in setup()")
        
        except FileNotFoundError:
            issues.append(f"{file_path}: File not found")
        except Exception as e:
            issues.append(f"{file_path}: Error reading file - {e}")
    
    if issues:
        print(f"❌ STRUCTURE ISSUES FOUND:")
        for issue in issues:
            print(f"  - {issue}")
        return False
    
    print(f"✅ All command group structures are correct!")
    return True

def main():
    """Main test function."""
    print("🧪 SLASH COMMAND VALIDATION TEST")
    print("=" * 50)
    
    names_valid = check_command_names()
    structure_valid = check_command_structure()
    
    print(f"\n" + "=" * 50)
    if names_valid and structure_valid:
        print("🎉 ALL TESTS PASSED!")
        print("✅ Command names are Discord-compliant")
        print("✅ Command group structures are correct")
        print("🚀 Ready for deployment!")
        return 0
    else:
        print("❌ TESTS FAILED!")
        if not names_valid:
            print("❌ Command names need fixes")
        if not structure_valid:
            print("❌ Command group structures need fixes")
        return 1

if __name__ == "__main__":
    sys.exit(main())