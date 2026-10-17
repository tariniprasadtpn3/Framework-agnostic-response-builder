"""Flask adapter — wraps ResponseCore output in Flask's jsonify."""

from __future__ import annotations

from flask import Response, jsonify

from ..core import ResponseCore


class FlaskResponseHelper(ResponseCore[Response]):
    """
    Drop-in helper for Flask routes (must be called inside an app context).
    Returns a JSON Response, or a bodiless Response for 204 / 304.
    """

    @classmethod
    def _render(cls, body, status_code, headers) -> Response:
        if body is None:
            return Response(status=status_code, headers=headers)
        response = jsonify(body)
        response.status_code = status_code
        response.headers.update(headers)
        return response
