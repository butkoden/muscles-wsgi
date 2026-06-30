# OpenAPI And Routing

Russian version: [openapi-and-routing.ru.md](openapi-and-routing.ru.md)

WSGI API routing is built from the same core route tree as the rest of Muscles.
The HTTP transport receives a request, resolves the route, runs the handler and
then serializes the framework response back to WSGI.

## Controller Shape

```python
from muscles import JsonRequestBody, JsonResponseBody, Model, String, Column
from muscles.wsgi import RestApi


class Booking(Model):
    name = Column(String, required=True)


api = RestApi(prefix="/api/v1", version="1.0", name="ApiV1")


@api.controller("/bookings", description="Bookings")
class BookingController:
    @api.action(
        route="",
        method="post",
        request=[JsonRequestBody(model=Booking)],
        response=[JsonResponseBody(model=Booking)],
    )
    def create(self, request):
        return request.json
```

`controller(..., stateful=True)` is supported for ASGI parity and marks the
controller class with `stateful_controller=True`.

## Generated Paths

The OpenAPI builder exports external paths, not only internal action paths:

- API prefix: `/api/v1`;
- controller/action path: `/bookings`;
- OpenAPI path: `/api/v1/bookings`.

This keeps Swagger UI curl examples aligned with the real application URL.

## Route Groups

`RestApi.group()` registers routes with a shared prefix and inherited OpenAPI
metadata:

```python
from muscles import BearerAuthSecurity, JsonResponseBody

documents = api.group(
    "/documents",
    tags=["Documents"],
    security=[BearerAuthSecurity()],
    response={401: JsonResponseBody(description="Unauthorized")},
)


@documents.init("/{id}", method="GET", summary="Show document")
def show(request, id):
    return {"id": id}
```

The generated operation is emitted as `get`, includes `tags`, `security` and
common responses, and registers the bearer scheme in OpenAPI components.

Endpoint metadata can override inherited auth:

```python
@documents.init("/login", method="POST", auth=False)
def login(request):
    return {"token": "issued-token"}
```

`auth=False` clears inherited security for that operation and tells the WSGI
pipeline to skip matching auth guards.

## Route Key Rule (Important)

`@routes.init(...)` / `api.init(...)` binds handlers by route `path + key + method`.

Endpoints that share the same `path` may keep one shared `key`, or use distinct
keys per HTTP method when operation names must differ.

```python
@api.init("/api/documents", key="documents.collection", method="GET", summary="List")
def list_documents(request):
    ...


@api.init("/api/documents", key="documents.collection", method="POST", summary="Create")
def create_document(request):
    ...


@api.init("/api/documents", key="documents.list", method="GET", summary="List V2")
def list_documents_v2(request):
    ...


@api.init("/api/documents", key="documents.create", method="POST", summary="Create V2")
def create_document_v2(request):
    ...
```

Core route lookup keeps all route records on the matched terminal node and then
filters by method and content type.

## Performance Notes

Route registration should happen during application startup/imports. Repeated
imports must not append duplicate named routes, otherwise every request becomes
slower. The core itinerary indexes routes and caches matches, so WSGI should use
that structure instead of maintaining separate route lists.

WSGI caches the resolved route, matching itinerary and path parameters together,
matching the ASGI route cache behavior for repeated requests.

## Optional Dependencies

## Swagger/OpenAPI defaults

`RestApi` uses these defaults:
- `docs_url` = `/docs`
- `swagger_url` = `/swagger`
- `openapi_url` = `/openapi.json`
- `schema_url` = `schema`
- `prefix` = `/`

By default the UI is reachable at `/swagger`, and OpenAPI JSON at `/openapi.json`.
Compatibility aliases are also registered, so for the defaults you'll also get:
- `/docs` as docs alias
- `/schema` as openapi alias
- `/healthz`, `/ready`, `/live` service endpoints

When `prefix="/api/v1"` the same defaults become:
- UI: `/api/v1/docs`, `/api/v1/swagger`, `/api/v1/redoc`
- OpenAPI: `/api/v1/openapi.json`, `/api/v1/schema`

You can override route names directly in `RestApi(...)`:
```python
api = RestApi(
    prefix="/api/v1",
    docs_url="/api-docs",
    swagger_url="/api-docs",
    openapi_url="/api-spec.json",
    schema_url="/api-spec",
)
```

## Optional Dependencies

`python-magic` is optional. If it is not installed, uploads still work and MIME
detection falls back to the provided headers or `application/octet-stream`.
