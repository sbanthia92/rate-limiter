from enum import Enum


class AlgorithmType(str, Enum):
    """Available rate limiting algorithms"""
    SLIDING_WINDOW = "SLIDING_WINDOW"
