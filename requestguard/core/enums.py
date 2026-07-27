from enum import Enum

class Algorithm(str, Enum):
    FIXED_WINDOW = "fixed_window"
    TOKEN_BUCKET = "token_bucket"
    LEAKY_BUCKET = "leaky_bucket"
    SLIDING_WINDOW = "sliding_window"
    SLIDING_WINDOW_COUNTER = "sliding_window_counter"
    GCRA = "gcra"
