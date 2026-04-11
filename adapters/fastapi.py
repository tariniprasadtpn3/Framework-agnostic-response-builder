"""FastAPI adapter — wraps ResponseCore output in FastAPI's JSONResponse."""

from fastapi.responses import JSONResponse
from ..core import ResponseCore


class FastAPIResponseHelper(ResponseCore):
    """
    Drop-in replacement for FastAPI routes.
    Returns FastAPI JSONResponse objects.
    """

    @classmethod
    def build(cls, http_status, message=None, data=None,
              metadata=None, errors=None, internal_code=None, trace_id=None):
        body, status_code = super().build(
            http_status, message, data, metadata, errors, internal_code, trace_id
        )
        return JSONResponse(content=body, status_code=status_code)

    @classmethod
    def no_content(cls):
        return JSONResponse(content={}, status_code=204)