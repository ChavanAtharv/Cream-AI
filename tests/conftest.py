"""Global test fixtures."""

import pytest

from app.cache import CACHE


@pytest.fixture(autouse=True)
def reset_cache():
    """Ensure in-memory cache is empty before and after every test."""
    CACHE.clear()
    yield
    CACHE.clear()
