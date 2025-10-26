import unittest
import time
import threading
from unittest.mock import patch
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src'))

from metrics.metrics_collector import MetricsCollector, MetricSnapshot, ClientMetrics


class TestMetricsCollector(unittest.TestCase):
    """Test cases for MetricsCollector"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.collector = MetricsCollector(history_window_seconds=60)
    
    def test_initial_state(self):
        """Test initial state of metrics collector"""
        self.assertEqual(self.collector.total_requests, 0)
        self.assertEqual(self.collector.allowed_requests, 0)
        self.assertEqual(self.collector.rejected_requests, 0)
        self.assertEqual(len(self.collector.client_metrics), 0)
        self.assertEqual(len(self.collector.response_times), 0)
    
    def test_record_allowed_request(self):
        """Test recording an allowed request"""
        self.collector.record_request("client1", allowed=True, response_time_ms=5.0)
        
        self.assertEqual(self.collector.total_requests, 1)
        self.assertEqual(self.collector.allowed_requests, 1)
        self.assertEqual(self.collector.rejected_requests, 0)
        
        # Check client metrics
        self.assertIn("client1", self.collector.client_metrics)
        client_metric = self.collector.client_metrics["client1"]
        self.assertEqual(client_metric.total_requests, 1)
        self.assertEqual(client_metric.allowed_requests, 1)
        self.assertEqual(client_metric.rejected_requests, 0)
    
    def test_record_rejected_request(self):
        """Test recording a rejected request"""
        self.collector.record_request("client1", allowed=False, response_time_ms=3.0)
        
        self.assertEqual(self.collector.total_requests, 1)
        self.assertEqual(self.collector.allowed_requests, 0)
        self.assertEqual(self.collector.rejected_requests, 1)
        
        # Check client metrics
        client_metric = self.collector.client_metrics["client1"]
        self.assertEqual(client_metric.total_requests, 1)
        self.assertEqual(client_metric.allowed_requests, 0)
        self.assertEqual(client_metric.rejected_requests, 1)
    
    def test_multiple_clients(self):
        """Test recording requests from multiple clients"""
        self.collector.record_request("client1", allowed=True, response_time_ms=5.0)
        self.collector.record_request("client2", allowed=False, response_time_ms=3.0)
        self.collector.record_request("client1", allowed=True, response_time_ms=4.0)
        
        self.assertEqual(self.collector.total_requests, 3)
        self.assertEqual(self.collector.allowed_requests, 2)
        self.assertEqual(self.collector.rejected_requests, 1)
        self.assertEqual(len(self.collector.client_metrics), 2)
        
        # Check client1 metrics
        client1 = self.collector.client_metrics["client1"]
        self.assertEqual(client1.total_requests, 2)
        self.assertEqual(client1.allowed_requests, 2)
        self.assertEqual(client1.rejected_requests, 0)
        
        # Check client2 metrics
        client2 = self.collector.client_metrics["client2"]
        self.assertEqual(client2.total_requests, 1)
        self.assertEqual(client2.allowed_requests, 0)
        self.assertEqual(client2.rejected_requests, 1)
    
    def test_response_time_tracking(self):
        """Test response time tracking"""
        response_times = [1.0, 2.0, 3.0, 4.0, 5.0]
        
        for i, rt in enumerate(response_times):
            self.collector.record_request(f"client{i}", allowed=True, response_time_ms=rt)
        
        self.assertEqual(len(self.collector.response_times), 5)
        self.assertEqual(list(self.collector.response_times), response_times)
    
    def test_get_current_metrics(self):
        """Test getting current metrics snapshot"""
        # Record some requests
        self.collector.record_request("client1", allowed=True, response_time_ms=5.0)
        self.collector.record_request("client1", allowed=False, response_time_ms=3.0)
        self.collector.record_request("client2", allowed=True, response_time_ms=4.0)
        
        snapshot = self.collector.get_current_metrics()
        
        self.assertIsInstance(snapshot, MetricSnapshot)
        self.assertEqual(snapshot.total_requests, 3)
        self.assertEqual(snapshot.allowed_requests, 2)
        self.assertEqual(snapshot.rejected_requests, 1)
        self.assertEqual(snapshot.avg_response_time_ms, 4.0)  # (5+3+4)/3
        self.assertEqual(snapshot.rejection_rate, 33.33333333333333)  # 1/3 * 100
        self.assertEqual(snapshot.active_clients, 2)
    
    def test_get_top_clients(self):
        """Test getting top clients by request count"""
        # Create clients with different request counts
        for i in range(5):
            self.collector.record_request("client1", allowed=True, response_time_ms=1.0)
        for i in range(3):
            self.collector.record_request("client2", allowed=True, response_time_ms=1.0)
        for i in range(7):
            self.collector.record_request("client3", allowed=True, response_time_ms=1.0)
        
        top_clients = self.collector.get_top_clients(limit=2)
        
        self.assertEqual(len(top_clients), 2)
        self.assertEqual(top_clients[0].client_id, "client3")  # 7 requests
        self.assertEqual(top_clients[0].total_requests, 7)
        self.assertEqual(top_clients[1].client_id, "client1")  # 5 requests
        self.assertEqual(top_clients[1].total_requests, 5)
    
    def test_reset_metrics(self):
        """Test resetting all metrics"""
        # Record some data
        self.collector.record_request("client1", allowed=True, response_time_ms=5.0)
        self.collector.record_request("client2", allowed=False, response_time_ms=3.0)
        
        # Verify data exists
        self.assertEqual(self.collector.total_requests, 2)
        self.assertEqual(len(self.collector.client_metrics), 2)
        
        # Reset and verify
        self.collector.reset_metrics()
        
        self.assertEqual(self.collector.total_requests, 0)
        self.assertEqual(self.collector.allowed_requests, 0)
        self.assertEqual(self.collector.rejected_requests, 0)
        self.assertEqual(len(self.collector.client_metrics), 0)
        self.assertEqual(len(self.collector.response_times), 0)
        self.assertEqual(len(self.collector.request_timestamps), 0)
    
    def test_thread_safety(self):
        """Test thread safety of metrics collection"""
        def record_requests():
            for i in range(100):
                self.collector.record_request(f"client{i % 5}", allowed=True, response_time_ms=1.0)
        
        # Create multiple threads
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=record_requests)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Verify total requests
        self.assertEqual(self.collector.total_requests, 500)  # 5 threads * 100 requests
        self.assertEqual(self.collector.allowed_requests, 500)
        self.assertEqual(len(self.collector.client_metrics), 5)  # 5 unique clients
    
    def test_uptime_tracking(self):
        """Test uptime tracking"""
        start_time = time.time()
        uptime = self.collector.get_uptime_seconds()
        end_time = time.time()
        
        # Uptime should be between 0 and the elapsed time
        self.assertGreaterEqual(uptime, 0)
        self.assertLessEqual(uptime, end_time - start_time + 0.1)  # Small tolerance
    
    def test_historical_snapshots(self):
        """Test historical snapshot storage"""
        # Record some requests and get snapshots
        self.collector.record_request("client1", allowed=True, response_time_ms=5.0)
        snapshot1 = self.collector.get_current_metrics()
        
        self.collector.record_request("client2", allowed=False, response_time_ms=3.0)
        snapshot2 = self.collector.get_current_metrics()
        
        # Get historical snapshots
        history = self.collector.get_historical_snapshots(limit=10)
        
        self.assertEqual(len(history), 2)
        self.assertEqual(history[0].total_requests, 1)  # First snapshot
        self.assertEqual(history[1].total_requests, 2)  # Second snapshot


if __name__ == '__main__':
    unittest.main()
