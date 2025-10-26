from abc import ABC, abstractmethod

from models.config_response import ConfigResponse
from models.rate_limit_response import RateLimitResponse


class RateLimitAlgorithm(ABC):
    """
    Abstract base class for rate limiting algorithms.
    
    This defines the interface that all rate limiting algorithms must implement.
    New algorithms can be added by extending this class.
    """

    @abstractmethod
    def check_request(self,  client_key: str, config: ConfigResponse) -> RateLimitResponse:
        """Check if a request should be allowed."""
        pass