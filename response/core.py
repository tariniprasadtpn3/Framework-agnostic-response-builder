"""
Framework-agnostic response builder.
Returns plain Python dicts — no framework imports anywhere here.
"""

from __future__ import annotations
from typing import Any, Union

from .enums import HttpStatus
from .schema import ResponseSchema


class ResponseCore:
    """
    Pure Python response factory.
    All framework adapters delegate to this class.
    """

    @classmethod
    def build(
        cls,
        http_status: HttpStatus,
        message: Union[str, None] = None,
        data: Any = None,
        metadata: Union[dict[str, Any], None] = None,
        errors: Union[list[dict[str, Any]], None] = None,
        internal_code: Union[int, None] = None,
        trace_id: Union[str, None] = None,
    ) -> tuple[dict[str, Any], int]:
        """
        Returns a (body_dict, http_status_code) tuple.
        Adapters consume this and wrap in their own response object.
        """
        schema = ResponseSchema(
            http_status=http_status,
            internal_code=internal_code if internal_code is not None else http_status.value,
            message=message if message is not None else http_status.message,
            data=data if data is not None else ([] if not http_status.is_success else {}),
            metadata=metadata or {},
            errors=errors or [],
            trace_id=trace_id,
        )
        return schema.to_dict(), http_status.value

    # ------------------------------------------------------------------ #
    #  2xx
    # ------------------------------------------------------------------ #
    @classmethod
    def ok(cls, data: Any, message: str = "Success",
           metadata: dict = None, trace_id: str = None):
        return cls.build(HttpStatus.OK, message, data, metadata, trace_id=trace_id)

    @classmethod
    def created(cls, data: Any, message: str = "Resource Created Successfully",
                metadata: dict = None, trace_id: str = None):
        return cls.build(HttpStatus.CREATED, message, data, metadata, trace_id=trace_id)

    @classmethod
    def accepted(cls, data: Any, message: str = "Request Accepted",
                 metadata: dict = None, trace_id: str = None):
        return cls.build(HttpStatus.ACCEPTED, message, data, metadata, trace_id=trace_id)

    @classmethod
    def no_content(cls):
        return {}, 204

    # ------------------------------------------------------------------ #
    #  3xx
    # ------------------------------------------------------------------ #
    @classmethod
    def moved_permanently(cls, message: str = None):
        return cls.build(HttpStatus.MOVED_PERMANENTLY, message)

    @classmethod
    def not_modified(cls, message: str = None):
        return cls.build(HttpStatus.NOT_MODIFIED, message)

    # ------------------------------------------------------------------ #
    #  4xx
    # ------------------------------------------------------------------ #
    @classmethod
    def bad_request(cls, message: str = None, errors: list = None, trace_id: str = None):
        return cls.build(HttpStatus.BAD_REQUEST, message, errors=errors, trace_id=trace_id)

    @classmethod
    def unauthorized(cls, message: str = None, errors: list = None, trace_id: str = None):
        return cls.build(HttpStatus.UNAUTHORIZED, message, errors=errors, trace_id=trace_id)

    @classmethod
    def forbidden(cls, message: str = None, errors: list = None, trace_id: str = None):
        return cls.build(HttpStatus.FORBIDDEN, message, errors=errors, trace_id=trace_id)

    @classmethod
    def not_found(cls, message: str = None, errors: list = None, trace_id: str = None):
        return cls.build(HttpStatus.NOT_FOUND, message, errors=errors, trace_id=trace_id)

    @classmethod
    def method_not_allowed(cls, message: str = None, trace_id: str = None):
        return cls.build(HttpStatus.METHOD_NOT_ALLOWED, message, trace_id=trace_id)

    @classmethod
    def request_timeout(cls, message: str = None, trace_id: str = None):
        return cls.build(HttpStatus.REQUEST_TIMEOUT, message, trace_id=trace_id)

    @classmethod
    def conflict(cls, message: str = None, errors: list = None, trace_id: str = None):
        return cls.build(HttpStatus.CONFLICT, message, errors=errors, trace_id=trace_id)

    # ------------------------------------------------------------------ #
    #  5xx
    # ------------------------------------------------------------------ #
    @classmethod
    def internal_server_error(cls, message: str = None, errors: list = None, trace_id: str = None):
        return cls.build(HttpStatus.INTERNAL_SERVER_ERROR, message, errors=errors, trace_id=trace_id)

    @classmethod
    def not_implemented(cls, message: str = None, trace_id: str = None):
        return cls.build(HttpStatus.NOT_IMPLEMENTED, message, trace_id=trace_id)

    @classmethod
    def bad_gateway(cls, message: str = None, trace_id: str = None):
        return cls.build(HttpStatus.BAD_GATEWAY, message, trace_id=trace_id)

    @classmethod
    def service_unavailable(cls, message: str = None, trace_id: str = None):
        return cls.build(HttpStatus.SERVICE_UNAVAILABLE, message, trace_id=trace_id)

    @classmethod
    def gateway_timeout(cls, message: str = None, trace_id: str = None):
        return cls.build(HttpStatus.GATEWAY_TIMEOUT, message, trace_id=trace_id)