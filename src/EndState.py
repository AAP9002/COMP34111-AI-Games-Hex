from enum import Enum


class EndState(Enum):
    """This enum describes the possible end conditions of a match."""

    WIN = 0
    TIMEOUT = 1
    BAD_MOVE = 2
    FAILED_LOAD = 3
