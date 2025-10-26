from typing import List, Optional
from pydantic import BaseModel, Field


class ClientMetricsResponse(BaseModel):
    """Response model for individual client metrics"""
    client_id: str = Field(..., description="Unique identifier for the client")
    total_requests: int = Field(..., description="Total number of requests made by this client")
    allowed_requests: int = Field(..., description="Number of requests that were allowed")
    rejected_requests: int = Field(..., description="Number of requests that were rejected")
    last_request_time: float = Field(..., description="Timestamp of the last request from this client")
    first_request_time: float = Field(..., description="Timestamp of the first request from this client")
    rejection_rate: float = Field(..., description="Percentage of requests that were rejected")
    
    @classmethod
    def from_client_metrics(cls, client_metrics):
        """Create response from ClientMetrics dataclass"""
        rejection_rate = (
            (client_metrics.rejected_requests / client_metrics.total_requests * 100)
            if client_metrics.total_requests > 0 else 0.0
        )
        
        return cls(
            client_id=client_metrics.client_id,
            total_requests=client_metrics.total_requests,
            allowed_requests=client_metrics.allowed_requests,
            rejected_requests=client_metrics.rejected_requests,
            last_request_time=client_metrics.last_request_time,
            first_request_time=client_metrics.first_request_time,
            rejection_rate=rejection_rate
        )


class MetricsSnapshotResponse(BaseModel):
    """Response model for metrics snapshot"""
    timestamp: float = Field(..., description="Unix timestamp when the snapshot was taken")
    total_requests: int = Field(..., description="Total number of requests processed")
    allowed_requests: int = Field(..., description="Number of requests that were allowed")
    rejected_requests: int = Field(..., description="Number of requests that were rejected")
    avg_response_time_ms: float = Field(..., description="Average response time in milliseconds")
    active_clients: int = Field(..., description="Number of clients active in the last 5 minutes")
    requests_per_second: float = Field(..., description="Current requests per second (last minute average)")
    rejection_rate: float = Field(..., description="Percentage of requests that were rejected")
    
    @classmethod
    def from_snapshot(cls, snapshot):
        """Create response from MetricSnapshot dataclass"""
        return cls(
            timestamp=snapshot.timestamp,
            total_requests=snapshot.total_requests,
            allowed_requests=snapshot.allowed_requests,
            rejected_requests=snapshot.rejected_requests,
            avg_response_time_ms=snapshot.avg_response_time_ms,
            active_clients=snapshot.active_clients,
            requests_per_second=snapshot.requests_per_second,
            rejection_rate=snapshot.rejection_rate
        )


class SystemMetricsResponse(BaseModel):
    """Response model for comprehensive system metrics"""
    current_metrics: MetricsSnapshotResponse = Field(..., description="Current system metrics snapshot")
    uptime_seconds: float = Field(..., description="Service uptime in seconds")
    top_clients: List[ClientMetricsResponse] = Field(..., description="Top clients by request volume")
    historical_snapshots: List[MetricsSnapshotResponse] = Field(..., description="Historical metrics snapshots")


class HealthResponse(BaseModel):
    """Response model for health check endpoint"""
    status: str = Field(..., description="Service health status (healthy/degraded/unhealthy)")
    uptime_seconds: float = Field(..., description="Service uptime in seconds")
    total_requests: int = Field(..., description="Total requests processed since startup")
    current_rps: float = Field(..., description="Current requests per second")
    avg_response_time_ms: float = Field(..., description="Average response time in milliseconds")
    rejection_rate: float = Field(..., description="Current rejection rate percentage")
    active_clients: int = Field(..., description="Number of active clients")
    memory_usage_mb: Optional[float] = Field(None, description="Estimated memory usage in MB")
    
    @classmethod
    def from_snapshot(cls, snapshot, uptime_seconds: float, memory_usage_mb: Optional[float] = None):
        """Create health response from metrics snapshot"""
        # Determine health status based on metrics
        if snapshot.rejection_rate > 50:
            status = "unhealthy"
        elif snapshot.rejection_rate > 20 or snapshot.avg_response_time_ms > 50:
            status = "degraded"
        else:
            status = "healthy"
        
        return cls(
            status=status,
            uptime_seconds=uptime_seconds,
            total_requests=snapshot.total_requests,
            current_rps=snapshot.requests_per_second,
            avg_response_time_ms=snapshot.avg_response_time_ms,
            rejection_rate=snapshot.rejection_rate,
            active_clients=snapshot.active_clients,
            memory_usage_mb=memory_usage_mb
        )
