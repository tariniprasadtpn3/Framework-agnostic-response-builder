"""
Framework-agnostic response builder.
No framework imports anywhere here — adapters subclass ResponseCore and
override `_render` to wrap the result in their own response object.
"""

from __future__ import annotations

from http import HTTPStatus as _StdlibStatus
from typing import Any, Callable, ClassVar, Dict, Generic, List, Optional, TypeVar, Union

from .enums import HttpStatus
from .schema import ResponseSchema

R = TypeVar("R")

# RFC 9110: these statuses must not carry a message body.
_BODILESS = frozenset({204, 304})


def _default_message(code: int) -> str:
    try:
        return HttpStatus(code).message
    except ValueError:
        pass
    try:
        return _StdlibStatus(code).phrase
    except ValueError:
        return "Unknown Status"


class custom_response:
    """
    Declares a project-specific response on a helper subclass:

        class AppResponse(JsonResponseHelper):
            user_not_found = custom_response(404, "User not found", internal_code=40401)

        AppResponse.user_not_found()                       # 404, status 40401
        AppResponse.user_not_found(trace_id=request_id)    # any field can be overridden

    The generated method takes keyword arguments only: data, message, metadata,
    errors, internal_code, trace_id, headers.
    """

    def __init__(
        self,
        http_status: Union[HttpStatus, int],
        message: Optional[str] = None,
        *,
        internal_code: Optional[int] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> None:
        self.http_status = http_status
        self.message = message
        self.internal_code = internal_code
        self.headers = dict(headers or {})
        self.name = "custom_response"

    def __set_name__(self, owner: type, name: str) -> None:
        self.name = name

    def __get__(self, instance: Any, owner: type) -> Callable[..., Any]:
        definition = self

        def respond(
            *,
            data: Any = None,
            message: Optional[str] = None,
            metadata: Optional[Dict[str, Any]] = None,
            errors: Optional[List[Dict[str, Any]]] = None,
            internal_code: Optional[int] = None,
            trace_id: Optional[str] = None,
            headers: Optional[Dict[str, str]] = None,
        ) -> Any:
            return owner.build(
                definition.http_status,
                message if message is not None else definition.message,
                data,
                metadata,
                errors,
                internal_code if internal_code is not None else definition.internal_code,
                trace_id,
                {**definition.headers, **(headers or {})},
            )

        respond.__name__ = respond.__qualname__ = self.name
        respond.__doc__ = f"{int(self.http_status)} — {self.message or _default_message(int(self.http_status))}"
        return respond


class ResponseCore(Generic[R]):
    """
    Response factory shared by every adapter.

    Subclasses implement `_render(body, status_code, headers)`, where `body`
    is the envelope dict, or None for statuses that must not have a body.

    Customizing (on any helper subclass):
      - `messages = {404: "..."}` replaces default messages; inherited and merged.
      - `name = custom_response(status, message, internal_code=...)` adds a
        named, project-specific response.
    """

    messages: ClassVar[Dict[int, str]] = {}

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        merged: Dict[int, str] = {}
        for klass in reversed(cls.__mro__):
            merged.update({int(code): text for code, text in vars(klass).get("messages", {}).items()})
        cls.messages = merged

    @classmethod
    def _render(
        cls,
        body: Optional[Dict[str, Any]],
        status_code: int,
        headers: Dict[str, str],
    ) -> R:
        raise NotImplementedError(f"{cls.__name__} must implement _render()")

    @classmethod
    def build(
        cls,
        http_status: Union[HttpStatus, int],
        message: Optional[str] = None,
        data: Any = None,
        metadata: Optional[Dict[str, Any]] = None,
        errors: Optional[List[Dict[str, Any]]] = None,
        internal_code: Optional[int] = None,
        trace_id: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> R:
        """
        Core builder — all named methods delegate here.
        `http_status` may be an HttpStatus member or any int status code.
        """
        code = int(http_status)
        if not 100 <= code <= 599:
            raise ValueError(f"Invalid HTTP status code: {code}")
        headers = dict(headers or {})

        if code in _BODILESS:
            return cls._render(None, code, headers)

        if message is None:
            message = cls.messages.get(code) or _default_message(code)

        schema = ResponseSchema(
            http_status=http_status,
            internal_code=internal_code if internal_code is not None else code,
            message=message,
            data=data if data is not None else ({} if 200 <= code < 300 else []),
            metadata=metadata or {},
            errors=errors or [],
            trace_id=trace_id,
        )
        return cls._render(schema.to_dict(), code, headers)

    # ------------------------------------------------------------------ #
    #  2xx
    # ------------------------------------------------------------------ #
    @classmethod
    def ok(cls, data: Any = None, message: Optional[str] = None, *,
           metadata: Optional[Dict[str, Any]] = None,
           internal_code: Optional[int] = None,
           trace_id: Optional[str] = None) -> R:
        return cls.build(HttpStatus.OK, message, data, metadata,
                         internal_code=internal_code, trace_id=trace_id)

    @classmethod
    def created(cls, data: Any = None, message: Optional[str] = None, *,
                metadata: Optional[Dict[str, Any]] = None,
                internal_code: Optional[int] = None,
                trace_id: Optional[str] = None,
                location: Optional[str] = None) -> R:
        headers = {"Location": location} if location else None
        return cls.build(HttpStatus.CREATED, message, data, metadata,
                         internal_code=internal_code, trace_id=trace_id, headers=headers)

    @classmethod
    def accepted(cls, data: Any = None, message: Optional[str] = None, *,
                 metadata: Optional[Dict[str, Any]] = None,
                 internal_code: Optional[int] = None,
                 trace_id: Optional[str] = None) -> R:
        return cls.build(HttpStatus.ACCEPTED, message, data, metadata,
                         internal_code=internal_code, trace_id=trace_id)

    @classmethod
    def no_content(cls, *, headers: Optional[Dict[str, str]] = None) -> R:
        return cls.build(HttpStatus.NO_CONTENT, headers=headers)

    # ------------------------------------------------------------------ #
    #  3xx
    # ------------------------------------------------------------------ #
    @classmethod
    def moved_permanently(cls, location: str, message: Optional[str] = None, *,
                          trace_id: Optional[str] = None) -> R:
        return cls.build(HttpStatus.MOVED_PERMANENTLY, message, trace_id=trace_id,
                         headers={"Location": location})

    @classmethod
    def found(cls, location: str, message: Optional[str] = None, *,
              trace_id: Optional[str] = None) -> R:
        return cls.build(HttpStatus.FOUND, message, trace_id=trace_id,
                         headers={"Location": location})

    @classmethod
    def not_modified(cls, *, headers: Optional[Dict[str, str]] = None) -> R:
        """304 — no body. Pass ETag / Cache-Control etc. via `headers`."""
        return cls.build(HttpStatus.NOT_MODIFIED, headers=headers)

    # ------------------------------------------------------------------ #
    #  4xx
    # ------------------------------------------------------------------ #
    @classmethod
    def bad_request(cls, message: Optional[str] = None, *,
                    errors: Optional[List[Dict[str, Any]]] = None,
                    internal_code: Optional[int] = None,
                    trace_id: Optional[str] = None) -> R:
        return cls.build(HttpStatus.BAD_REQUEST, message, errors=errors,
                         internal_code=internal_code, trace_id=trace_id)

    @classmethod
    def unauthorized(cls, message: Optional[str] = None, *,
                     errors: Optional[List[Dict[str, Any]]] = None,
                     internal_code: Optional[int] = None,
                     trace_id: Optional[str] = None) -> R:
        return cls.build(HttpStatus.UNAUTHORIZED, message, errors=errors,
                         internal_code=internal_code, trace_id=trace_id)

    @classmethod
    def forbidden(cls, message: Optional[str] = None, *,
                  errors: Optional[List[Dict[str, Any]]] = None,
                  internal_code: Optional[int] = None,
                  trace_id: Optional[str] = None) -> R:
        return cls.build(HttpStatus.FORBIDDEN, message, errors=errors,
                         internal_code=internal_code, trace_id=trace_id)

    @classmethod
    def not_found(cls, message: Optional[str] = None, *,
                  errors: Optional[List[Dict[str, Any]]] = None,
                  internal_code: Optional[int] = None,
                  trace_id: Optional[str] = None) -> R:
        return cls.build(HttpStatus.NOT_FOUND, message, errors=errors,
                         internal_code=internal_code, trace_id=trace_id)

    @classmethod
    def method_not_allowed(cls, message: Optional[str] = None, *,
                           errors: Optional[List[Dict[str, Any]]] = None,
                           internal_code: Optional[int] = None,
                           trace_id: Optional[str] = None) -> R:
        return cls.build(HttpStatus.METHOD_NOT_ALLOWED, message, errors=errors,
                         internal_code=internal_code, trace_id=trace_id)

    @classmethod
    def request_timeout(cls, message: Optional[str] = None, *,
                        errors: Optional[List[Dict[str, Any]]] = None,
                        internal_code: Optional[int] = None,
                        trace_id: Optional[str] = None) -> R:
        return cls.build(HttpStatus.REQUEST_TIMEOUT, message, errors=errors,
                         internal_code=internal_code, trace_id=trace_id)

    @classmethod
    def conflict(cls, message: Optional[str] = None, *,
                 errors: Optional[List[Dict[str, Any]]] = None,
                 internal_code: Optional[int] = None,
                 trace_id: Optional[str] = None) -> R:
        return cls.build(HttpStatus.CONFLICT, message, errors=errors,
                         internal_code=internal_code, trace_id=trace_id)

    @classmethod
    def unprocessable_entity(cls, message: Optional[str] = None, *,
                             errors: Optional[List[Dict[str, Any]]] = None,
                             internal_code: Optional[int] = None,
                             trace_id: Optional[str] = None) -> R:
        return cls.build(HttpStatus.UNPROCESSABLE_ENTITY, message, errors=errors,
                         internal_code=internal_code, trace_id=trace_id)

    @classmethod
    def too_many_requests(cls, message: Optional[str] = None, *,
                          errors: Optional[List[Dict[str, Any]]] = None,
                          internal_code: Optional[int] = None,
                          trace_id: Optional[str] = None,
                          retry_after: Optional[int] = None) -> R:
        headers = {"Retry-After": str(retry_after)} if retry_after is not None else None
        return cls.build(HttpStatus.TOO_MANY_REQUESTS, message, errors=errors,
                         internal_code=internal_code, trace_id=trace_id, headers=headers)

    # ------------------------------------------------------------------ #
    #  5xx
    # ------------------------------------------------------------------ #
    @classmethod
    def internal_server_error(cls, message: Optional[str] = None, *,
                              errors: Optional[List[Dict[str, Any]]] = None,
                              internal_code: Optional[int] = None,
                              trace_id: Optional[str] = None) -> R:
        return cls.build(HttpStatus.INTERNAL_SERVER_ERROR, message, errors=errors,
                         internal_code=internal_code, trace_id=trace_id)

    @classmethod
    def not_implemented(cls, message: Optional[str] = None, *,
                        errors: Optional[List[Dict[str, Any]]] = None,
                        internal_code: Optional[int] = None,
                        trace_id: Optional[str] = None) -> R:
        return cls.build(HttpStatus.NOT_IMPLEMENTED, message, errors=errors,
                         internal_code=internal_code, trace_id=trace_id)

    @classmethod
    def bad_gateway(cls, message: Optional[str] = None, *,
                    errors: Optional[List[Dict[str, Any]]] = None,
                    internal_code: Optional[int] = None,
                    trace_id: Optional[str] = None) -> R:
        return cls.build(HttpStatus.BAD_GATEWAY, message, errors=errors,
                         internal_code=internal_code, trace_id=trace_id)

    @classmethod
    def service_unavailable(cls, message: Optional[str] = None, *,
                            errors: Optional[List[Dict[str, Any]]] = None,
                            internal_code: Optional[int] = None,
                            trace_id: Optional[str] = None) -> R:
        return cls.build(HttpStatus.SERVICE_UNAVAILABLE, message, errors=errors,
                         internal_code=internal_code, trace_id=trace_id)

    @classmethod
    def gateway_timeout(cls, message: Optional[str] = None, *,
                        errors: Optional[List[Dict[str, Any]]] = None,
                        internal_code: Optional[int] = None,
                        trace_id: Optional[str] = None) -> R:
        return cls.build(HttpStatus.GATEWAY_TIMEOUT, message, errors=errors,
                         internal_code=internal_code, trace_id=trace_id)
