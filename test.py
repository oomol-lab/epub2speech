#!/usr/bin/env python3
"""EPUB Function Test Runner - unittest-based test harness"""

import sys
import os
import unittest
import argparse

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def run_tests():
    """Run all test cases using unittest framework"""
    print("🧪 Starting EPUB functionality tests with unittest...\n")

    # Discover and run all tests in the tests directory
    test_loader = unittest.TestLoader()
    test_suite = test_loader.discover('tests', pattern='test_*.py')

    # Run tests with detailed output
    test_runner = unittest.TextTestRunner(verbosity=2)
    result = test_runner.run(test_suite)

    # Return appropriate exit code
    return 0 if result.wasSuccessful() else 1

def run_specific_test(test_name):
    """Run a specific test module"""
    print(f"🧪 Running specific test: {test_name}\n")

    test_loader = unittest.TestLoader()

    try:
        # Import the specific test module
        test_module = __import__(f'tests.{test_name}', fromlist=[''])
        test_suite = test_loader.loadTestsFromModule(test_module)

        # Run the specific test
        test_runner = unittest.TextTestRunner(verbosity=2)
        result = test_runner.run(test_suite)

        return 0 if result.wasSuccessful() else 1
    except ImportError:
        print(f"❌ Test module '{test_name}' not found")
        return 1

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Run EPUB functionality tests')
    parser.add_argument('--test', type=str, help='Run specific test module (e.g., test_epub_picker)')
    args = parser.parse_args()

    if args.test:
        exit_code = run_specific_test(args.test)
    else:
        exit_code = run_tests()

    sys.exit(exit_code)