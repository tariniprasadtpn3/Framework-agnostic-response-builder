"""
Auto-detects the installed framework and exports the right helper.
You can also import a specific adapter explicitly.
"""

from .core import ResponseCore
from .enums import HttpStatus
from .schema import ResponseSchema, ExceptionInfo

# Explicit adapter imports (always available)
from .adapters.plain import PlainResponseHelper

try:
    from .adapters.django import DjangoResponseHelper as JsonResponseHelper
except ImportError:
    try:
        from .adapters.fastapi import FastAPIResponseHelper as JsonResponseHelper
    except ImportError:
        try:
            from .adapters.flask import FlaskResponseHelper as JsonResponseHelper
        except ImportError:
            from .adapters.plain import PlainResponseHelper as JsonResponseHelper

__all__ = [
    "JsonResponseHelper",
    "ResponseCore",
    "HttpStatus",
    "ResponseSchema",
    "ExceptionInfo",
    # explicit adapters
    "DjangoResponseHelper",
    "FlaskResponseHelper",
    "FastAPIResponseHelper",
    "PlainResponseHelper",
]