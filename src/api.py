from fastapi import FastAPI, HTTPException
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
from constants.algorithm_type import AlgorithmType
from models.config_request import ConfigRequest
from models.rate_limit_request import RateLimitRequest
from models.rate_limit_response import RateLimitResponse
from models.config_response import ConfigResponse
from models.metrics_response import (
    SystemMetricsResponse, 
    HealthResponse, 
    ClientMetricsResponse,
    MetricsSnapshotResponse
)
from rate_limiter_service import RateLimiterService
import uvicorn
from pydantic import BaseModel
from typing import List, Optional

app = FastAPI(title="Rate Limiter Service")

# Initialize rate limiter with default sliding window config
rate_limiter = RateLimiterService(ConfigResponse(window_seconds=60, requests_per_window=100, algorithm=AlgorithmType.SLIDING_WINDOW))

class TestResponse(BaseModel):
    status: str

@app.get("/test", response_model=TestResponse)
async def test():
    """Simple test endpoint"""
    return TestResponse(status="working")

@app.post("/api/v1/ratelimit", response_model=RateLimitResponse)
async def check_rate_limit(request: RateLimitRequest):
    """Check if a request should be allowed"""
    import time
    
    # Measure just the rate limiting logic
    start_time = time.perf_counter()
    result = rate_limiter.check_rate_limit(request.client_id, request.resource)
    end_time = time.perf_counter()
    
    # Calculate processing time in microseconds for precision
    processing_time_us = (end_time - start_time) * 1_000_000
    
    return RateLimitResponse(
        allowed=result.allowed,
        remaining=result.remaining,
        processing_time_us=round(processing_time_us, 2),
        retry_after=result.retry_after if not result.allowed and result.retry_after > 0 else None
    )

@app.post("/api/v1/configure", response_model=ConfigResponse)
async def configure(request: ConfigRequest):
    """Update rate limiting configuration"""
    config = ConfigResponse(
        window_seconds=request.window_seconds, 
        requests_per_window=request.requests_per_window,
        algorithm=AlgorithmType.SLIDING_WINDOW
    )
    rate_limiter.update_config(config)
    
    return ConfigResponse(
        window_seconds=config.window_seconds,
        requests_per_window=config.requests_per_window,
        algorithm="SLIDING_WINDOW"
    )


@app.get("/api/v1/health", response_model=HealthResponse)
async def health_check():
    """Get service health status and key metrics"""
    metrics_collector = rate_limiter.get_metrics_collector()
    if not metrics_collector:
        # If metrics are disabled, return basic health
        return HealthResponse(
            status="healthy",
            uptime_seconds=0,
            total_requests=0,
            current_rps=0.0,
            avg_response_time_ms=0.0,
            rejection_rate=0.0,
            active_clients=0
        )
    
    current_metrics = metrics_collector.get_current_metrics()
    uptime = metrics_collector.get_uptime_seconds()
    
    # Get memory usage if psutil is available
    memory_usage_mb = None
    if PSUTIL_AVAILABLE:
        try:
            process = psutil.Process()
            memory_usage_mb = process.memory_info().rss / 1024 / 1024
        except Exception:
            memory_usage_mb = None
    
    return HealthResponse.from_snapshot(current_metrics, uptime, memory_usage_mb)


if __name__ == '__main__':
    uvicorn.run(
        app, 
        host='0.0.0.0', 
        port=5000, 
        log_level="error",
        workers=1,
        loop="asyncio",
        http="h11",
        access_log=False,
        backlog=2048,
        limit_concurrency=1000,
        limit_max_requests=10000
    )
