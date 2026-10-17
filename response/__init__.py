"""
Framework-agnostic response builder.

    from response import JsonResponseHelper

    return JsonResponseHelper.ok(data=results)

JsonResponseHelper returns a Django, Flask or FastAPI response depending on
which framework is running (see response.auto). Framework-specific helpers are
also available if you prefer to be explicit; they load lazily, so importing
`response` never requires any framework to be installed.
"""

from importlib import import_module
from typing import Any

from .core import ResponseCore, custom_response
from .enums import HttpStatus
from .schema import ResponseSchema, ExceptionInfo
from .adapters.plain import PlainResponse, PlainResponseHelper
from .auto import JsonResponseHelper, configure, detect_framework

_LAZY_ADAPTERS = {
    "DjangoResponseHelper": ".adapters.django",
    "FlaskResponseHelper": ".adapters.flask",
    "FastAPIResponseHelper": ".adapters.fastapi",
}

# Framework adapters are deliberately left out so `from response import *`
# doesn't try to import every framework.
__all__ = [
    "JsonResponseHelper",
    "custom_response",
    "configure",
    "detect_framework",
    "ResponseCore",
    "HttpStatus",
    "ResponseSchema",
    "ExceptionInfo",
    "PlainResponse",
    "PlainResponseHelper",
]


def __getattr__(name: str) -> Any:
    if name in _LAZY_ADAPTERS:
        return getattr(import_module(_LAZY_ADAPTERS[name], __name__), name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__() -> list:
    return sorted(set(globals()) | set(_LAZY_ADAPTERS))
