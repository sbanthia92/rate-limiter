from pydantic import BaseModel, Field
from typing import Optional

class RateLimitResponse(BaseModel):
    """API response model for rate limit check endpoint"""
    allowed: bool = Field(..., description="Whether the request is allowed")
    remaining: int = Field(..., description="Number of requests remaining in the current window")
    processing_time_us: Optional[float] = Field(None, description="Processing time in microseconds")
    retry_after: Optional[int] = Field(None, description="Seconds to wait before retrying (only present when allowed=false)")
