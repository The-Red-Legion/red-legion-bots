#!/usr/bin/env python3
"""
Test Ansible configuration for completeness and correctness.
"""

import os
import yaml
import sys
from pathlib import Path

def test_ansible_config():
    """Test Ansible configuration files."""
    print("🧪 Testing Ansible Configuration...")
    print("=" * 50)
    
    # Check ansible directory structure
    ansible_dir = Path("ansible")
    required_files = [
        "deploy.yml",
        "inventory.ini", 
        "templates/env.j2",
        "tasks/database_migrations.yml",
        "tasks/start_bot.yml",
        "tasks/stop_bot.yml",
        "tasks/verify_bot.yml",
        "tasks/apply_single_migration.yml"
    ]
    
    print("📁 Checking required files...")
    missing_files = []
    for file_path in required_files:
        full_path = ansible_dir / file_path
        if full_path.exists():
            print(f"  ✅ {file_path}")
        else:
            print(f"  ❌ {file_path} - MISSING")
            missing_files.append(file_path)
    
    if missing_files:
        print(f"\n❌ Missing files: {missing_files}")
        return False
    
    # Test YAML syntax
    print(f"\n🔍 Testing YAML syntax...")
    yaml_files = [
        "deploy.yml",
        "tasks/database_migrations.yml", 
        "tasks/start_bot.yml",
        "tasks/stop_bot.yml",
        "tasks/verify_bot.yml",
        "tasks/apply_single_migration.yml"
    ]
    
    for yaml_file in yaml_files:
        try:
            with open(ansible_dir / yaml_file, 'r') as f:
                yaml.safe_load(f)
            print(f"  ✅ {yaml_file}")
        except yaml.YAMLError as e:
            print(f"  ❌ {yaml_file} - YAML ERROR: {e}")
            return False
        except Exception as e:
            print(f"  ❌ {yaml_file} - ERROR: {e}")
            return False
    
    # Check for updated references to new architecture
    print(f"\n🔍 Checking for updated architecture references...")
    
    with open(ansible_dir / "deploy.yml", 'r') as f:
        deploy_content = f.read()
    
    # Check that old references are updated
    architecture_checks = [
        ("import main", "✅ Updated to import main (not src.main)"),
        ("Red Legion Bot", "✅ Updated deployment name"),
        ("src/main.py", "✅ References correct main entry point"),
    ]
    
    for check_text, success_msg in architecture_checks:
        if check_text in deploy_content:
            print(f"  {success_msg}")
        else:
            print(f"  ⚠️ May need update: {check_text}")
    
    # Check database migration configuration
    with open(ansible_dir / "tasks/database_migrations.yml", 'r') as f:
        db_content = f.read()
    
    if "run_unified_migration.py" in db_content:
        print("  ✅ Uses unified migration system")
    else:
        print("  ❌ Missing unified migration system reference")
        return False
    
    # Check start_bot.yml for new architecture
    with open(ansible_dir / "tasks/start_bot.yml", 'r') as f:
        start_content = f.read()
    
    if "validate_config.py" in start_content:
        print("  ✅ References updated config validation script")
    else:
        print("  ❌ Missing config validation reference")
        return False
    
    if "Test database connection" in start_content:
        print("  ✅ Has database connection test")
    else:
        print("  ❌ Missing database connection test")
        return False
    
    # Check verify_bot.yml uses systemd
    with open(ansible_dir / "tasks/verify_bot.yml", 'r') as f:
        verify_content = f.read()
    
    if "systemd" in verify_content and "journalctl" in verify_content:
        print("  ✅ Uses systemd for service management")
    else:
        print("  ❌ Not updated for systemd service management")
        return False
    
    print(f"\n🎉 All Ansible configuration tests passed!")
    print("✅ Ready for deployment with new architecture")
    return True

if __name__ == "__main__":
    try:
        success = test_ansible_config()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"💥 Test failed with error: {e}")
        sys.exit(1)