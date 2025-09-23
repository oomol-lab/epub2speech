#!/usr/bin/env python3
"""EPUB Function Test Runner - Simple test harness"""

import sys
import os

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def run_tests():
    """Run all test cases"""
    print("🧪 Starting EPUB functionality tests...\n")

    try:
        # Import test module
        from tests.test_picker import test_picker_functionality

        print("📋 Running tests/test_picker.py...")

        # Execute tests
        test_picker_functionality()

        print("\n🎉 All tests passed!")
        return 0

    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        return 1
    except Exception as e:
        print(f"\n💥 Test error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(run_tests())