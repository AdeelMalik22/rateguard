from typing import Dict, Type
from requestguard.core.enums import Algorithm
from requestguard.algorithms.fixed_window import FixedWindowLimiter
from requestguard.algorithms.token_bucket import TokenBucketLimiter

_REGISTRY: Dict[Algorithm, Type] = {
    Algorithm.FIXED_WINDOW: FixedWindowLimiter,
    Algorithm.TOKEN_BUCKET: TokenBucketLimiter
}

def get_algorithm(algorithm: Algorithm) -> Type:
    if algorithm not in _REGISTRY:
        raise ValueError(f"Unknown algorithm: {algorithm}")
    return _REGISTRY[algorithm]

def register_algorithm(algorithm: Algorithm, cls: Type):
    _REGISTRY[algorithm] = cls
