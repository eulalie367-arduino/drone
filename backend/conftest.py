import pytest


@pytest.fixture(autouse=True)
def _anyio_backend():
    """Use asyncio as the default backend for async tests."""
    return "asyncio"
