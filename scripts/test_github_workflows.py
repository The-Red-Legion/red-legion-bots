#!/usr/bin/env python3
"""
Test GitHub workflow files for correctness and completeness.
"""

import os
import yaml
import sys
from pathlib import Path

def test_github_workflows():
    """Test GitHub workflow configuration files."""
    print("🧪 Testing GitHub Workflows...")
    print("=" * 50)
    
    # Check workflows directory structure
    workflows_dir = Path(".github/workflows")
    if not workflows_dir.exists():
        print("❌ .github/workflows directory not found")
        return False
    
    required_workflows = [
        "test.yml",
        "deploy.yml",
        "merge.yml"
    ]
    
    print("📁 Checking required workflow files...")
    missing_workflows = []
    for workflow_file in required_workflows:
        workflow_path = workflows_dir / workflow_file
        if workflow_path.exists():
            print(f"  ✅ {workflow_file}")
        else:
            print(f"  ❌ {workflow_file} - MISSING")
            missing_workflows.append(workflow_file)
    
    if missing_workflows:
        print(f"\n❌ Missing workflows: {missing_workflows}")
        return False
    
    # Test YAML syntax for all workflow files
    print(f"\n🔍 Testing YAML syntax...")
    all_workflow_files = list(workflows_dir.glob("*.yml")) + list(workflows_dir.glob("*.yaml"))
    
    for workflow_path in all_workflow_files:
        try:
            with open(workflow_path, 'r') as f:
                yaml.safe_load(f)
            print(f"  ✅ {workflow_path.name}")
        except yaml.YAMLError as e:
            print(f"  ❌ {workflow_path.name} - YAML ERROR: {e}")
            return False
        except Exception as e:
            print(f"  ❌ {workflow_path.name} - ERROR: {e}")
            return False
    
    # Test test.yml for correct test references
    print(f"\n🔍 Validating test.yml workflow...")
    with open(workflows_dir / "test.yml", 'r') as f:
        test_workflow_content = f.read()
    
    # Check that it references existing test files
    existing_tests = [
        "test_validation.py",
        "test_database_v2.py", 
        "test_main.py",
        "test_command_sync.py",
        "test_uex_api.py",
        "test_channel_names.py",
        "test_redpricecheck.py"
    ]
    
    missing_test_refs = []
    for test_file in existing_tests:
        if test_file not in test_workflow_content:
            missing_test_refs.append(test_file)
        else:
            print(f"  ✅ References {test_file}")
    
    # Check that it doesn't reference archived tests
    archived_tests = [
        "test_advanced_system.py",
        "test_database_integration.py",
        "test_database_performance.py",
        "test_modular_system.py"
    ]
    
    bad_test_refs = []
    for test_file in archived_tests:
        if test_file in test_workflow_content:
            bad_test_refs.append(test_file)
            print(f"  ❌ Still references archived {test_file}")
        else:
            print(f"  ✅ No longer references archived {test_file}")
    
    if missing_test_refs:
        print(f"  ⚠️ Missing references to: {missing_test_refs}")
    
    if bad_test_refs:
        print(f"  ❌ Bad references to archived tests: {bad_test_refs}")
        return False
    
    # Check deploy.yml for correct structure
    print(f"\n🔍 Validating deploy.yml workflow...")
    with open(workflows_dir / "deploy.yml", 'r') as f:
        deploy_workflow_content = f.read()
    
    deploy_checks = [
        ("deploy", "✅ Uses correct 'deploy' label trigger"),
        ("Ready To Deploy", "✅ Checks for 'Ready To Deploy' label"),
        ("ansible", "✅ Uses Ansible for deployment"),
    ]
    
    for check_text, success_msg in deploy_checks:
        if check_text in deploy_workflow_content:
            print(f"  {success_msg}")
        else:
            print(f"  ⚠️ May need update: {check_text}")
    
    # Check for old references that should be cleaned up
    old_refs = ["participation_bot", "src.main"]
    old_refs_found = []
    
    for workflow_path in all_workflow_files:
        with open(workflow_path, 'r') as f:
            content = f.read()
        for old_ref in old_refs:
            if old_ref in content:
                old_refs_found.append(f"{workflow_path.name}:{old_ref}")
    
    if old_refs_found:
        print(f"\n⚠️ Found old references that may need updating:")
        for ref in old_refs_found:
            print(f"  - {ref}")
    else:
        print(f"\n✅ No old file references found")
    
    print(f"\n🎉 All GitHub workflow tests passed!")
    print("✅ Workflows are updated for new architecture")
    return True

if __name__ == "__main__":
    try:
        success = test_github_workflows()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"💥 Workflow test failed with error: {e}")
        sys.exit(1)