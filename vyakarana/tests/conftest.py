"""conftest.py — pytest fixtures for vyakarana integration tests.

One socket connection is opened per test session and shared across all tests.
Set VYAKARANA_SOCKET env var or pass --socket on the CLI to override the path.

Start the server before running:
    cd vyakarana && ./_build/default/bin/vyakarana.exe --quiet-startup --socket /tmp/vy.sock ../brahman &

Then run tests:
    cd vyakarana/tests && ../../.venv/bin/pytest
    or: cd vyakarana/tests && pytest            # if venv is activated
"""

import os
from collections.abc import Generator
import pytest
from vy import Client, DEFAULT_SOCKET


def pytest_addoption(parser):
    parser.addoption(
        "--socket",
        default=None,
        help="Path to vyakarana Unix socket (default: $VYAKARANA_SOCKET or /tmp/vyakarana.sock)",
    )


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "xfail_known: mark test as a known failure (feature not yet implemented)",
    )


@pytest.fixture(scope="session")
def vy(request) -> Client:
    """Session-scoped vyakarana client. One connection, reused for all tests."""
    socket_path = request.config.getoption("--socket") or DEFAULT_SOCKET
    client = Client(socket_path)
    yield client
    client.close()
