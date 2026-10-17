"""
JsonResponseHelper — one import that works in any framework.

The adapter is chosen each time a response is built, from the framework that is
actually running (not merely installed):

  1. configure("...") or the RESPONSE_BUILDER_FRAMEWORK env var, if set
  2. Flask   — a Flask app context is active
  3. FastAPI — fastapi has been imported by the app
  4. Django  — Django settings are configured
  5. plain   — anything else (Celery, scripts, tests) -> PlainResponse

Detection only inspects modules the app has already imported, so it never
imports a framework itself.
"""

from __future__ import annotations

import os
import sys
from importlib import import_module
from typing import Any, Dict, Optional

from .core import ResponseCore

ENV_VAR = "RESPONSE_BUILDER_FRAMEWORK"

_ADAPTERS = {
    "django": (".adapters.django", "DjangoResponseHelper"),
    "flask": (".adapters.flask", "FlaskResponseHelper"),
    "fastapi": (".adapters.fastapi", "FastAPIResponseHelper"),
    "plain": (".adapters.plain", "PlainResponseHelper"),
}

_configured: Optional[str] = None


def _validate(framework: str) -> str:
    name = framework.strip().lower()
    if name not in _ADAPTERS:
        raise ValueError(
            f"Unknown framework {framework!r}; expected one of {sorted(_ADAPTERS)}"
        )
    return name


def configure(framework: Optional[str]) -> None:
    """
    Pin the adapter instead of auto-detecting, e.g. configure("fastapi").
    Only needed when an app loads several frameworks at once.
    Pass None to go back to auto-detection.
    """
    global _configured
    _configured = _validate(framework) if framework is not None else None


def detect_framework() -> str:
    """Returns the name of the adapter JsonResponseHelper would use right now."""
    if _configured:
        return _configured
    env = os.environ.get(ENV_VAR)
    if env:
        return _validate(env)

    if "flask" in sys.modules:
        from flask import has_app_context

        if has_app_context():
            return "flask"

    # Checked before Django so FastAPI apps that use the Django ORM still get
    # FastAPI responses.
    if "fastapi" in sys.modules:
        return "fastapi"

    if "django" in sys.modules:
        from django.conf import settings

        if settings.configured:
            return "django"

    return "plain"


class JsonResponseHelper(ResponseCore[Any]):
    """
    Same API as every adapter; returns the running framework's response type.

        return JsonResponseHelper.ok(data=results, message="Fetched successfully")
    """

    @classmethod
    def _render(cls, body: Optional[Dict[str, Any]], status_code: int,
                headers: Dict[str, str]) -> Any:
        module, name = _ADAPTERS[detect_framework()]
        adapter = getattr(import_module(module, __package__), name)
        return adapter._render(body, status_code, headers)
