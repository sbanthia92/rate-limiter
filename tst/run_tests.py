#!/usr/bin/env python3
"""
Test runner for the rate limiter service
"""

import unittest
import sys
import os

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

def run_all_tests():
    """Run all working unit tests"""
    print("=" * 60)
    print("RUNNING ALL RATE LIMITER TESTS")
    print("=" * 60)
    
    # All test modules - one per source model file + metrics tests
    test_modules = [
        'models.test_config_request',
        'models.test_config_response', 
        'models.test_rate_limit_request',
        'models.test_rate_limit_response',
        'models.test_metrics_response',
        'test_api',
        'algorithms.test_rate_limiter_service',
        'algorithms.test_sliding_window_algorithm',
        'metrics.test_metrics_collector'
    ]
    
    total_tests = 0
    total_failures = 0
    
    for module in test_modules:
        print(f"\n--- Running {module} ---")
        
        try:
            # Load and run tests for this module
            loader = unittest.TestLoader()
            suite = loader.loadTestsFromName(module)
            runner = unittest.TextTestRunner(verbosity=1, stream=sys.stdout)
            result = runner.run(suite)
            
            total_tests += result.testsRun
            total_failures += len(result.failures) + len(result.errors)
            
            if result.failures:
                print(f"FAILURES in {module}:")
                for test, traceback in result.failures:
                    print(f"  - {test}")
            
            if result.errors:
                print(f"ERRORS in {module}:")
                for test, traceback in result.errors:
                    print(f"  - {test}")
                    
        except Exception as e:
            print(f"ERROR loading {module}: {e}")
            total_failures += 1
    
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"Total tests run: {total_tests}")
    print(f"Failures/Errors: {total_failures}")
    print(f"Success rate: {((total_tests - total_failures) / total_tests * 100):.1f}%" if total_tests > 0 else "0%")
    
    if total_failures == 0:
        print("🎉 ALL TESTS PASSED!")
        return True
    else:
        print("❌ Some tests failed")
        return False

def run_specific_test(test_module):
    """Run a specific test module"""
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromName(test_module)
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()

if __name__ == '__main__':
    if len(sys.argv) > 1:
        # Run specific test
        test_module = sys.argv[1]
        success = run_specific_test(test_module)
    else:
        # Run all tests
        print("Running all tests...")
        success = run_all_tests()
    
    sys.exit(0 if success else 1)
