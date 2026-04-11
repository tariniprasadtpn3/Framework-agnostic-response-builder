"""
Centralized HTTP status code registry using Python Enum.
Eliminates magic numbers across the entire codebase.
"""

from enum import Enum


class HttpStatus(int, Enum):
    """
    Strongly-typed HTTP status codes with built-in message resolution.
    Inherits from int for direct Django JsonResponse compatibility.
    """

    # 2xx — Success
    OK = 200
    CREATED = 201
    ACCEPTED = 202
    NO_CONTENT = 204

    # 3xx — Redirection
    MOVED_PERMANENTLY = 301
    FOUND = 302
    NOT_MODIFIED = 304

    # 4xx — Client Errors
    BAD_REQUEST = 400
    UNAUTHORIZED = 401
    FORBIDDEN = 403
    NOT_FOUND = 404
    METHOD_NOT_ALLOWED = 405
    REQUEST_TIMEOUT = 408
    CONFLICT = 409

    # 5xx — Server Errors
    INTERNAL_SERVER_ERROR = 500
    NOT_IMPLEMENTED = 501
    BAD_GATEWAY = 502
    SERVICE_UNAVAILABLE = 503
    GATEWAY_TIMEOUT = 504

    @property
    def message(self) -> str:
        """Returns the canonical message for this status code."""
        return _STATUS_MESSAGES.get(self.value, "Unknown Status")

    @property
    def is_success(self) -> bool:
        return 200 <= self.value < 300

    @property
    def is_redirect(self) -> bool:
        return 300 <= self.value < 400

    @property
    def is_client_error(self) -> bool:
        return 400 <= self.value < 500

    @property
    def is_server_error(self) -> bool:
        return 500 <= self.value < 600


_STATUS_MESSAGES: dict[int, str] = {
    200: "Success",
    201: "Resource Created Successfully",
    202: "Request Accepted",
    204: "No Content",
    301: "Resource Moved Permanently",
    302: "Resource Temporarily Moved",
    304: "Resource Not Modified",
    400: "Bad Request",
    401: "Unauthorized Access",
    403: "Forbidden Resource",
    404: "Requested Resource Not Found",
    405: "Method Not Allowed",
    408: "Request Timed Out",
    409: "Conflict",
    500: "Internal Server Error",
    501: "Not Implemented",
    502: "Bad Gateway Error",
    503: "Service Unavailable",
    504: "Gateway Timeout",
}