import unittest
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from models.rate_limit_request import RateLimitRequest
from models.config_request import ConfigRequest
from models.config_response import ConfigResponse
from rate_limiter_service import RateLimiterService
from constants.algorithm_type import AlgorithmType
from pydantic import ValidationError


class TestAPI(unittest.TestCase):
    """Test cases for API logic (without HTTP layer)"""

    def setUp(self):
        """Set up test fixtures"""
        # Create a rate limiter service for testing
        config = ConfigResponse(
            window_seconds=60,
            requests_per_window=100,
            algorithm=AlgorithmType.SLIDING_WINDOW
        )
        self.rate_limiter = RateLimiterService(config)

    def test_config_request_validation(self):
        """Test ConfigRequest model validation"""
        # Valid config request
        config = ConfigRequest(window_seconds=30, requests_per_window=10)
        self.assertEqual(config.window_seconds, 30)
        self.assertEqual(config.requests_per_window, 10)
        
        # Invalid config request
        with self.assertRaises(ValidationError):
            ConfigRequest(window_seconds="invalid", requests_per_window=10)

    def test_rate_limit_request_validation(self):
        """Test RateLimitRequest model validation"""
        # Valid request
        request = RateLimitRequest(client_id="test_client", resource="api")
        self.assertEqual(request.client_id, "test_client")
        self.assertEqual(request.resource, "api")
        
        # Valid request with default resource
        request = RateLimitRequest(client_id="test_client")
        self.assertEqual(request.client_id, "test_client")
        self.assertEqual(request.resource, "default")
        
        # Invalid request
        with self.assertRaises(ValidationError):
            RateLimitRequest(resource="api")  # Missing client_id

    def test_rate_limit_service_functionality(self):
        """Test rate limit service functionality"""
        # Test successful rate limit check
        result = self.rate_limiter.check_rate_limit("test_client", "api")
        
        self.assertTrue(result.allowed)
        self.assertIsInstance(result.remaining, int)
        self.assertIsNone(result.retry_after)  # Should be None for allowed requests

    def test_rate_limit_service_configuration(self):
        """Test rate limit service configuration"""
        # Create new config
        new_config = ConfigResponse(
            window_seconds=30,
            requests_per_window=10,
            algorithm=AlgorithmType.SLIDING_WINDOW
        )
        
        # Update service config
        self.rate_limiter.update_config(new_config)
        
        # Verify config was updated
        self.assertEqual(self.rate_limiter.config.window_seconds, 30)
        self.assertEqual(self.rate_limiter.config.requests_per_window, 10)

    def test_rate_limit_service_integration(self):
        """Test integration between configuration and rate limiting"""
        # Configure rate limiter with low limits for testing
        config = ConfigResponse(
            window_seconds=10,
            requests_per_window=2,
            algorithm=AlgorithmType.SLIDING_WINDOW
        )
        self.rate_limiter.update_config(config)
        
        # First two requests should be allowed
        for i in range(2):
            result = self.rate_limiter.check_rate_limit("integration_test", "api")
            self.assertTrue(result.allowed)
            self.assertEqual(result.remaining, 1 - i)
        
        # Third request should be rejected
        result = self.rate_limiter.check_rate_limit("integration_test", "api")
        self.assertFalse(result.allowed)
        self.assertEqual(result.remaining, 0)
        self.assertIsNotNone(result.retry_after)

    def test_rate_limit_response_structure(self):
        """Test that rate limit responses have correct structure"""
        result = self.rate_limiter.check_rate_limit("test_structure", "api")
        
        # Check that result has all expected attributes
        self.assertTrue(hasattr(result, 'allowed'))
        self.assertTrue(hasattr(result, 'remaining'))
        self.assertTrue(hasattr(result, 'retry_after'))
        
        # Check types
        self.assertIsInstance(result.allowed, bool)
        self.assertIsInstance(result.remaining, int)
        # retry_after should be None for allowed requests, int for rejected
        self.assertTrue(result.retry_after is None or isinstance(result.retry_after, int))

    def test_different_clients_independence(self):
        """Test that different clients have independent rate limits"""
        # Configure with low limits
        config = ConfigResponse(
            window_seconds=10,
            requests_per_window=1,
            algorithm=AlgorithmType.SLIDING_WINDOW
        )
        self.rate_limiter.update_config(config)
        
        # Exhaust client1's limit
        result1 = self.rate_limiter.check_rate_limit("client1", "api")
        self.assertTrue(result1.allowed)
        
        result1_rejected = self.rate_limiter.check_rate_limit("client1", "api")
        self.assertFalse(result1_rejected.allowed)
        
        # Client2 should still be allowed
        result2 = self.rate_limiter.check_rate_limit("client2", "api")
        self.assertTrue(result2.allowed)

    def test_model_field_descriptions(self):
        """Test that API models have proper field descriptions"""
        # Test ConfigRequest
        config_schema = ConfigRequest.model_json_schema()
        self.assertIn('description', config_schema['properties']['window_seconds'])
        self.assertIn('description', config_schema['properties']['requests_per_window'])
        
        # Test RateLimitRequest
        request_schema = RateLimitRequest.model_json_schema()
        self.assertIn('description', request_schema['properties']['client_id'])
        self.assertIn('description', request_schema['properties']['resource'])


if __name__ == '__main__':
    unittest.main()
