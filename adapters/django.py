"""Django adapter — wraps ResponseCore output in Django's JsonResponse."""

from django.http import JsonResponse
from ..core import ResponseCore


class DjangoResponseHelper(ResponseCore):
    """
    Drop-in replacement for Django views.
    Identical API to ResponseCore but returns Django JsonResponse.
    """

    @classmethod
    def build(cls, http_status, message=None, data=None,
              metadata=None, errors=None, internal_code=None, trace_id=None):
        body, status_code = super().build(
            http_status, message, data, metadata, errors, internal_code, trace_id
        )
        return JsonResponse(body, status=status_code)

    @classmethod
    def no_content(cls):
        return JsonResponse({}, status=204)