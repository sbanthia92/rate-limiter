import time
from algorithms.algorithm_factory import AlgorithmFactory
from algorithms.rate_limit_algorithm import RateLimitAlgorithm
from models.config_response import ConfigResponse
from models.rate_limit_response import RateLimitResponse
from metrics.metrics_collector import MetricsCollector


class RateLimiterService:
    """
    Main rate limiter service that coordinates algorithm and configuration.
    Now includes comprehensive metrics collection.
    """
    
    def __init__(self, config: ConfigResponse, enable_metrics: bool = True):
        self.config = config
        self.algorithm = AlgorithmFactory.create_algorithm(config.algorithm)
        self.metrics_collector = MetricsCollector() if enable_metrics else None

    def update_config(self, config: ConfigResponse):
        """Update rate limiting configuration."""
        if config.algorithm != self.config.algorithm:
            self.algorithm = AlgorithmFactory.create_algorithm(config.algorithm)
        self.config = config
    
    def check_rate_limit(self, client_id: str, resource: str = "default") -> RateLimitResponse:
        """Check if request should be allowed based on rate limits."""
        start_time = time.time()
        client_key = f"{client_id}:{resource}"
        
        # Process the rate limit check
        response = self.algorithm.check_request(client_key, self.config)
        
        # Record metrics if enabled
        if self.metrics_collector:
            response_time_ms = (time.time() - start_time) * 1000
            self.metrics_collector.record_request(
                client_id=client_id,
                allowed=response.allowed,
                response_time_ms=response_time_ms
            )
        
        return response
    
    def get_metrics_collector(self) -> MetricsCollector:
        """Get the metrics collector instance"""
        return self.metrics_collector
    
    def reset_metrics(self):
        """Reset all collected metrics"""
        if self.metrics_collector:
            self.metrics_collector.reset_metrics()
