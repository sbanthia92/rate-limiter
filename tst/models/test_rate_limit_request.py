import unittest
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from models.rate_limit_request import RateLimitRequest
from pydantic import ValidationError


class TestRateLimitRequest(unittest.TestCase):
    """Test cases for RateLimitRequest model"""

    def test_rate_limit_request_valid(self):
        """Test valid RateLimitRequest creation"""
        request = RateLimitRequest(
            client_id="test_client",
            resource="api"
        )
        
        self.assertEqual(request.client_id, "test_client")
        self.assertEqual(request.resource, "api")

    def test_rate_limit_request_default_resource(self):
        """Test RateLimitRequest with default resource"""
        request = RateLimitRequest(client_id="test_client")
        
        self.assertEqual(request.client_id, "test_client")
        self.assertEqual(request.resource, "default")

    def test_rate_limit_request_missing_client_id(self):
        """Test RateLimitRequest validation with missing client_id"""
        with self.assertRaises(ValidationError):
            RateLimitRequest(resource="api")

    def test_rate_limit_request_field_descriptions(self):
        """Test RateLimitRequest has proper field descriptions"""
        schema = RateLimitRequest.model_json_schema()
        properties = schema['properties']
        
        self.assertIn('client_id', properties)
        self.assertEqual(
            properties['client_id']['description'],
            "Unique identifier for the client making the request"
        )
        
        self.assertIn('resource', properties)
        self.assertEqual(
            properties['resource']['description'],
            "Resource being accessed (defaults to 'default')"
        )

    def test_rate_limit_request_docstring(self):
        """Test that RateLimitRequest has proper docstring"""
        self.assertIsNotNone(RateLimitRequest.__doc__)
        self.assertIn("API request model", RateLimitRequest.__doc__)

    def test_rate_limit_request_validation_works(self):
        """Test that Pydantic validation still works after Field additions"""
        # Test valid creation
        request = RateLimitRequest(client_id="test")
        self.assertEqual(request.client_id, "test")
        self.assertEqual(request.resource, "default")
        
        # Test validation errors still work
        with self.assertRaises(ValidationError):
            RateLimitRequest()  # Missing required client_id

    def test_rate_limit_request_serialization(self):
        """Test RateLimitRequest serialization"""
        request = RateLimitRequest(
            client_id="user123",
            resource="api/v1"
        )
        
        data = request.model_dump()
        expected = {
            'client_id': 'user123',
            'resource': 'api/v1'
        }
        
        self.assertEqual(data, expected)

    def test_rate_limit_request_empty_strings(self):
        """Test RateLimitRequest with empty strings"""
        # Empty client_id is actually allowed by current model
        request = RateLimitRequest(client_id="")
        self.assertEqual(request.client_id, "")
        
        # Empty resource is also allowed
        request = RateLimitRequest(client_id="test", resource="")
        self.assertEqual(request.resource, "")

    def test_rate_limit_request_whitespace_handling(self):
        """Test RateLimitRequest handles whitespace properly"""
        # Whitespace-only client_id is allowed by current model
        request = RateLimitRequest(client_id="   ")
        self.assertEqual(request.client_id, "   ")
        
        # Whitespace-only resource is also allowed
        request = RateLimitRequest(client_id="test", resource="   ")
        self.assertEqual(request.resource, "   ")

    def test_rate_limit_request_special_characters(self):
        """Test RateLimitRequest with various characters"""
        # Valid characters should work
        request = RateLimitRequest(
            client_id="user-123_test.client",
            resource="api/v1/users"
        )
        self.assertEqual(request.client_id, "user-123_test.client")
        self.assertEqual(request.resource, "api/v1/users")
        
        # Special characters are allowed by current model
        request = RateLimitRequest(client_id="user<script>")
        self.assertEqual(request.client_id, "user<script>")
        
        request = RateLimitRequest(client_id="user", resource="api//bad")
        self.assertEqual(request.resource, "api//bad")


if __name__ == '__main__':
    unittest.main()
