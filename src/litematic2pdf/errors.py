"""User-facing errors and global limits."""



MAX_VOLUME = 2_000_000


class LitematicError(RuntimeError):
    """User-facing failure: bad/unsupported input, not a program bug."""
