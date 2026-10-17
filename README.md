# Framework-agnostic Response Builder

One consistent JSON response envelope for Django, Flask, FastAPI and plain Python
(Celery, Lambda, scripts, tests).

```json
{
  "status": 200,
  "message": "Success",
  "data": {"id": 1},
  "metadata": {"page": 1},
  "errors": [],
  "trace_id": "abc-123"
}
```

`metadata`, `errors` and `trace_id` are omitted when empty. `status` is the
internal/business code and defaults to the HTTP status. 204 and 304 responses
have no body.

## Install

```bash
pip install -e ".[django]"    # or [flask], [fastapi]; core has no dependencies
```

## Usage

The same code works in every framework:

```python
from response import JsonResponseHelper as R, HttpStatus

R.ok({"id": 1}, metadata={"page": 1})
R.created({"id": 7}, location="/items/7")
R.no_content()
R.found("/login")
R.not_modified(headers={"ETag": '"v2"'})
R.bad_request("Invalid sort field", errors=[{"field": "sort"}], trace_id=request_id)
R.build(HttpStatus.CONFLICT, "Already exists", internal_code=40901)
```

`JsonResponseHelper` picks the response type from the framework that is running,
each time a response is built:

| Situation                                | Returns                                |
|------------------------------------------|----------------------------------------|
| Inside a Flask app/request context       | Flask `Response`                       |
| App has imported `fastapi`               | FastAPI `JSONResponse` / `Response`    |
| Django settings configured               | Django `JsonResponse` / `HttpResponse` |
| Anything else (Celery, scripts, tests)   | `PlainResponse(body, status_code, headers)` |

FastAPI is checked before Django, so FastAPI apps using the Django ORM still get
FastAPI responses. If an app loads several frameworks and detection guesses
wrong, pin it once at startup:

```python
import response
response.configure("django")      # or set RESPONSE_BUILDER_FRAMEWORK=django
```

You can also use a framework's helper directly: `DjangoResponseHelper`,
`FlaskResponseHelper`, `FastAPIResponseHelper`, `PlainResponseHelper`.

## Your own responses

Subclass a helper once per project (usually `JsonResponseHelper`) and declare
your responses, business codes and default messages:

```python
# myproject/responses.py
from response import JsonResponseHelper, HttpStatus, custom_response


class AppResponse(JsonResponseHelper):
    # Replace default messages for any status; applies to built-in methods too.
    messages = {
        404: "Nothing here",
        HttpStatus.UNAUTHORIZED: "Please log in",
    }

    # Project-specific responses: status, default message, business code, headers.
    user_not_found = custom_response(404, "User not found", internal_code=40401)
    email_taken    = custom_response(409, "Email already registered", internal_code=40901)
    order_placed   = custom_response(201, "Order placed", internal_code=20101)
    rate_limited   = custom_response(429, internal_code=42901, headers={"Retry-After": "30"})
```

```python
from myproject.responses import AppResponse

AppResponse.user_not_found()                              # 404 · {"status": 40401, "message": "User not found", ...}
AppResponse.order_placed(data=order, trace_id=req_id)     # any field can be passed or overridden
AppResponse.email_taken(errors=[{"field": "email"}])
AppResponse.not_found()                                   # built-ins still work: "Nothing here"
```

- Custom responses take keyword arguments only: `data`, `message`, `metadata`,
  `errors`, `internal_code`, `trace_id`, `headers`.
- `messages` is inherited and merged, so a subclass of `AppResponse` only lists
  what it changes.
- Any status code works, including ones without a built-in method
  (`custom_response(402, ...)`, `R.build(418)`); the default message falls back
  to the standard HTTP phrase.
- For logic beyond defaults, add a normal classmethod that calls `cls.build(...)`.

Reporting exceptions:

```python
from response import ExceptionInfo

try:
    ...
except Exception as exc:
    info = ExceptionInfo.capture(exc)
    logger.error("failed", extra=info.to_error_dict(include_debug=True))
    return R.internal_server_error(errors=[info.to_error_dict()])  # type only, no internals
```

## Writing an adapter

Subclass `ResponseCore` and implement `_render(body, status_code, headers)`;
`body` is `None` for bodiless statuses.

## Layout

```
response/
├── __init__.py      public API; framework adapters load lazily
├── enums.py         HttpStatus
├── schema.py        ResponseSchema, ExceptionInfo
├── core.py          ResponseCore (no framework imports)
├── auto.py          JsonResponseHelper + framework detection
└── adapters/
    ├── django.py
    ├── flask.py
    ├── fastapi.py
    └── plain.py
tests/
```

## Tests

```bash
pip install -e ".[test]"
pytest
```
