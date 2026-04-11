"""
JsonResponseHelper — Production-grade JSON response factory for Django.

Design principles:
  - Zero magic numbers: All status codes come from HttpStatus enum.
  - Named methods per status: No caller needs to remember codes.
  - Null-safe: No field ever silently drops to None in the response body.
  - Traceable: Optional trace_id threads through every response.
  - Immutable schema: ResponseSchema is frozen; no post-construction mutation.
"""

from __future__ import annotations

from typing import Any, Union

from django.http import JsonResponse

from .enums import HttpStatus
from .schema import ResponseSchema


class JsonResponseHelper:
    """
    Stateless factory class for producing consistent Django JsonResponse objects.

    Usage:
        # Success
        return JsonResponseHelper.ok(data=results, message="Fetched successfully")

        # Client error
        return JsonResponseHelper.bad_request("Invalid sort field")

        # Server error with trace
        return JsonResponseHelper.internal_server_error(
            message="DB connection failed",
            trace_id=request.headers.get("X-Request-ID")
        )
    """

    # ------------------------------------------------------------------ #
    #  Core builder                                                        #
    # ------------------------------------------------------------------ #

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
    ) -> JsonResponse:
        """
        Core builder — all named methods delegate here.
        Resolves all None defaults before constructing the frozen ResponseSchema.
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
        return JsonResponse(schema.to_dict(), status=http_status.value)

    # ------------------------------------------------------------------ #
    #  2xx — Success                                                       #
    # ------------------------------------------------------------------ #

    @classmethod
    def ok(
        cls,
        data: Any,
        message: str = "Success",
        metadata: Union[dict, None] = None,
        internal_code: Union[int, None] = None,
        trace_id: Union[str, None] = None,
    ) -> JsonResponse:
        return cls.build(HttpStatus.OK, message, data, metadata,
                         internal_code=internal_code, trace_id=trace_id)

    @classmethod
    def created(
        cls,
        data: Any,
        message: str = "Resource Created Successfully",
        metadata: Union[dict, None] = None,
        trace_id: Union[str, None] = None,
    ) -> JsonResponse:
        return cls.build(HttpStatus.CREATED, message, data, metadata, trace_id=trace_id)

    @classmethod
    def accepted(
        cls,
        data: Any,
        message: str = "Request Accepted",
        metadata: Union[dict, None] = None,
        trace_id: Union[str, None] = None,
    ) -> JsonResponse:
        return cls.build(HttpStatus.ACCEPTED, message, data, metadata, trace_id=trace_id)

    @classmethod
    def no_content(cls) -> JsonResponse:
        """204 — No body. Django returns empty response."""
        return JsonResponse({}, status=HttpStatus.NO_CONTENT.value)

    # ------------------------------------------------------------------ #
    #  3xx — Redirection                                                   #
    # ------------------------------------------------------------------ #

    @classmethod
    def moved_permanently(cls, message: Union[str, None] = None) -> JsonResponse:
        return cls.build(HttpStatus.MOVED_PERMANENTLY, message)

    @classmethod
    def found(cls, message: Union[str, None] = None) -> JsonResponse:
        return cls.build(HttpStatus.FOUND, message)

    @classmethod
    def not_modified(cls, message: Union[str, None] = None) -> JsonResponse:
        return cls.build(HttpStatus.NOT_MODIFIED, message)

    # ------------------------------------------------------------------ #
    #  4xx — Client Errors                                                 #
    # ------------------------------------------------------------------ #

    @classmethod
    def bad_request(
        cls,
        message: Union[str, None] = None,
        errors: Union[list[dict], None] = None,
        trace_id: Union[str, None] = None,
    ) -> JsonResponse:
        return cls.build(HttpStatus.BAD_REQUEST, message, errors=errors, trace_id=trace_id)

    @classmethod
    def unauthorized(
        cls,
        message: Union[str, None] = None,
        errors: Union[list[dict], None] = None,
        trace_id: Union[str, None] = None,
    ) -> JsonResponse:
        return cls.build(HttpStatus.UNAUTHORIZED, message, errors=errors, trace_id=trace_id)

    @classmethod
    def forbidden(
        cls,
        message: Union[str, None] = None,
        errors: Union[list[dict], None] = None,
        trace_id: Union[str, None] = None,
    ) -> JsonResponse:
        return cls.build(HttpStatus.FORBIDDEN, message, errors=errors, trace_id=trace_id)

    @classmethod
    def not_found(
        cls,
        message: Union[str, None] = None,
        errors: Union[list[dict], None] = None,
        trace_id: Union[str, None] = None,
    ) -> JsonResponse:
        return cls.build(HttpStatus.NOT_FOUND, message, errors=errors, trace_id=trace_id)

    @classmethod
    def method_not_allowed(
        cls,
        message: Union[str, None] = None,
        trace_id: Union[str, None] = None,
    ) -> JsonResponse:
        return cls.build(HttpStatus.METHOD_NOT_ALLOWED, message, trace_id=trace_id)

    @classmethod
    def request_timeout(
        cls,
        message: Union[str, None] = None,
        trace_id: Union[str, None] = None,
    ) -> JsonResponse:
        return cls.build(HttpStatus.REQUEST_TIMEOUT, message, trace_id=trace_id)

    @classmethod
    def conflict(
        cls,
        message: Union[str, None] = None,
        errors: Union[list[dict], None] = None,
        trace_id: Union[str, None] = None,
    ) -> JsonResponse:
        return cls.build(HttpStatus.CONFLICT, message, errors=errors, trace_id=trace_id)

    # ------------------------------------------------------------------ #
    #  5xx — Server Errors                                                 #
    # ------------------------------------------------------------------ #

    @classmethod
    def internal_server_error(
        cls,
        message: Union[str, None] = None,
        errors: Union[list[dict], None] = None,
        trace_id: Union[str, None] = None,
    ) -> JsonResponse:
        return cls.build(HttpStatus.INTERNAL_SERVER_ERROR, message, errors=errors, trace_id=trace_id)

    @classmethod
    def not_implemented(
        cls,
        message: Union[str, None] = None,
        trace_id: Union[str, None] = None,
    ) -> JsonResponse:
        return cls.build(HttpStatus.NOT_IMPLEMENTED, message, trace_id=trace_id)

    @classmethod
    def bad_gateway(
        cls,
        message: Union[str, None] = None,
        trace_id: Union[str, None] = None,
    ) -> JsonResponse:
        return cls.build(HttpStatus.BAD_GATEWAY, message, trace_id=trace_id)

    @classmethod
    def service_unavailable(
        cls,
        message: Union[str, None] = None,
        trace_id: Union[str, None] = None,
    ) -> JsonResponse:
        return cls.build(HttpStatus.SERVICE_UNAVAILABLE, message, trace_id=trace_id)

    @classmethod
    def gateway_timeout(
        cls,
        message: Union[str, None] = None,
        trace_id: Union[str, None] = None,
    ) -> JsonResponse:
        return cls.build(HttpStatus.GATEWAY_TIMEOUT, message, trace_id=trace_id)