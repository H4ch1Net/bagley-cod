#!/usr/bin/env python3
"""
Simple test suite for Bagley orchestrator
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from skills.lab_orchestrator import LabManager


def test_create_lab():
    """Test basic lab creation"""
    manager = LabManager()
    result = manager.create_lab("test_user", "dvwa")
    assert "started successfully" in result
    assert "test_user" in list(manager.active_labs.values())[0].owner
    print("✅ test_create_lab passed")


def test_duplicate_prevention():
    """Test that duplicate labs are prevented"""
    manager = LabManager()
    manager.create_lab("test_user", "dvwa")
    result = manager.create_lab("test_user", "dvwa")
    assert "already have" in result
    print("✅ test_duplicate_prevention passed")


def test_invalid_lab_type():
    """Test handling of invalid lab types"""
    manager = LabManager()
    result = manager.create_lab("test_user", "invalid")
    assert "Unknown lab type" in result
    print("✅ test_invalid_lab_type passed")


def test_stop_lab():
    """Test stopping a lab"""
    manager = LabManager()
    manager.create_lab("test_user", "dvwa")
    result = manager.stop_lab("test_user", "dvwa")
    assert "stopped" in result
    print("✅ test_stop_lab passed")


def test_delete_lab():
    """Test deleting a lab"""
    manager = LabManager()
    manager.create_lab("test_user", "webgoat")
    result = manager.delete_lab("test_user", "webgoat")
    assert "deleted" in result
    assert len(manager.active_labs) == 0
    print("✅ test_delete_lab passed")


def test_status():
    """Test status reporting"""
    manager = LabManager()
    result = manager.get_status("test_user")
    assert "No active labs" in result
    
    manager.create_lab("test_user", "dvwa")
    result = manager.get_status("test_user")
    assert "Active Labs" in result
    print("✅ test_status passed")


def test_list_available():
    """Test listing available labs"""
    manager = LabManager()
    result = manager.list_available()
    assert "DVWA" in result
    assert "WEBGOAT" in result
    assert "METASPLOITABLE" in result
    assert "JUICE-SHOP" in result
    print("✅ test_list_available passed")


def run_all_tests():
    """Run all tests"""
    tests = [
        test_create_lab,
        test_duplicate_prevention,
        test_invalid_lab_type,
        test_stop_lab,
        test_delete_lab,
        test_status,
        test_list_available,
    ]
    
    print("🧪 Running Bagley tests...\n")
    failed = 0
    
    for test in tests:
        try:
            test()
        except AssertionError as e:
            print(f"❌ {test.__name__} failed: {e}")
            failed += 1
        except Exception as e:
            print(f"❌ {test.__name__} error: {e}")
            failed += 1
    
    print(f"\n{'='*50}")
    if failed == 0:
        print("🎉 All tests passed!")
        return 0
    else:
        print(f"💥 {failed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(run_all_tests())
