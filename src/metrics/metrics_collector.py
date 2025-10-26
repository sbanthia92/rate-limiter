import threading
import time
from typing import Dict, List
from dataclasses import dataclass, field
from collections import defaultdict, deque


@dataclass
class MetricSnapshot:
    """Snapshot of metrics at a point in time"""
    timestamp: float
    total_requests: int
    allowed_requests: int
    rejected_requests: int
    avg_response_time_ms: float
    active_clients: int
    requests_per_second: float
    rejection_rate: float


@dataclass
class ClientMetrics:
    """Per-client metrics tracking"""
    client_id: str
    total_requests: int = 0
    allowed_requests: int = 0
    rejected_requests: int = 0
    last_request_time: float = 0
    first_request_time: float = 0


class MetricsCollector:
    """
    Thread-safe metrics collection service for rate limiter.
    
    Collects and aggregates metrics including:
    - Request counts (total, allowed, rejected)
    - Response times
    - Client activity
    - Rate limiting effectiveness
    """
    
    def __init__(self, history_window_seconds: int = 300):  # 5 minutes default
        self.history_window_seconds = history_window_seconds
        self.lock = threading.Lock()
        
        # Global counters
        self.total_requests = 0
        self.allowed_requests = 0
        self.rejected_requests = 0
        
        # Response time tracking
        self.response_times: deque = deque(maxlen=1000)  # Keep last 1000 response times
        
        # Client tracking
        self.client_metrics: Dict[str, ClientMetrics] = {}
        
        # Time-series data for rates
        self.request_timestamps: deque = deque()
        
        # Historical snapshots
        self.snapshots: deque = deque(maxlen=100)  # Keep last 100 snapshots
        
        # Start time
        self.start_time = time.time()
    
    def record_request(self, client_id: str, allowed: bool, response_time_ms: float):
        """Record a rate limit check request"""
        current_time = time.time()
        
        with self.lock:
            # Update global counters
            self.total_requests += 1
            if allowed:
                self.allowed_requests += 1
            else:
                self.rejected_requests += 1
            
            # Record response time
            self.response_times.append(response_time_ms)
            
            # Record timestamp for rate calculation
            self.request_timestamps.append(current_time)
            
            # Update client metrics
            if client_id not in self.client_metrics:
                self.client_metrics[client_id] = ClientMetrics(
                    client_id=client_id,
                    first_request_time=current_time
                )
            
            client_metric = self.client_metrics[client_id]
            client_metric.total_requests += 1
            client_metric.last_request_time = current_time
            if allowed:
                client_metric.allowed_requests += 1
            else:
                client_metric.rejected_requests += 1
            
            # Clean old timestamps
            self._cleanup_old_data(current_time)
    
    def _cleanup_old_data(self, current_time: float):
        """Remove data older than history window"""
        cutoff_time = current_time - self.history_window_seconds
        
        # Clean request timestamps
        while self.request_timestamps and self.request_timestamps[0] < cutoff_time:
            self.request_timestamps.popleft()
    
    def get_current_metrics(self) -> MetricSnapshot:
        """Get current metrics snapshot"""
        current_time = time.time()
        
        with self.lock:
            # Calculate requests per second
            recent_requests = len([ts for ts in self.request_timestamps 
                                 if ts > current_time - 60])  # Last minute
            requests_per_second = recent_requests / 60.0
            
            # Calculate average response time
            avg_response_time = (
                sum(self.response_times) / len(self.response_times) 
                if self.response_times else 0.0
            )
            
            # Calculate rejection rate
            rejection_rate = (
                (self.rejected_requests / self.total_requests * 100) 
                if self.total_requests > 0 else 0.0
            )
            
            # Count active clients (clients with requests in last 5 minutes)
            active_clients = len([
                client for client in self.client_metrics.values()
                if client.last_request_time > current_time - 300
            ])
            
            snapshot = MetricSnapshot(
                timestamp=current_time,
                total_requests=self.total_requests,
                allowed_requests=self.allowed_requests,
                rejected_requests=self.rejected_requests,
                avg_response_time_ms=avg_response_time,
                active_clients=active_clients,
                requests_per_second=requests_per_second,
                rejection_rate=rejection_rate
            )
            
            # Store snapshot
            self.snapshots.append(snapshot)
            
            return snapshot
    
    def get_client_metrics(self) -> List[ClientMetrics]:
        """Get metrics for all clients"""
        with self.lock:
            return list(self.client_metrics.values())
    
    def get_top_clients(self, limit: int = 10) -> List[ClientMetrics]:
        """Get top clients by request count"""
        with self.lock:
            return sorted(
                self.client_metrics.values(),
                key=lambda c: c.total_requests,
                reverse=True
            )[:limit]
    
    def get_historical_snapshots(self, limit: int = 50) -> List[MetricSnapshot]:
        """Get historical metric snapshots"""
        with self.lock:
            return list(self.snapshots)[-limit:]
    
    def reset_metrics(self):
        """Reset all metrics (useful for testing)"""
        with self.lock:
            self.total_requests = 0
            self.allowed_requests = 0
            self.rejected_requests = 0
            self.response_times.clear()
            self.client_metrics.clear()
            self.request_timestamps.clear()
            self.snapshots.clear()
            self.start_time = time.time()
    
    def get_uptime_seconds(self) -> float:
        """Get service uptime in seconds"""
        return time.time() - self.start_time
