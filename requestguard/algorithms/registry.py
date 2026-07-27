from typing import Dict, Type
from requestguard.core.enums import Algorithm
from requestguard.algorithms.fixed_window import FixedWindowLimiter
from requestguard.algorithms.token_bucket import TokenBucketLimiter
from requestguard.algorithms.leaky_bucket import LeakyBucketLimiter
from requestguard.algorithms.sliding_window import SlidingWindowLimiter
from requestguard.algorithms.sliding_window_counter import SlidingWindowCounterLimiter
from requestguard.algorithms.gcra import GCRALimiter
from requestguard.core.exceptions import UnsupportedAlgorithmError

_REGISTRY: Dict[Algorithm, Type] = {
    Algorithm.FIXED_WINDOW: FixedWindowLimiter,
    Algorithm.TOKEN_BUCKET: TokenBucketLimiter,
    Algorithm.LEAKY_BUCKET: LeakyBucketLimiter,
    Algorithm.SLIDING_WINDOW: SlidingWindowLimiter,
    Algorithm.SLIDING_WINDOW_COUNTER: SlidingWindowCounterLimiter,
    Algorithm.GCRA: GCRALimiter,
}

def get_algorithm(algorithm: Algorithm) -> Type:
    if algorithm not in _REGISTRY:
        supported = ", ".join(item.value for item in _REGISTRY)
        raise UnsupportedAlgorithmError(
            f"Unsupported rate-limit algorithm: {algorithm}. "
            f"Supported algorithms: {supported}."
        )
    return _REGISTRY[algorithm]

def register_algorithm(algorithm: Algorithm, cls: Type):
    _REGISTRY[algorithm] = cls
