"""
Defines the strict typed schema for all API responses.
Enforces a consistent response envelope across the entire platform.
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass, field
from typing import Any, Union

from .enums import HttpStatus


@dataclass(frozen=True)
class ResponseSchema:
    """
    Immutable, typed response envelope.

    Every API response — success or failure — must conform to this schema.
    `frozen=True` prevents accidental mutation after construction.

    Attributes:
        http_status   : The HTTP status code (HttpStatus enum).
        internal_code : Internal business/system status code.
        message       : Human-readable response message.
        data          : Response payload. Empty list `[]` for errors.
        metadata      : Supplementary pagination/context info.
        errors        : Structured error details for 4xx/5xx responses.
        trace_id      : Optional request trace ID for observability.
    """

    http_status: HttpStatus
    message: str
    internal_code: int
    data: Any = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    errors: list[dict[str, Any]] = field(default_factory=list)
    trace_id: Union[str, None] = None

    def to_dict(self) -> dict[str, Any]:
        """
        Serializes the schema to a response-safe dictionary.
        None values are excluded to keep the response clean.
        """
        payload: dict[str, Any] = {
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

    exc_type: Union[type, None]
    filename: str
    line_number: int
    detail: Union[str, None] = None

    @classmethod
    def capture(cls) -> "ExceptionInfo":
        """Captures the current exception context from sys.exc_info()."""
        exc_type, exc_value, exc_tb = sys.exc_info()
        filename = (
            os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            if exc_tb
            else "unknown"
        )
        return cls(
            exc_type=exc_type,
            filename=filename,
            line_number=exc_tb.tb_lineno if exc_tb else 0,
            detail=str(exc_value) if exc_value else None,
        )

    def to_error_dict(self) -> dict[str, Any]:
        return {
            "type": self.exc_type.__name__ if self.exc_type else "UnknownError",
            "file": self.filename,
            "line": self.line_number,
            "detail": self.detail,
        }