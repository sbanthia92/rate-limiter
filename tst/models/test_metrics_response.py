import unittest
import time
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src'))

from models.metrics_response import (
    ClientMetricsResponse, 
    MetricsSnapshotResponse, 
    SystemMetricsResponse,
    HealthResponse
)
from metrics.metrics_collector import ClientMetrics, MetricSnapshot


class TestMetricsResponse(unittest.TestCase):
    """Test cases for metrics response models"""
    
    def test_client_metrics_response_creation(self):
        """Test creating ClientMetricsResponse from ClientMetrics"""
        # Create a ClientMetrics instance
        client_metrics = ClientMetrics(
            client_id="test_client",
            total_requests=100,
            allowed_requests=80,
            rejected_requests=20,
            last_request_time=time.time(),
            first_request_time=time.time() - 3600
        )
        
        # Create response model
        response = ClientMetricsResponse.from_client_metrics(client_metrics)
        
        # Verify fields
        self.assertEqual(response.client_id, "test_client")
        self.assertEqual(response.total_requests, 100)
        self.assertEqual(response.allowed_requests, 80)
        self.assertEqual(response.rejected_requests, 20)
        self.assertEqual(response.rejection_rate, 20.0)  # 20/100 * 100
        self.assertEqual(response.last_request_time, client_metrics.last_request_time)
        self.assertEqual(response.first_request_time, client_metrics.first_request_time)
    
    def test_client_metrics_response_zero_requests(self):
        """Test ClientMetricsResponse with zero requests"""
        client_metrics = ClientMetrics(
            client_id="empty_client",
            total_requests=0,
            allowed_requests=0,
            rejected_requests=0,
            last_request_time=0,
            first_request_time=0
        )
        
        response = ClientMetricsResponse.from_client_metrics(client_metrics)
        
        self.assertEqual(response.rejection_rate, 0.0)
        self.assertEqual(response.total_requests, 0)
    
    def test_client_metrics_response_field_descriptions(self):
        """Test that ClientMetricsResponse has proper field descriptions"""
        # Get the model schema
        schema = ClientMetricsResponse.model_json_schema()
        properties = schema['properties']
        
        # Check that all fields have descriptions
        expected_fields = [
            'client_id', 'total_requests', 'allowed_requests', 
            'rejected_requests', 'last_request_time', 'first_request_time', 'rejection_rate'
        ]
        
        for field in expected_fields:
            self.assertIn(field, properties)
            self.assertIn('description', properties[field])
            self.assertIsInstance(properties[field]['description'], str)
            self.assertGreater(len(properties[field]['description']), 0)
    
    def test_metrics_snapshot_response_creation(self):
        """Test creating MetricsSnapshotResponse from MetricSnapshot"""
        current_time = time.time()
        snapshot = MetricSnapshot(
            timestamp=current_time,
            total_requests=500,
            allowed_requests=400,
            rejected_requests=100,
            avg_response_time_ms=5.5,
            active_clients=25,
            requests_per_second=10.5,
            rejection_rate=20.0
        )
        
        response = MetricsSnapshotResponse.from_snapshot(snapshot)
        
        self.assertEqual(response.timestamp, current_time)
        self.assertEqual(response.total_requests, 500)
        self.assertEqual(response.allowed_requests, 400)
        self.assertEqual(response.rejected_requests, 100)
        self.assertEqual(response.avg_response_time_ms, 5.5)
        self.assertEqual(response.active_clients, 25)
        self.assertEqual(response.requests_per_second, 10.5)
        self.assertEqual(response.rejection_rate, 20.0)
    
    def test_metrics_snapshot_response_field_descriptions(self):
        """Test that MetricsSnapshotResponse has proper field descriptions"""
        schema = MetricsSnapshotResponse.model_json_schema()
        properties = schema['properties']
        
        expected_fields = [
            'timestamp', 'total_requests', 'allowed_requests', 'rejected_requests',
            'avg_response_time_ms', 'active_clients', 'requests_per_second', 'rejection_rate'
        ]
        
        for field in expected_fields:
            self.assertIn(field, properties)
            self.assertIn('description', properties[field])
            self.assertIsInstance(properties[field]['description'], str)
    
    def test_system_metrics_response_creation(self):
        """Test creating SystemMetricsResponse"""
        # Create mock data
        current_time = time.time()
        snapshot = MetricSnapshot(
            timestamp=current_time,
            total_requests=100,
            allowed_requests=80,
            rejected_requests=20,
            avg_response_time_ms=3.0,
            active_clients=5,
            requests_per_second=2.5,
            rejection_rate=20.0
        )
        
        client_metrics = [
            ClientMetrics("client1", 50, 40, 10, current_time, current_time - 1000),
            ClientMetrics("client2", 30, 25, 5, current_time, current_time - 500)
        ]
        
        snapshots = [snapshot]
        
        response = SystemMetricsResponse(
            current_metrics=MetricsSnapshotResponse.from_snapshot(snapshot),
            uptime_seconds=3600.0,
            top_clients=[ClientMetricsResponse.from_client_metrics(c) for c in client_metrics],
            historical_snapshots=[MetricsSnapshotResponse.from_snapshot(s) for s in snapshots]
        )
        
        self.assertEqual(response.uptime_seconds, 3600.0)
        self.assertEqual(len(response.top_clients), 2)
        self.assertEqual(len(response.historical_snapshots), 1)
        self.assertEqual(response.current_metrics.total_requests, 100)
    
    def test_health_response_healthy_status(self):
        """Test HealthResponse with healthy status"""
        snapshot = MetricSnapshot(
            timestamp=time.time(),
            total_requests=100,
            allowed_requests=95,
            rejected_requests=5,
            avg_response_time_ms=8.0,
            active_clients=10,
            requests_per_second=15.0,
            rejection_rate=5.0  # Low rejection rate = healthy
        )
        
        response = HealthResponse.from_snapshot(snapshot, uptime_seconds=1800.0, memory_usage_mb=128.5)
        
        self.assertEqual(response.status, "healthy")
        self.assertEqual(response.uptime_seconds, 1800.0)
        self.assertEqual(response.total_requests, 100)
        self.assertEqual(response.current_rps, 15.0)
        self.assertEqual(response.avg_response_time_ms, 8.0)
        self.assertEqual(response.rejection_rate, 5.0)
        self.assertEqual(response.active_clients, 10)
        self.assertEqual(response.memory_usage_mb, 128.5)
    
    def test_health_response_degraded_status(self):
        """Test HealthResponse with degraded status"""
        snapshot = MetricSnapshot(
            timestamp=time.time(),
            total_requests=100,
            allowed_requests=75,
            rejected_requests=25,
            avg_response_time_ms=60.0,  # High response time = degraded
            active_clients=10,
            requests_per_second=15.0,
            rejection_rate=25.0
        )
        
        response = HealthResponse.from_snapshot(snapshot, uptime_seconds=1800.0)
        
        self.assertEqual(response.status, "degraded")
        self.assertEqual(response.rejection_rate, 25.0)
        self.assertEqual(response.avg_response_time_ms, 60.0)
        self.assertIsNone(response.memory_usage_mb)
    
    def test_health_response_unhealthy_status(self):
        """Test HealthResponse with unhealthy status"""
        snapshot = MetricSnapshot(
            timestamp=time.time(),
            total_requests=100,
            allowed_requests=40,
            rejected_requests=60,
            avg_response_time_ms=15.0,
            active_clients=10,
            requests_per_second=15.0,
            rejection_rate=60.0  # High rejection rate = unhealthy
        )
        
        response = HealthResponse.from_snapshot(snapshot, uptime_seconds=1800.0)
        
        self.assertEqual(response.status, "unhealthy")
        self.assertEqual(response.rejection_rate, 60.0)
    
    def test_health_response_field_descriptions(self):
        """Test that HealthResponse has proper field descriptions"""
        schema = HealthResponse.model_json_schema()
        properties = schema['properties']
        
        expected_fields = [
            'status', 'uptime_seconds', 'total_requests', 'current_rps',
            'avg_response_time_ms', 'rejection_rate', 'active_clients', 'memory_usage_mb'
        ]
        
        for field in expected_fields:
            self.assertIn(field, properties)
            self.assertIn('description', properties[field])
            self.assertIsInstance(properties[field]['description'], str)
    
    def test_response_serialization(self):
        """Test that all response models can be serialized to JSON"""
        current_time = time.time()
        
        # Test ClientMetricsResponse
        client_metrics = ClientMetrics("test", 10, 8, 2, current_time, current_time - 100)
        client_response = ClientMetricsResponse.from_client_metrics(client_metrics)
        client_json = client_response.model_dump_json()
        self.assertIsInstance(client_json, str)
        
        # Test MetricsSnapshotResponse
        snapshot = MetricSnapshot(current_time, 100, 80, 20, 5.0, 10, 2.0, 20.0)
        snapshot_response = MetricsSnapshotResponse.from_snapshot(snapshot)
        snapshot_json = snapshot_response.model_dump_json()
        self.assertIsInstance(snapshot_json, str)
        
        # Test HealthResponse
        health_response = HealthResponse.from_snapshot(snapshot, 3600.0, 128.0)
        health_json = health_response.model_dump_json()
        self.assertIsInstance(health_json, str)
    
    def test_response_validation(self):
        """Test response model validation"""
        # Test that required fields are enforced
        with self.assertRaises(ValueError):
            ClientMetricsResponse(
                # Missing required fields
                client_id="test"
                # Should fail validation
            )
        
        # Test valid creation
        valid_response = ClientMetricsResponse(
            client_id="test",
            total_requests=10,
            allowed_requests=8,
            rejected_requests=2,
            last_request_time=time.time(),
            first_request_time=time.time() - 100,
            rejection_rate=20.0
        )
        self.assertEqual(valid_response.client_id, "test")


if __name__ == '__main__':
    unittest.main()
