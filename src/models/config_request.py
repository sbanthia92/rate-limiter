from pydantic import BaseModel, Field


class ConfigRequest(BaseModel):
    """API request model for configuration endpoint"""
    window_seconds: int = Field(..., description="Window size in seconds for rate limiting")
    requests_per_window: int = Field(..., description="Maximum number of requests allowed per window")
