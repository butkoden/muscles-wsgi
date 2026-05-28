# Muscles WSGI

`muscles-wsgi` is the WSGI runtime for Muscles. It provides page routing,
request/response handling, templates, static files, REST controllers and Swagger
UI on top of the shared `muscles` core.

## Runtime

An app binds `Context` to `WsgiStrategy`:

```python
from muscles import ApplicationMeta, Configurator, Context
from muscles.wsgi import WsgiStrategy


class App(metaclass=ApplicationMeta):
    config = Configurator(obj={"main": {"HOST": "0.0.0.0", "PORT": "8080"}})
    context = Context(WsgiStrategy, {})

    def run(self, *args):
        return self.context.execute(*args, shutup=True)
```

`WsgiStrategy` now accepts explicit `host` and `port` keyword arguments and uses
standard WSGI environment keys such as `PATH_INFO`, `QUERY_STRING` and
`wsgi.url_scheme`.

## REST API And Swagger

`RestApi` registers controllers and actions into the shared route structure.
Swagger is generated from those controller schemas, request bodies, parameters
and response bodies.

The generated OpenAPI paths include the mounted API prefix. If a controller
action is registered as `/bookings` under prefix `/api/v1`, the schema exposes
`/api/v1/bookings`.

More detail: [docs/openapi-and-routing.md](docs/openapi-and-routing.md).

## Request Handling

The request parser supports standard WSGI input and does not require optional
system libraries to import. Multipart parsing uses the Python standard library;
`python-magic` is treated as optional.

## Development

Run tests with sibling packages on `PYTHONPATH` when working from source:

```bash
PYTHONPATH=../muscles/src:src python -m pytest -q
```
