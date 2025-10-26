import unittest
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from models.rate_limit_response import RateLimitResponse
from pydantic import ValidationError


class TestRateLimitResponse(unittest.TestCase):
    """Test cases for RateLimitResponse model"""

    def test_rate_limit_response_allowed(self):
        """Test RateLimitResponse for allowed request"""
        response = RateLimitResponse(
            allowed=True,
            remaining=5
        )
        
        self.assertTrue(response.allowed)
        self.assertEqual(response.remaining, 5)
        self.assertIsNone(response.processing_time_us)
        self.assertIsNone(response.retry_after)

    def test_rate_limit_response_rejected(self):
        """Test RateLimitResponse for rejected request"""
        response = RateLimitResponse(
            allowed=False,
            remaining=0,
            retry_after=30
        )
        
        self.assertFalse(response.allowed)
        self.assertEqual(response.remaining, 0)
        self.assertEqual(response.retry_after, 30)
        self.assertIsNone(response.processing_time_us)

    def test_rate_limit_response_with_processing_time(self):
        """Test RateLimitResponse with processing time"""
        response = RateLimitResponse(
            allowed=True,
            remaining=3,
            processing_time_us=150.5
        )
        
        self.assertTrue(response.allowed)
        self.assertEqual(response.remaining, 3)
        self.assertEqual(response.processing_time_us, 150.5)
        self.assertIsNone(response.retry_after)

    def test_rate_limit_response_missing_required_fields(self):
        """Test RateLimitResponse validation with missing required fields"""
        with self.assertRaises(ValidationError):
            RateLimitResponse(allowed=True)  # Missing remaining
        
        with self.assertRaises(ValidationError):
            RateLimitResponse(remaining=5)  # Missing allowed

    def test_rate_limit_response_invalid_types(self):
        """Test RateLimitResponse validation with invalid types"""
        with self.assertRaises(ValidationError):
            RateLimitResponse(
                allowed="invalid_bool",  # Should be bool, can't be coerced
                remaining=5
            )
        
        with self.assertRaises(ValidationError):
            RateLimitResponse(
                allowed=True,
                remaining="five"  # Should be int
            )
        
        with self.assertRaises(ValidationError):
            RateLimitResponse(
                allowed=True,
                remaining=5,
                processing_time_us="slow"  # Should be float
            )
        
        with self.assertRaises(ValidationError):
            RateLimitResponse(
                allowed=False,
                remaining=0,
                retry_after="thirty"  # Should be int
            )
        
        # Test that negative remaining is actually allowed (no validation constraint)
        # This test documents current behavior - negative remaining is allowed
        response = RateLimitResponse(
            allowed=True,
            remaining=-1  # This is actually allowed by the model
        )
        self.assertEqual(response.remaining, -1)

    def test_rate_limit_response_field_descriptions(self):
        """Test RateLimitResponse has proper field descriptions"""
        schema = RateLimitResponse.model_json_schema()
        properties = schema['properties']
        
        self.assertIn('allowed', properties)
        self.assertEqual(
            properties['allowed']['description'],
            "Whether the request is allowed"
        )
        
        self.assertIn('remaining', properties)
        self.assertEqual(
            properties['remaining']['description'],
            "Number of requests remaining in the current window"
        )
        
        self.assertIn('processing_time_us', properties)
        self.assertEqual(
            properties['processing_time_us']['description'],
            "Processing time in microseconds"
        )
        
        self.assertIn('retry_after', properties)
        self.assertEqual(
            properties['retry_after']['description'],
            "Seconds to wait before retrying (only present when allowed=false)"
        )

    def test_rate_limit_response_docstring(self):
        """Test that RateLimitResponse has proper docstring"""
        self.assertIsNotNone(RateLimitResponse.__doc__)
        self.assertIn("API response model", RateLimitResponse.__doc__)

    def test_rate_limit_response_validation_works(self):
        """Test that Pydantic validation still works after Field additions"""
        # Test valid creation
        response = RateLimitResponse(allowed=True, remaining=5)
        self.assertTrue(response.allowed)
        self.assertEqual(response.remaining, 5)
        
        # Test validation errors still work
        with self.assertRaises(ValidationError):
            RateLimitResponse()  # Missing required fields

    def test_rate_limit_response_serialization(self):
        """Test RateLimitResponse serialization"""
        response = RateLimitResponse(
            allowed=False,
            remaining=0,
            retry_after=60,
            processing_time_us=250.75
        )
        
        data = response.model_dump()
        expected = {
            'allowed': False,
            'remaining': 0,
            'retry_after': 60,
            'processing_time_us': 250.75
        }
        
        self.assertEqual(data, expected)

    def test_rate_limit_response_optional_fields(self):
        """Test RateLimitResponse with optional fields as None"""
        response = RateLimitResponse(
            allowed=True,
            remaining=10,
            processing_time_us=None,
            retry_after=None
        )
        
        self.assertTrue(response.allowed)
        self.assertEqual(response.remaining, 10)
        self.assertIsNone(response.processing_time_us)
        self.assertIsNone(response.retry_after)


if __name__ == '__main__':
    unittest.main()
