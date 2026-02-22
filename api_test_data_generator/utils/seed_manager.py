"""Seed management for deterministic data generation."""
import random
import logging

logger = logging.getLogger(__name__)

_current_seed: int | None = None


def set_seed(seed: int) -> None:
    """Set the global random seed for reproducibility."""
    global _current_seed
    _current_seed = seed
    random.seed(seed)
    logger.debug(f"Global seed set to {seed}")


def get_seed() -> int | None:
    """Return the current seed value."""
    return _current_seed


def reset_seed() -> None:
    """Clear the global seed."""
    global _current_seed
    _current_seed = None
