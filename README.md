# Muscles WSGI

`muscles-wsgi` is the WSGI runtime for Muscles. It provides page routing,
request/response handling, templates, static files, REST controllers and Swagger
UI on top of the shared `muscles` core.

## Installation

Canonical ecosystem install matrix is documented in core:
[Muscles installation matrix](https://github.com/butkoden/muscles/blob/master/docs/installation.md).

## Runtime

An app binds `Context` to `WsgiStrategy`:

```python
from muscles import ApplicationMeta, Configurator, Context
from muscles.wsgi import WsgiStrategy


class App(metaclass=ApplicationMeta):
    config = Configurator(obj={"main": {"HOST": "0.0.0.0", "PORT": "8080"}})
    context = Context(WsgiStrategy, params={})

    def run(self, *args):
        return self.context.execute(*args, shutup=True)
```

`WsgiStrategy` now accepts explicit `host` and `port` keyword arguments and uses
standard WSGI environment keys such as `PATH_INFO`, `QUERY_STRING` and
`wsgi.url_scheme`.

## ASGI/WSGI Parity

WSGI mirrors the ASGI developer-facing API. An application should be able to
switch from `AsgiStrategy` to `WsgiStrategy` without changing route groups,
OpenAPI metadata, guards, auth overrides, response helpers, file upload
handlers or typed handler arguments.

The WSGI package also exposes the same convenience layers:

```python
from muscles.wsgi import MuscularWsgiApp, TestClient, wsgi_app

application = wsgi_app(MuscularWsgiApp())
client = TestClient(application).with_bearer("token")
response = client.post("/api/documents", json={"title": "Spec"})
```

Use `auth=False` on a route when a public endpoint such as `/api/login` lives
inside a protected API group.

## REST API And Swagger

`RestApi` registers controllers and actions into the shared route structure.
Swagger is generated from those controller schemas, request bodies, parameters
and response bodies.

The generated OpenAPI paths include the mounted API prefix. If a controller
action is registered as `/bookings` under prefix `/api/v1`, the schema exposes
`/api/v1/bookings`.

More detail: [docs/openapi-and-routing.md](docs/openapi-and-routing.md).
Backend pipeline features are documented in
[docs/backend-pipeline.md](docs/backend-pipeline.md).
Russian documentation:
[docs/openapi-and-routing.ru.md](docs/openapi-and-routing.ru.md) and
[docs/backend-pipeline.ru.md](docs/backend-pipeline.ru.md).

## Request Handling

The request parser supports standard WSGI input and does not require optional
system libraries to import. Multipart parsing uses the Python standard library;
`python-magic` is treated as optional.

WSGI strategy uses a persistent server lifecycle on strategy/app level, so
route cache is reused across requests while `environ`/`start_response` remain
strictly per-request state.

## Development

Run tests with sibling packages on `PYTHONPATH` when working from source:

```bash
PYTHONPATH=../muscles/src:src python -m pytest -q
```

Production notes: [docs/production.md](docs/production.md).
