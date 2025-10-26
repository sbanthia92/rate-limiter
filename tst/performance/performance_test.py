#!/usr/bin/env python3
"""
Performance test for rate limiter service
Tests throughput and latency requirements for both API and core decision logic
"""

import requests
import time
import threading
import statistics
import sys
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

# Add src to path to import rate limiter components for core testing
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

try:
    from rate_limiter_service import RateLimiterService
    from models.config_response import ConfigResponse
    from constants.algorithm_type import AlgorithmType
    CORE_TESTING_AVAILABLE = True
except ImportError:
    CORE_TESTING_AVAILABLE = False
    print("⚠️  Core testing modules not available - will only test API performance")

BASE_URL = "http://localhost:5000"

def single_request():
    """Make a single rate limit request and measure latency"""
    start_time = time.time()
    try:
        response = requests.post(f"{BASE_URL}/api/v1/ratelimit", 
                               json={"client_id": f"perf_test_{threading.current_thread().ident}", 
                                    "resource": "api"},
                               timeout=1)
        end_time = time.time()
        latency = (end_time - start_time) * 1000  # Convert to milliseconds
        return {
            'success': response.status_code == 200,
            'latency_ms': latency,
            'response': response.json() if response.status_code == 200 else None
        }
    except Exception as e:
        end_time = time.time()
        return {
            'success': False,
            'latency_ms': (end_time - start_time) * 1000,
            'error': str(e)
        }

def single_core_decision(rate_limiter, client_id, resource="api"):
    """Test a single core rate limiting decision and measure latency"""
    start_time = time.perf_counter()
    result = rate_limiter.check_rate_limit(client_id, resource)
    end_time = time.perf_counter()
    
    latency_us = (end_time - start_time) * 1_000_000  # Convert to microseconds
    
    return {
        'allowed': result.allowed,
        'remaining': result.remaining,
        'latency_us': latency_us,
        'latency_ms': latency_us / 1000
    }

def throughput_test(num_requests=1000, num_threads=50):
    """Test throughput with concurrent requests"""
    print(f"Testing throughput: {num_requests} requests with {num_threads} threads")
    
    # Configure high limits for throughput test
    config_response = requests.post(f"{BASE_URL}/api/v1/configure",
                                  json={"window_seconds": 60, "requests_per_window": 10000})
    
    if config_response.status_code != 200:
        print("Failed to configure rate limiter")
        return
    
    start_time = time.time()
    results = []
    
    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = [executor.submit(single_request) for _ in range(num_requests)]
        
        for future in as_completed(futures):
            results.append(future.result())
    
    end_time = time.time()
    total_time = end_time - start_time
    
    # Calculate metrics
    successful_requests = [r for r in results if r['success']]
    failed_requests = [r for r in results if not r['success']]
    latencies = [r['latency_ms'] for r in successful_requests]
    
    rps = len(successful_requests) / total_time
    avg_latency = statistics.mean(latencies) if latencies else 0
    p95_latency = statistics.quantiles(latencies, n=20)[18] if len(latencies) > 20 else 0
    
    print(f"📊 Results:")
    print(f"   Total time: {total_time:.2f}s")
    print(f"   Successful requests: {len(successful_requests)}/{num_requests}")
    print(f"   Failed requests: {len(failed_requests)}")
    print(f"   Throughput: {rps:.2f} RPS")
    print(f"   Average latency: {avg_latency:.2f}ms")
    print(f"   P95 latency: {p95_latency:.2f}ms")
    
    # Check requirements
    print(f"\n✅ Requirements Check:")
    print(f"   Throughput ≥ 1000 RPS: {'✅' if rps >= 1000 else '❌'} ({rps:.0f} RPS)")
    print(f"   Avg Latency < 10ms: {'✅' if avg_latency < 10 else '❌'} ({avg_latency:.1f}ms)")
    print(f"   P95 Latency < 10ms: {'✅' if p95_latency < 10 else '❌'} ({p95_latency:.1f}ms)")

