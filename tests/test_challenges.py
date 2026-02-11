#!/usr/bin/env python3
"""
Test suite for Bagley challenge and stats systems
"""

import sys
import os
import json
import tempfile
import shutil

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from skills.challenge_manager import ChallengeManager
from skills.stats_manager import StatsManager


# ── Challenge Manager Tests ─────────────────────────────────────

def test_challenges_loaded():
    """Test that challenges are loaded from disk"""
    cm = ChallengeManager()
    assert len(cm.challenges) > 0, "No challenges loaded"
    print(f"✅ test_challenges_loaded passed ({len(cm.challenges)} challenges)")


def test_list_categories():
    """Test listing challenge categories"""
    cm = ChallengeManager()
    cats = cm.list_categories()
    assert isinstance(cats, list)
    assert len(cats) > 0
    assert "cryptography" in cats
    print(f"✅ test_list_categories passed ({cats})")


def test_get_challenges_by_category():
    """Test filtering challenges by category"""
    cm = ChallengeManager()
    crypto = cm.get_challenges_by_category("cryptography")
    assert len(crypto) > 0
    for c in crypto:
        assert c.get("category") == "cryptography"
    print("✅ test_get_challenges_by_category passed")


def test_get_challenge_by_id():
    """Test fetching a specific challenge"""
    cm = ChallengeManager()
    challenge = cm.get_challenge("crypto-001")
    assert challenge is not None
    assert challenge["title"] == "Caesar's Secret"
    assert challenge["points"] == 100
    print("✅ test_get_challenge_by_id passed")


def test_get_challenge_not_found():
    """Test fetching a non-existent challenge"""
    cm = ChallengeManager()
    challenge = cm.get_challenge("nonexistent-999")
    assert challenge is None
    print("✅ test_get_challenge_not_found passed")


def test_check_flag_correct():
    """Test correct flag submission"""
    cm = ChallengeManager()
    assert cm.check_flag("crypto-001", "flag{the_quick_brown_fox_jumps_over_the_lazy_dog}") is True
    print("✅ test_check_flag_correct passed")


def test_check_flag_incorrect():
    """Test incorrect flag submission"""
    cm = ChallengeManager()
    assert cm.check_flag("crypto-001", "flag{wrong_answer}") is False
    print("✅ test_check_flag_incorrect passed")


def test_check_flag_whitespace():
    """Test flag with extra whitespace"""
    cm = ChallengeManager()
    assert cm.check_flag("crypto-001", "  flag{the_quick_brown_fox_jumps_over_the_lazy_dog}  ") is True
    print("✅ test_check_flag_whitespace passed")


def test_get_hint():
    """Test getting hints"""
    cm = ChallengeManager()
    hint0 = cm.get_hint("crypto-001", 0)
    assert hint0 is not None
    assert "shift" in hint0.lower() or "classic" in hint0.lower()

    hint2 = cm.get_hint("crypto-001", 2)
    assert hint2 is not None

    # Out of range hint
    hint_oor = cm.get_hint("crypto-001", 99)
    assert hint_oor is None
    print("✅ test_get_hint passed")


def test_format_challenge_list():
    """Test Discord formatting of challenge list"""
    cm = ChallengeManager()
    result = cm.format_challenge_list("cryptography")
    assert "Cryptography" in result
    assert "crypto-001" in result
    print("✅ test_format_challenge_list passed")


def test_format_challenge_list_empty():
    """Test formatting for non-existent category"""
    cm = ChallengeManager()
    result = cm.format_challenge_list("nonexistent")
    assert "No challenges found" in result
    print("✅ test_format_challenge_list_empty passed")


# ── Stats Manager Tests ─────────────────────────────────────────

def test_stats_record_solve():
    """Test recording a solve"""
    sm = StatsManager()
    # Use a temp stats file to avoid polluting real data
    sm.stats = {}
    sm.stats_file = tempfile.mktemp(suffix=".json")

    result = sm.record_solve("alice", "crypto-001", 100, "cryptography")
    assert result is True
    assert sm.stats["alice"]["total_points"] == 100
    assert len(sm.stats["alice"]["solves"]) == 1

    # Clean up
    if os.path.exists(sm.stats_file):
        os.remove(sm.stats_file)
    print("✅ test_stats_record_solve passed")


def test_stats_duplicate_solve():
    """Test that duplicate solves are rejected"""
    sm = StatsManager()
    sm.stats = {}
    sm.stats_file = tempfile.mktemp(suffix=".json")

    sm.record_solve("alice", "crypto-001", 100, "cryptography")
    result = sm.record_solve("alice", "crypto-001", 100, "cryptography")
    assert result is False
    assert sm.stats["alice"]["total_points"] == 100  # Not doubled

    if os.path.exists(sm.stats_file):
        os.remove(sm.stats_file)
    print("✅ test_stats_duplicate_solve passed")


