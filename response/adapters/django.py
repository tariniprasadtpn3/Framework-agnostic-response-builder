"""Django adapter — wraps ResponseCore output in Django's JsonResponse."""

from __future__ import annotations

from django.http import HttpResponse, JsonResponse

from ..core import ResponseCore


class DjangoResponseHelper(ResponseCore[HttpResponse]):
    """
    Drop-in helper for Django views.
    Returns JsonResponse, or a bodiless HttpResponse for 204 / 304.
    """

    @classmethod
    def _render(cls, body, status_code, headers) -> HttpResponse:
        if body is None:
            response = HttpResponse(status=status_code)
        else:
            response = JsonResponse(body, status=status_code)
        for name, value in headers.items():
            response[name] = value
        return response