def latency_test(num_requests=100):
    """Test latency with sequential requests"""
    print(f"\n🎯 Testing API latency: {num_requests} sequential requests")
    
    latencies = []
    for i in range(num_requests):
        result = single_request()
        if result['success']:
            latencies.append(result['latency_ms'])
        
        if (i + 1) % 20 == 0:
            print(f"   Completed {i + 1}/{num_requests} requests")
    
    if latencies:
        avg_latency = statistics.mean(latencies)
        min_latency = min(latencies)
        max_latency = max(latencies)
        p95_latency = statistics.quantiles(latencies, n=20)[18] if len(latencies) > 20 else max_latency
        
        print(f"📊 API Latency Results:")
        print(f"   Average: {avg_latency:.2f}ms")
        print(f"   Min: {min_latency:.2f}ms")
        print(f"   Max: {max_latency:.2f}ms")
        print(f"   P95: {p95_latency:.2f}ms")
        print(f"   API Requirement < 10ms: {'✅' if avg_latency < 10 else '❌'}")

def core_decision_latency_test(num_requests=1000):
    """Test core decision logic latency without HTTP overhead"""
    if not CORE_TESTING_AVAILABLE:
        print(f"\n⚠️  Core decision testing not available - skipping")
        return None
        
    print(f"\n🎯 Testing CORE DECISION latency: {num_requests} sequential decisions")
    
    # Initialize rate limiter directly
    config = ConfigResponse(window_seconds=60, requests_per_window=100, algorithm=AlgorithmType.SLIDING_WINDOW)
    rate_limiter = RateLimiterService(config)
    
    latencies_us = []
    latencies_ms = []
    
    for i in range(num_requests):
        result = single_core_decision(rate_limiter, f"core_test_{i}")
        latencies_us.append(result['latency_us'])
        latencies_ms.append(result['latency_ms'])
        
        if (i + 1) % 200 == 0:
            print(f"   Completed {i + 1}/{num_requests} decisions")
    
    # Calculate statistics
    avg_latency_us = statistics.mean(latencies_us)
    min_latency_us = min(latencies_us)
    max_latency_us = max(latencies_us)
    p95_latency_us = statistics.quantiles(latencies_us, n=20)[18] if len(latencies_us) > 20 else max_latency_us
    p99_latency_us = statistics.quantiles(latencies_us, n=100)[98] if len(latencies_us) > 100 else max_latency_us
    
    avg_latency_ms = avg_latency_us / 1000
    p95_latency_ms = p95_latency_us / 1000
    
    print(f"📊 Core Decision Latency Results:")
    print(f"   Average: {avg_latency_us:.2f} μs ({avg_latency_ms:.3f} ms)")
    print(f"   Min: {min_latency_us:.2f} μs ({min_latency_us/1000:.3f} ms)")
    print(f"   Max: {max_latency_us:.2f} μs ({max_latency_us/1000:.3f} ms)")
    print(f"   P95: {p95_latency_us:.2f} μs ({p95_latency_ms:.3f} ms)")
    print(f"   P99: {p99_latency_us:.2f} μs ({p99_latency_us/1000:.3f} ms)")
    print(f"   Core Decision < 10ms: {'✅' if avg_latency_ms < 10 else '❌'}")
    
    return {
        'avg_latency_us': avg_latency_us,
        'p95_latency_us': p95_latency_us,
        'meets_requirement': avg_latency_ms < 10 and p95_latency_ms < 10
    }

def core_decision_throughput_test(num_requests=1000, num_threads=50):
    """Test core decision throughput without HTTP overhead"""
    if not CORE_TESTING_AVAILABLE:
        print(f"\n⚠️  Core decision testing not available - skipping")
        return None
        
    print(f"\n🚀 Testing CORE DECISION throughput: {num_requests} decisions with {num_threads} threads")
    
    # Initialize rate limiter with high limits
    config = ConfigResponse(window_seconds=60, requests_per_window=10000, algorithm=AlgorithmType.SLIDING_WINDOW)
    rate_limiter = RateLimiterService(config)
    
    start_time = time.perf_counter()
    results = []
    
    def worker_task(task_id):
        return single_core_decision(rate_limiter, f"throughput_test_{threading.current_thread().ident}_{task_id}")
    
    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = [executor.submit(worker_task, i) for i in range(num_requests)]
        
        for future in as_completed(futures):
            results.append(future.result())
    
    end_time = time.perf_counter()
    total_time = end_time - start_time
    
    # Calculate metrics
    latencies_us = [r['latency_us'] for r in results]
    decisions_per_second = len(results) / total_time
    avg_latency_us = statistics.mean(latencies_us)
    p95_latency_us = statistics.quantiles(latencies_us, n=20)[18] if len(latencies_us) > 20 else max(latencies_us)
    
    avg_latency_ms = avg_latency_us / 1000
    p95_latency_ms = p95_latency_us / 1000
    
    print(f"📊 Core Decision Throughput Results:")
    print(f"   Total time: {total_time:.3f}s")
    print(f"   Decisions per second: {decisions_per_second:.2f} DPS")
    print(f"   Average decision latency: {avg_latency_us:.2f} μs ({avg_latency_ms:.3f} ms)")
    print(f"   P95 decision latency: {p95_latency_us:.2f} μs ({p95_latency_ms:.3f} ms)")
    
    print(f"\n✅ Core Decision Requirements Check:")
    print(f"   Decisions ≥ 1000 DPS: {'✅' if decisions_per_second >= 1000 else '❌'} ({decisions_per_second:.0f} DPS)")
    print(f"   Avg Decision < 10ms: {'✅' if avg_latency_ms < 10 else '❌'} ({avg_latency_ms:.3f}ms)")
    print(f"   P95 Decision < 10ms: {'✅' if p95_latency_ms < 10 else '❌'} ({p95_latency_ms:.3f}ms)")
    
    return {
        'decisions_per_second': decisions_per_second,
        'avg_latency_us': avg_latency_us,
        'p95_latency_us': p95_latency_us,
        'meets_throughput': decisions_per_second >= 1000,
        'meets_latency': avg_latency_ms < 10 and p95_latency_ms < 10
    }