def test_stats_multiple_solves():
    """Test recording multiple different solves"""
    sm = StatsManager()
    sm.stats = {}
    sm.stats_file = tempfile.mktemp(suffix=".json")

    sm.record_solve("alice", "crypto-001", 100, "cryptography")
    sm.record_solve("alice", "osint-001", 150, "osint")
    assert sm.stats["alice"]["total_points"] == 250
    assert len(sm.stats["alice"]["solves"]) == 2
    assert sm.stats["alice"]["categories"]["cryptography"] == 100
    assert sm.stats["alice"]["categories"]["osint"] == 150

    if os.path.exists(sm.stats_file):
        os.remove(sm.stats_file)
    print("✅ test_stats_multiple_solves passed")


def test_stats_lab_start():
    """Test recording lab starts"""
    sm = StatsManager()
    sm.stats = {}
    sm.stats_file = tempfile.mktemp(suffix=".json")

    sm.record_lab_start("alice")
    sm.record_lab_start("alice")
    assert sm.stats["alice"]["labs_started"] == 2

    if os.path.exists(sm.stats_file):
        os.remove(sm.stats_file)
    print("✅ test_stats_lab_start passed")


def test_leaderboard():
    """Test leaderboard generation"""
    sm = StatsManager()
    sm.stats = {}
    sm.stats_file = tempfile.mktemp(suffix=".json")

    sm.record_solve("alice", "crypto-001", 100, "cryptography")
    sm.record_solve("bob", "crypto-001", 100, "cryptography")
    sm.record_solve("bob", "osint-001", 150, "osint")

    leaders = sm.get_leaderboard(10)
    assert len(leaders) == 2
    assert leaders[0][0] == "bob"  # Bob has more points
    assert leaders[0][1]["total_points"] == 250
    assert leaders[1][0] == "alice"

    if os.path.exists(sm.stats_file):
        os.remove(sm.stats_file)
    print("✅ test_leaderboard passed")


def test_format_leaderboard():
    """Test Discord leaderboard formatting"""
    sm = StatsManager()
    sm.stats = {}
    sm.stats_file = tempfile.mktemp(suffix=".json")

    sm.record_solve("alice", "crypto-001", 100, "cryptography")
    result = sm.format_leaderboard()
    assert "alice" in result
    assert "100" in result

    if os.path.exists(sm.stats_file):
        os.remove(sm.stats_file)
    print("✅ test_format_leaderboard passed")


def test_format_leaderboard_empty():
    """Test leaderboard when empty"""
    sm = StatsManager()
    sm.stats = {}
    sm.stats_file = tempfile.mktemp(suffix=".json")

    result = sm.format_leaderboard()
    assert "No stats yet" in result

    if os.path.exists(sm.stats_file):
        os.remove(sm.stats_file)
    print("✅ test_format_leaderboard_empty passed")


def test_format_user_stats():
    """Test user stats formatting"""
    sm = StatsManager()
    sm.stats = {}
    sm.stats_file = tempfile.mktemp(suffix=".json")

    sm.record_solve("alice", "crypto-001", 100, "cryptography")
    sm.record_lab_start("alice")
    result = sm.format_user_stats("alice")
    assert "alice" in result
    assert "100" in result

    if os.path.exists(sm.stats_file):
        os.remove(sm.stats_file)
    print("✅ test_format_user_stats passed")


def test_format_user_stats_unknown():
    """Test stats for unknown user"""
    sm = StatsManager()
    sm.stats = {}
    sm.stats_file = tempfile.mktemp(suffix=".json")

    result = sm.format_user_stats("nobody")
    assert "No stats" in result

    if os.path.exists(sm.stats_file):
        os.remove(sm.stats_file)
    print("✅ test_format_user_stats_unknown passed")


# ── Runner ──────────────────────────────────────────────────────

def run_all_tests():
    """Run all tests"""
    tests = [
        # Challenge Manager
        test_challenges_loaded,
        test_list_categories,
        test_get_challenges_by_category,
        test_get_challenge_by_id,
        test_get_challenge_not_found,
        test_check_flag_correct,
        test_check_flag_incorrect,
        test_check_flag_whitespace,
        test_get_hint,
        test_format_challenge_list,
        test_format_challenge_list_empty,
        # Stats Manager
        test_stats_record_solve,
        test_stats_duplicate_solve,
        test_stats_multiple_solves,
        test_stats_lab_start,
        test_leaderboard,
        test_format_leaderboard,
        test_format_leaderboard_empty,
        test_format_user_stats,
        test_format_user_stats_unknown,
    ]

    print("🧪 Running Bagley challenge & stats tests...\n")
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
