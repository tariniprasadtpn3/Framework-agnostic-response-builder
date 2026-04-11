"""
Plain adapter — returns raw dict + status code.
Use for: Celery tasks, AWS Lambda, CLI scripts, unit tests, gRPC, WebSockets.
"""

from ..core import ResponseCore


class PlainResponseHelper(ResponseCore):
    """
    No framework. Returns (dict, int) tuple directly.
    Perfect for Celery, Lambda, or any non-HTTP context.
    """
    pass  # ResponseCore.build() already returns (dict, int) — nothing to override