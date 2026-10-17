"""FastAPI adapter — wraps ResponseCore output in FastAPI's JSONResponse."""

from __future__ import annotations

from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse, Response

from ..core import ResponseCore


class FastAPIResponseHelper(ResponseCore[Response]):
    """
    Drop-in helper for FastAPI routes.
    Returns JSONResponse, or a bodiless Response for 204 / 304.
    """

    @classmethod
    def _render(cls, body, status_code, headers) -> Response:
        if body is None:
            return Response(status_code=status_code, headers=headers)
        # jsonable_encoder handles datetime, Decimal, UUID and Pydantic models,
        # which plain JSONResponse would reject.
        return JSONResponse(content=jsonable_encoder(body), status_code=status_code,
                            headers=headers)
