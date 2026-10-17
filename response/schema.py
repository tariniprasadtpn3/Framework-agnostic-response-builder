"""
Defines the strict typed schema for all API responses.
Enforces a consistent response envelope across the entire platform.
"""

from __future__ import annotations

import os
import sys
import traceback
from dataclasses import dataclass, field
from types import TracebackType
from typing import Any, Dict, List, Optional, Type, Union

from .enums import HttpStatus


@dataclass(frozen=True)
class ResponseSchema:
    """
    Typed response envelope.

    Every API response — success or failure — must conform to this schema.
    `frozen=True` prevents reassigning fields; `metadata` and `errors` are
    copied on construction so later changes to the caller's objects don't leak in.

    Attributes:
        http_status   : The HTTP status code (HttpStatus member or int).
        internal_code : Internal business/system status code. Serialized as "status".
        message       : Human-readable response message.
        data          : Response payload. Empty list `[]` for errors.
        metadata      : Supplementary pagination/context info.
        errors        : Structured error details for 4xx/5xx responses.
        trace_id      : Optional request trace ID for observability.
    """

    http_status: Union[HttpStatus, int]
    message: str
    internal_code: int
    data: Any = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    errors: List[Dict[str, Any]] = field(default_factory=list)
    trace_id: Optional[str] = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "metadata", dict(self.metadata))
        object.__setattr__(self, "errors", list(self.errors))

    def to_dict(self) -> Dict[str, Any]:
        """
        Serializes the schema to a response-safe dictionary.
        Empty metadata/errors and a None trace_id are omitted.
        """
        payload: Dict[str, Any] = {
            "status": self.internal_code,
            "message": self.message,
            "data": self.data,
        }

        if self.metadata:
            payload["metadata"] = self.metadata

        if self.errors:
            payload["errors"] = self.errors

        if self.trace_id is not None:
            payload["trace_id"] = self.trace_id

        return payload


@dataclass
class ExceptionInfo:
    """
    Captures structured exception context for logging and error responses.
    """

    exc_type: Optional[Type[BaseException]]
    filename: str
    line_number: int
    detail: Optional[str] = None

    @classmethod
    def capture(cls, exc: Optional[BaseException] = None) -> "ExceptionInfo":
        """
        Captures context from `exc`, or from the exception currently being
        handled (sys.exc_info()) when `exc` is omitted.
        The file/line reported is where the exception was raised.
        """
        if exc is not None:
            exc_type: Optional[Type[BaseException]] = type(exc)
            exc_tb: Optional[TracebackType] = exc.__traceback__
        else:
            exc_type, exc, exc_tb = sys.exc_info()

        if exc_tb is not None:
            raise_site = traceback.extract_tb(exc_tb)[-1]
            filename = os.path.basename(raise_site.filename)
            line_number = raise_site.lineno or 0
        else:
            filename, line_number = "unknown", 0

        return cls(
            exc_type=exc_type,
            filename=filename,
            line_number=line_number,
            detail=str(exc) if exc is not None else None,
        )

    def to_error_dict(self, include_debug: bool = False) -> Dict[str, Any]:
        """
        Returns an entry for the response `errors` list.
        File, line and the exception message can expose internals, so they are
        only included when `include_debug` is True (e.g. DEBUG builds or logs).
        """
        error: Dict[str, Any] = {
            "type": self.exc_type.__name__ if self.exc_type else "UnknownError",
        }
        if include_debug:
            error.update(file=self.filename, line=self.line_number, detail=self.detail)
        return error
