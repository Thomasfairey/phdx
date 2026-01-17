#!/usr/bin/env python3
"""
Test script for the LLM Gateway (Intelligence Layer).

This script tests the multi-model routing system by sending a simple
prompt and verifying which model responds based on task type.

Usage:
    python tests/test_brain.py

Prerequisites:
    1. Create config/secrets.toml with your API keys
    2. Run this script to test model routing
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.llm_gateway import (
    generate_content,
    estimate_tokens,
    _route_task,
    get_available_models,
    SECRETS_PATH,
    HEAVY_LIFT_THRESHOLD,
    _gemini_available,
)


def test_routing_logic():
    """Test the routing logic without making API calls."""
    print("=" * 60)
    print("LLM GATEWAY - Routing Logic Test")
    print("=" * 60)
    print()

    # Test token estimation
    print("[1] Testing token estimation...")
    test_text = "Hello world" * 100  # 1100 chars
    tokens = estimate_tokens(test_text)
    print(f"    Text length: {len(test_text)} chars")
    print(f"    Estimated tokens: {tokens}")
    print(f"    Expected: ~{len(test_text) // 4}")
    print()

    # Check Gemini availability
    print("[2] Checking model availability...")
    print(f"    Gemini library available: {_gemini_available}")
    print()

    # Test routing rules
    print("[3] Testing routing rules...")
    print()

    # Build test cases based on what's available
    # When Gemini is unavailable, heavy lift should fall back to writer
    fallback_model = "writer"  # Fallback when Gemini not available

    test_cases = [
        # (task_type, token_count, expected_model, note)
        ("drafting", 1000, "writer", ""),
        ("synthesis", 5000, "writer", ""),
        ("audit", 1000, "auditor", ""),
        ("critique", 2000, "auditor", ""),
        ("review", 500, "auditor", ""),
        ("drafting", 50000, "context" if _gemini_available else fallback_model, "heavy lift"),
        ("audit", 100000, "context" if _gemini_available else fallback_model, "heavy lift"),
        ("unknown", 1000, "writer", "default"),
    ]

    print(f"    {'Task Type':<15} {'Tokens':<10} {'Expected':<10} {'Got':<10} {'Status':<6} {'Note'}")
    print("    " + "-" * 70)

    all_passed = True
    for task_type, token_count, expected, note in test_cases:
        # Pass None for models to test pure routing logic without availability check
        # For heavy lift tests, we simulate having/not having context model
        mock_models = {'context': True} if _gemini_available else {'context': None}
        result = _route_task(task_type, token_count, mock_models)
        status = "PASS" if result == expected else "FAIL"
        if result != expected:
            all_passed = False
        print(f"    {task_type:<15} {token_count:<10} {expected:<10} {result:<10} {status:<6} {note}")

    print()
    if all_passed:
        print("    All routing tests passed!")
    else:
        print("    WARNING: Some routing tests failed!")

    return all_passed


def test_api_call():
    """Test actual API call with drafting task."""
    print()
    print("=" * 60)
    print("LLM GATEWAY - API Call Test")
    print("=" * 60)
    print()

    # Check for secrets file
    print("[4] Checking configuration...")
    if not SECRETS_PATH.exists():
        print(f"    ERROR: {SECRETS_PATH} not found!")
        print()
        print("    To set up the Intelligence Layer:")
        print("    1. Copy config/secrets.toml.example to config/secrets.toml")
        print("    2. Add your API keys for Anthropic, OpenAI, and Google")
        print("    3. Run this test again")
        print()
        return False

    print("    Secrets file found!")
    print()

    # Check available models
    print("[5] Checking available models...")
    try:
        available = get_available_models()
        print(f"    Available models: {', '.join(available)}")
        if 'context' not in available:
            print("    Note: Gemini (context) model not configured - heavy lift will use Claude")
    except Exception as e:
        print(f"    Error initializing models: {e}")
        return False
    print()

    # Test simple generation
    print("[6] Testing content generation (task_type='drafting')...")
    print()

    try:
        result = generate_content(
            prompt="Say hello and identify yourself in one sentence.",
            task_type="drafting",
        )

        print(f"    Model used: {result['model_used']}")
        print(f"    Tokens estimated: {result['tokens_estimated']}")
        print()
        print("    Response:")
        print("    " + "-" * 50)
        # Truncate long responses for display
        content = result['content']
        if len(content) > 500:
            content = content[:500] + "..."
        for line in content.split('\n'):
            print(f"    {line}")
        print("    " + "-" * 50)
        print()
        print("    API test successful!")
        return True

    except Exception as e:
        print(f"    ERROR: {e}")
        print()
        print("    Check that your API keys are valid in config/secrets.toml")
        return False


def main():
    """Run all tests."""
    # Always run routing logic test (no API needed)
    routing_ok = test_routing_logic()

    # Run API test
    api_ok = test_api_call()

    print()
    print("=" * 60)
    if routing_ok and api_ok:
        print("All tests completed successfully!")
    elif routing_ok:
        print("Routing tests passed. API test skipped or failed.")
    else:
        print("Some tests failed. Check output above.")
    print("=" * 60)

    return 0 if (routing_ok and api_ok) else 1


if __name__ == "__main__":
    sys.exit(main())
