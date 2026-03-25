"""
Integration test for interviewer matching against the real DB pool.

Run with:
    pytest tests/test_matching_pool.py -v
"""
import pytest
from db import get_interviewer_pool
from matching import find_best_matches


@pytest.fixture(scope="module")
def interviewer_pool():
    pool = get_interviewer_pool()
    print(f"\n--- Interviewer Pool ({len(pool)} candidates) ---")
    for i, p in enumerate(pool, 1):
        print(f"  [{i}] {p.get('first_name', '?')} | major: {p.get('major')} | exp: {p.get('experience_years')}y")
    if len(pool) == 0:
        pytest.fail("Interviewer pool is empty — seed at least one interviewer with a parsed CV before running this test.")
    return pool


def test_pool_has_at_least_one_candidate(interviewer_pool):
    assert len(interviewer_pool) >= 1


def test_matching_returns_between_1_and_3(interviewer_pool):
    requester = {"major": interviewer_pool[0]["major"]}  # guaranteed overlap
    matches = find_best_matches(requester, interviewer_pool)
    print(f"\n--- Matching Results for major '{requester['major']}' ({len(matches)} found) ---")
    for i, m in enumerate(matches, 1):
        print(f"  [{i}] {m.get('first_name', '?')} | major: {m.get('major')} | score: {m.get('match_score')}")
    assert 1 <= len(matches) <= 3


def test_matching_returns_no_ai_fallback(interviewer_pool):
    requester = {"major": interviewer_pool[0]["major"]}
    matches = find_best_matches(requester, interviewer_pool)
    assert all(not m.get("is_ai") for m in matches)


def test_matching_results_have_required_fields(interviewer_pool):
    requester = {"major": interviewer_pool[0]["major"]}
    matches = find_best_matches(requester, interviewer_pool)
    for m in matches:
        assert "id" in m
        assert "email" in m
