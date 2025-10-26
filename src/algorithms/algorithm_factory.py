from algorithms.rate_limit_algorithm import RateLimitAlgorithm
from algorithms.sliding_window_algorithm import SlidingWindowAlgorithm
from constants.algorithm_type import AlgorithmType


class AlgorithmFactory:
    """Factory for creating rate limiting algorithms."""

    @staticmethod
    def create_algorithm(algorithm_type: AlgorithmType) -> RateLimitAlgorithm:
        if algorithm_type == AlgorithmType.SLIDING_WINDOW:
            return SlidingWindowAlgorithm()
        raise ValueError(f"Unsupported algorithm: {algorithm_type}")
