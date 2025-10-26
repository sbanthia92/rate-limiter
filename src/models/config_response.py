from pydantic import BaseModel, Field
from constants.algorithm_type import AlgorithmType


class ConfigResponse(BaseModel):
    """Configuration for rate limiting"""
    window_seconds: int = Field(..., description="Window size in seconds for rate limiting")
    requests_per_window: int = Field(..., description="Maximum number of requests allowed per window")
    algorithm: AlgorithmType = Field(AlgorithmType.SLIDING_WINDOW, description="Rate limiting algorithm to use")
