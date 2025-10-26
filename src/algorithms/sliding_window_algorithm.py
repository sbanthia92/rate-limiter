import threading
import time
from typing import Dict, Tuple
from algorithms.rate_limit_algorithm import RateLimitAlgorithm
from models.config_response import ConfigResponse
from models.rate_limit_response import RateLimitResponse


class SlidingWindowAlgorithm(RateLimitAlgorithm):
    """
    Ultra-optimized Sliding Window rate limiting algorithm.
    
    Uses a counter-based approach with minimal locking for sub-millisecond performance.
    Divides the window into buckets for efficient cleanup and counting.
    """
    
    def __init__(self):
        # Use smaller buckets for more precise sliding window but balance with performance
        self.bucket_size = 0.5  # 0.5 second per bucket for better precision
        self.client_data: Dict[str, Tuple[Dict[int, int], threading.Lock]] = {}
        self.global_lock = threading.Lock()
    
    def _get_client_data(self, client_key: str) -> Tuple[Dict[int, int], threading.Lock]:
        """Get or create client data with minimal locking"""
        if client_key in self.client_data:
            return self.client_data[client_key]
        
        with self.global_lock:
            if client_key not in self.client_data:
                self.client_data[client_key] = ({}, threading.Lock())
            return self.client_data[client_key]
    
    def _cleanup_expired_buckets(self, buckets: Dict[int, int], current_bucket: int, window_buckets: int):
        """Remove expired buckets efficiently - inline for speed"""
        min_bucket = current_bucket - window_buckets
        # Use list comprehension and direct deletion for speed
        keys_to_delete = [k for k in buckets if k <= min_bucket]
        for k in keys_to_delete:
            del buckets[k]
    
    def check_request(self, client_key: str, config: ConfigResponse) -> RateLimitResponse:
        """Check if request is allowed using ultra-optimized sliding window algorithm"""
        current_time = time.time()
        current_bucket = int(current_time / self.bucket_size)
        window_buckets = int(config.window_seconds / self.bucket_size)
        min_bucket = current_bucket - window_buckets
        
        buckets, lock = self._get_client_data(client_key)
        
        with lock:
            # Efficient cleanup strategy - only clean when needed
            if len(buckets) > window_buckets + 3:
                # Store valid buckets before clearing
                valid_buckets = {k: v for k, v in buckets.items() if k > min_bucket}
                buckets.clear()
                buckets.update(valid_buckets)
            
            # Count current requests in the window - optimized loop
            current_requests = sum(count for bucket_id, count in buckets.items() if bucket_id > min_bucket)
            
            if current_requests < config.requests_per_window:
                # Allow request and increment counter
                if current_bucket in buckets:
                    buckets[current_bucket] += 1
                else:
                    buckets[current_bucket] = 1
                remaining = config.requests_per_window - current_requests - 1
                return RateLimitResponse(allowed=True, remaining=remaining, retry_after=None)
            else:
                # Reject request - calculate retry_after
                retry_after = max(1, int(self.bucket_size * 2))  # More conservative retry
                return RateLimitResponse(allowed=False, remaining=0, retry_after=retry_after)
