# Framework-agnostic-response-builder
Framework Agnostic Response Builder

framework-agnostic-response-builder/
├── response/
│   ├── __init__.py
│   ├── enums.py           ← HttpStatus enum (unchanged)
│   ├── schema.py          ← ResponseSchema + ExceptionInfo (unchanged)
│   ├── core.py            ← Pure Python core (NO framework dependency)
│   └── adapters/
│       ├── __init__.py
│       ├── django.py      ← Django adapter
│       ├── flask.py       ← Flask adapter
│       ├── fastapi.py     ← FastAPI adapter
│       └── plain.py       ← Plain dict/JSON (for scripts, Celery, etc.)
