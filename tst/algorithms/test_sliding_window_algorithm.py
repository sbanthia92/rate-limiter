import unittest
import time
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from algorithms.sliding_window_algorithm import SlidingWindowAlgorithm
from models.config_response import ConfigResponse
from constants.algorithm_type import AlgorithmType


class TestSlidingWindowAlgorithm(unittest.TestCase):
    """Test cases for SlidingWindowAlgorithm"""

    def setUp(self):
        """Set up test fixtures"""
        self.algorithm = SlidingWindowAlgorithm()
        self.config = ConfigResponse(
            window_seconds=5,
            requests_per_window=3,
            algorithm=AlgorithmType.SLIDING_WINDOW
        )
        self.client_key = "test_client:api"

    def test_first_request_allowed(self):
        """Test first request is always allowed"""
        result = self.algorithm.check_request(self.client_key, self.config)
        
        self.assertTrue(result.allowed)
        self.assertEqual(result.remaining, 2)
        # retry_after should be None for allowed requests
        self.assertIsNone(result.retry_after)

    def test_requests_within_limit(self):
        """Test requests within limit are allowed"""
        # Make 3 requests (the limit)
        for i in range(3):
            result = self.algorithm.check_request(self.client_key, self.config)
            self.assertTrue(result.allowed)
            self.assertEqual(result.remaining, 2 - i)

    def test_request_exceeding_limit(self):
        """Test request exceeding limit is rejected"""
        # Make 3 requests to reach limit
        for _ in range(3):
            self.algorithm.check_request(self.client_key, self.config)
        
        # 4th request should be rejected
        result = self.algorithm.check_request(self.client_key, self.config)
        
        self.assertFalse(result.allowed)
        self.assertEqual(result.remaining, 0)
        self.assertGreater(result.retry_after, 0)

    def test_different_clients_independent(self):
        """Test different clients have independent limits"""
        client1 = "client1:api"
        client2 = "client2:api"
        
        # Exhaust client1's limit
        for _ in range(3):
            self.algorithm.check_request(client1, self.config)
        
        # Client2 should still be allowed
        result = self.algorithm.check_request(client2, self.config)
        self.assertTrue(result.allowed)

    def test_window_sliding(self):
        """Test that window slides over time"""
        # This test uses a shorter window for faster execution
        short_config = ConfigResponse(
            window_seconds=1,
            requests_per_window=2,
            algorithm=AlgorithmType.SLIDING_WINDOW
        )
        
        # Make 2 requests to reach limit
        for _ in range(2):
            result = self.algorithm.check_request(self.client_key, short_config)
            self.assertTrue(result.allowed)
        
        # 3rd request should be rejected
        result = self.algorithm.check_request(self.client_key, short_config)
        self.assertFalse(result.allowed)
        
        # Wait for window to slide
        time.sleep(1.1)
        
        # Should be allowed again
        result = self.algorithm.check_request(self.client_key, short_config)
        self.assertTrue(result.allowed)

    def test_empty_request_log_handling(self):
        """Test handling of empty request logs"""
        # This tests the edge case fix we made
        result = self.algorithm.check_request("new_client:api", self.config)
        self.assertTrue(result.allowed)


if __name__ == '__main__':
    unittest.main()
