# OpenAPI And Routing

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

## Generated Paths

The OpenAPI builder exports external paths, not only internal action paths:

- API prefix: `/api/v1`;
- controller/action path: `/bookings`;
- OpenAPI path: `/api/v1/bookings`.

This keeps Swagger UI curl examples aligned with the real application URL.

## Performance Notes

Route registration should happen during application startup/imports. Repeated
imports must not append duplicate named routes, otherwise every request becomes
slower. The core itinerary indexes routes and caches matches, so WSGI should use
that structure instead of maintaining separate route lists.

## Optional Dependencies

`python-magic` is optional. If it is not installed, uploads still work and MIME
detection falls back to the provided headers or `application/octet-stream`.
