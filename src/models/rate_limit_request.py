from pydantic import BaseModel, Field

class RateLimitRequest(BaseModel):
    """API request model for rate limit check endpoint"""
    client_id: str = Field(..., description="Unique identifier for the client making the request")
    resource: str = Field("default", description="Resource being accessed (defaults to 'default')")