if __name__ == '__main__':
    print("Rate Limiter Performance Test")
    print("============================")
    print("Testing both API performance and core decision logic performance\n")
    
    # Check if service is running for API tests
    api_available = False
    try:
        response = requests.get(f"{BASE_URL}/test", timeout=2)
        if response.status_code == 200:
            api_available = True
            print("✅ API service is running")
        else:
            print("❌ API service not responding properly")
    except:
        print("❌ Cannot connect to API service")
    
    if CORE_TESTING_AVAILABLE:
        print("✅ Core decision testing available")
    else:
        print("❌ Core decision testing not available")
    
    print()
    
    # Run API tests if available
    if api_available:
        print("=" * 50)
        print("API PERFORMANCE TESTS (includes HTTP overhead)")
        print("=" * 50)
        latency_test(100)
        throughput_test(1000, 50)
    
    # Run core decision tests if available
    if CORE_TESTING_AVAILABLE:
        print("\n" + "=" * 50)
        print("CORE DECISION PERFORMANCE TESTS (pure algorithm)")
        print("=" * 50)
        core_latency_results = core_decision_latency_test(1000)
        core_throughput_results = core_decision_throughput_test(1000, 50)
        
        # Final summary for core decision performance
        if core_latency_results and core_throughput_results:
            print(f"\n🏁 CORE DECISION PERFORMANCE SUMMARY")
            print("=" * 40)
            print(f"Sequential Decision Latency:")
            print(f"   Average: {core_latency_results['avg_latency_us']:.2f} μs ({core_latency_results['avg_latency_us']/1000:.3f} ms)")
            print(f"   P95: {core_latency_results['p95_latency_us']:.2f} μs ({core_latency_results['p95_latency_us']/1000:.3f} ms)")
            print(f"   Meets < 10ms requirement: {'✅' if core_latency_results['meets_requirement'] else '❌'}")
            
            print(f"\nConcurrent Decision Performance:")
            print(f"   Throughput: {core_throughput_results['decisions_per_second']:.0f} decisions/second")
            print(f"   Average latency: {core_throughput_results['avg_latency_us']:.2f} μs ({core_throughput_results['avg_latency_us']/1000:.3f} ms)")
            print(f"   P95 latency: {core_throughput_results['p95_latency_us']:.2f} μs ({core_throughput_results['p95_latency_us']/1000:.3f} ms)")
            print(f"   Meets all requirements: {'✅' if core_throughput_results['meets_throughput'] and core_throughput_results['meets_latency'] else '❌'}")
            
            print(f"\n🎯 FINAL CONCLUSION:")
            if core_latency_results['meets_requirement'] and core_throughput_results['meets_latency']:
                print("   ✅ CORE DECISION LOGIC FULLY MEETS < 10ms LATENCY REQUIREMENT")
                print("   ✅ Algorithm performance is excellent for production use")
                print("   📝 Note: API latency includes HTTP/network overhead (separate concern)")
            else:
                print("   ❌ Core decision logic does not meet performance requirements")
    
    print("\n🏁 Performance testing complete!")
