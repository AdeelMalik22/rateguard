from enum import Enum

class Algorithm(str, Enum):
    FIXED_WINDOW = "fixed_window"
    TOKEN_BUCKET = "token_bucket"
