import unittest
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from rate_limiter_service import RateLimiterService
from models.config_response import ConfigResponse
from constants.algorithm_type import AlgorithmType


class TestRateLimiterService(unittest.TestCase):
    """Test cases for RateLimiterService"""

    def setUp(self):
        """Set up test fixtures"""
        self.config = ConfigResponse(
            window_seconds=10,
            requests_per_window=5,
            algorithm=AlgorithmType.SLIDING_WINDOW
        )
        self.service = RateLimiterService(self.config)

    def test_service_initialization(self):
        """Test service initializes correctly"""
        self.assertEqual(self.service.config.window_seconds, 10)
        self.assertEqual(self.service.config.requests_per_window, 5)
        self.assertIsNotNone(self.service.algorithm)

    def test_check_rate_limit_allowed(self):
        """Test rate limit check when allowed"""
        result = self.service.check_rate_limit("client1", "resource1")
        
        self.assertTrue(result.allowed)
        self.assertEqual(result.remaining, 4)

    def test_check_rate_limit_with_default_resource(self):
        """Test rate limit check with default resource"""
        result = self.service.check_rate_limit("client1")
        
        self.assertTrue(result.allowed)
        self.assertIsInstance(result.remaining, int)

    def test_update_config(self):
        """Test configuration update"""
        new_config = ConfigResponse(
            window_seconds=20,
            requests_per_window=10,
            algorithm=AlgorithmType.SLIDING_WINDOW
        )
        
        self.service.update_config(new_config)
        
        self.assertEqual(self.service.config.window_seconds, 20)
        self.assertEqual(self.service.config.requests_per_window, 10)

    def test_multiple_clients_resources(self):
        """Test multiple clients and resources work independently"""
        # Different clients
        result1 = self.service.check_rate_limit("client1", "api")
        result2 = self.service.check_rate_limit("client2", "api")
        
        self.assertTrue(result1.allowed)
        self.assertTrue(result2.allowed)
        
        # Same client, different resources
        result3 = self.service.check_rate_limit("client1", "upload")
        result4 = self.service.check_rate_limit("client1", "download")
        
        self.assertTrue(result3.allowed)
        self.assertTrue(result4.allowed)

    def test_rate_limit_exhaustion(self):
        """Test rate limit exhaustion"""
        client_id = "test_client"
        resource = "api"
        
        # Make requests up to the limit
        for i in range(5):
            result = self.service.check_rate_limit(client_id, resource)
            self.assertTrue(result.allowed)
            self.assertEqual(result.remaining, 4 - i)
        
        # Next request should be rejected
        result = self.service.check_rate_limit(client_id, resource)
        self.assertFalse(result.allowed)
        self.assertEqual(result.remaining, 0)
        self.assertGreater(result.retry_after, 0)


if __name__ == '__main__':
    unittest.main()
