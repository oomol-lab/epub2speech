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
        # Import test modules
        from tests.test_epub_picker import test_picker_functionality
        from tests.test_extractor import test_extractor_functionality

        print("📋 Running tests/test_epub_picker.py...")
        # Execute EPUB picker tests
        test_picker_functionality()

        print("\n📋 Running tests/test_extractor.py...")
        # Execute text extractor tests
        test_extractor_functionality()

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