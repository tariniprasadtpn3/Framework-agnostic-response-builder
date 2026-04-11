"""Flask adapter — wraps ResponseCore output in Flask's jsonify."""

from flask import jsonify, make_response
from ..core import ResponseCore


class FlaskResponseHelper(ResponseCore):
    """
    Drop-in replacement for Flask routes.
    Returns Flask Response objects.
    """

    @classmethod
    def build(cls, http_status, message=None, data=None,
              metadata=None, errors=None, internal_code=None, trace_id=None):
        body, status_code = super().build(
            http_status, message, data, metadata, errors, internal_code, trace_id
        )
        return make_response(jsonify(body), status_code)

    @classmethod
    def no_content(cls):
        return make_response("", 204)