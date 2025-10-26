import unittest
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from models.config_request import ConfigRequest
from pydantic import ValidationError


class TestConfigRequest(unittest.TestCase):
    """Test cases for ConfigRequest model"""

    def test_config_request_valid(self):
        """Test valid ConfigRequest creation"""
        request = ConfigRequest(
            window_seconds=60,
            requests_per_window=100
        )
        
        self.assertEqual(request.window_seconds, 60)
        self.assertEqual(request.requests_per_window, 100)

    def test_config_request_missing_fields(self):
        """Test ConfigRequest validation with missing fields"""
        with self.assertRaises(ValidationError):
            ConfigRequest(window_seconds=60)
        
        with self.assertRaises(ValidationError):
            ConfigRequest(requests_per_window=100)

    def test_config_request_invalid_types(self):
        """Test ConfigRequest validation with invalid types"""
        with self.assertRaises(ValidationError):
            ConfigRequest(
                window_seconds="invalid",
                requests_per_window=100
            )
        
        with self.assertRaises(ValidationError):
            ConfigRequest(
                window_seconds=60,
                requests_per_window="invalid"
            )

    def test_config_request_field_descriptions(self):
        """Test ConfigRequest has proper field descriptions"""
        schema = ConfigRequest.model_json_schema()
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

    def test_config_request_docstring(self):
        """Test that ConfigRequest has proper docstring"""
        self.assertIsNotNone(ConfigRequest.__doc__)
        self.assertIn("API request model", ConfigRequest.__doc__)

    def test_config_request_validation_works(self):
        """Test that Pydantic validation still works after Field additions"""
        # Test validation errors still work
        with self.assertRaises(ValidationError):
            ConfigRequest(window_seconds=60)  # Missing requests_per_window

    def test_config_request_serialization(self):
        """Test ConfigRequest serialization"""
        request = ConfigRequest(
            window_seconds=120,
            requests_per_window=200
        )
        
        data = request.model_dump()
        expected = {
            'window_seconds': 120,
            'requests_per_window': 200
        }
        
        self.assertEqual(data, expected)

    def test_config_request_edge_values(self):
        """Test ConfigRequest with edge values"""
        # Test with minimum values
        request = ConfigRequest(
            window_seconds=1,
            requests_per_window=1
        )
        self.assertEqual(request.window_seconds, 1)
        self.assertEqual(request.requests_per_window, 1)
        
        # Test with large values
        request = ConfigRequest(
            window_seconds=86400,  # 1 day
            requests_per_window=1000000
        )
        self.assertEqual(request.window_seconds, 86400)
        self.assertEqual(request.requests_per_window, 1000000)


if __name__ == '__main__':
    unittest.main()
