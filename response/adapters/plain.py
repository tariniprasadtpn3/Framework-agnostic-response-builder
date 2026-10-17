"""
Plain adapter — returns the raw envelope, status code and headers.
Use for: Celery tasks, AWS Lambda, CLI scripts, unit tests, gRPC, WebSockets.
"""

from __future__ import annotations

from typing import Any, Dict, NamedTuple, Optional

from ..core import ResponseCore


class PlainResponse(NamedTuple):
    body: Optional[Dict[str, Any]]  # None for 204 / 304
    status_code: int
    headers: Dict[str, str]


class PlainResponseHelper(ResponseCore[PlainResponse]):
    """
    No framework. Returns a PlainResponse(body, status_code, headers) tuple.
    """

    @classmethod
    def _render(cls, body, status_code, headers) -> PlainResponse:
        return PlainResponse(body, status_code, headers)
