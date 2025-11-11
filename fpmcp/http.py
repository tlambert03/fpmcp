"""Shared HTTP session for efficient connection pooling across the application.

This module provides a singleton requests.Session that should be used for all
HTTP requests throughout the application. Benefits:

1. Connection pooling - reuses TCP connections
2. Keep-alive connections reduce latency
3. Consistent headers and configuration
4. Better performance for multiple requests
"""

from __future__ import annotations

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Singleton session
_session: requests.Session | None = None


def get_session() -> requests.Session:
    """Get or create the shared requests session.

    Returns
    -------
    requests.Session
        Configured session with connection pooling, retries, and browser-like
        headers

    Examples
    --------
    >>> from fpmcp.http import get_session
    >>> session = get_session()
    >>> response = session.get("https://example.com")
    """
    global _session
    if _session is None:
        _session = requests.Session()

        # Configure retry strategy
        retry_strategy = Retry(
            total=3,
            backoff_factor=0.5,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS"],
        )
        adapter = HTTPAdapter(
            max_retries=retry_strategy, pool_connections=10, pool_maxsize=20
        )
        _session.mount("http://", adapter)
        _session.mount("https://", adapter)

        # Add browser-like headers to avoid throttling
        _session.headers.update(
            {
                "User-Agent": (
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                ),
                "Accept": "*/*",
                "Accept-Language": "en-US,en;q=0.9",
                "Accept-Encoding": "gzip, deflate, br",
            }
        )

    return _session


def reset_session() -> None:
    """Reset the session (useful for testing).

    Examples
    --------
    >>> from fpmcp.http import reset_session
    >>> reset_session()  # Close and recreate session
    """
    global _session
    if _session is not None:
        _session.close()
        _session = None
