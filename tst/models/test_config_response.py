import unittest
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from models.config_response import ConfigResponse
from pydantic import ValidationError


class TestConfigResponse(unittest.TestCase):
    """Test cases for ConfigResponse model"""

    def test_config_response_valid(self):
        """Test ConfigResponse with valid data"""
        response = ConfigResponse(
            window_seconds=60,
            requests_per_window=100,
            algorithm="SLIDING_WINDOW"
        )
        
        self.assertEqual(response.window_seconds, 60)
        self.assertEqual(response.requests_per_window, 100)
        self.assertEqual(response.algorithm, "SLIDING_WINDOW")

    def test_config_response_missing_fields(self):
        """Test ConfigResponse with missing required fields"""
        with self.assertRaises(ValidationError):
            ConfigResponse(window_seconds=60)  # Missing requests_per_window and algorithm
        
        with self.assertRaises(ValidationError):
            ConfigResponse(requests_per_window=100)  # Missing window_seconds and algorithm
        
        with self.assertRaises(ValidationError):
            ConfigResponse(algorithm="SLIDING_WINDOW")  # Missing window_seconds and requests_per_window

    def test_config_response_invalid_types(self):
        """Test ConfigResponse with invalid data types"""
        with self.assertRaises(ValidationError):
            ConfigResponse(
                window_seconds="sixty",  # Should be int
                requests_per_window=100,
                algorithm="SLIDING_WINDOW"
            )
        
        with self.assertRaises(ValidationError):
            ConfigResponse(
                window_seconds=60,
                requests_per_window="hundred",  # Should be int
                algorithm="SLIDING_WINDOW"
            )
        
        with self.assertRaises(ValidationError):
            ConfigResponse(
                window_seconds=60,
                requests_per_window=100,
                algorithm=123  # Should be string
            )

    def test_config_response_edge_values(self):
        """Test ConfigResponse with edge values"""
        # Test with minimum values
        response = ConfigResponse(
            window_seconds=1,
            requests_per_window=1,
            algorithm="SLIDING_WINDOW"
        )
        self.assertEqual(response.window_seconds, 1)
        self.assertEqual(response.requests_per_window, 1)
        
        # Test with large values
        response = ConfigResponse(
            window_seconds=86400,  # 1 day
            requests_per_window=1000000,
            algorithm="SLIDING_WINDOW"
        )
        self.assertEqual(response.window_seconds, 86400)
        self.assertEqual(response.requests_per_window, 1000000)

    def test_config_response_serialization(self):
        """Test ConfigResponse serialization to dict"""
        response = ConfigResponse(
            window_seconds=60,
            requests_per_window=100,
            algorithm="SLIDING_WINDOW"
        )
        
        data = response.model_dump()
        expected = {
            'window_seconds': 60,
            'requests_per_window': 100,
            'algorithm': 'SLIDING_WINDOW'
        }
        
        self.assertEqual(data, expected)

    def test_config_response_field_descriptions(self):
        """Test ConfigResponse has proper field descriptions"""
        schema = ConfigResponse.model_json_schema()
        properties = schema['properties']
        
        self.assertIn('window_seconds', properties)
        self.assertEqual(
            properties['window_seconds']['description'],
            "Window size in seconds for rate limiting"
        )
        
        self.assertIn('requests_per_window', properties)
        self.assertEqual(
            properties['requests_per_window']['description'],
            "Maximum number of requests allowed per window"
        )
        
        self.assertIn('algorithm', properties)
        self.assertEqual(
            properties['algorithm']['description'],
            "Rate limiting algorithm to use"
        )

    def test_config_response_docstring(self):
        """Test that ConfigResponse has proper docstring"""
        self.assertIsNotNone(ConfigResponse.__doc__)
        self.assertIn("Configuration for rate limiting", ConfigResponse.__doc__)

    def test_config_response_validation_works(self):
        """Test that Pydantic validation still works after Field additions"""
        # Test validation errors still work
        with self.assertRaises(ValidationError):
            ConfigResponse(window_seconds=60)  # Missing requests_per_window and algorithm


if __name__ == '__main__':
    unittest.main()
