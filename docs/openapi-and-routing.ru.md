# OpenAPI и маршрутизация

English version: [openapi-and-routing.md](openapi-and-routing.md)

WSGI API routing строится из того же дерева маршрутов ядра, что и остальная
экосистема Muscles. HTTP transport получает request, разрешает маршрут,
запускает handler и сериализует framework response обратно в WSGI.

## Форма Controller

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

`controller(..., stateful=True)` поддерживается для совместимости с ASGI и
помечает controller class флагом `stateful_controller=True`.

## Сгенерированные Paths

OpenAPI builder экспортирует внешние paths, а не только внутренние action
paths:

- API prefix: `/api/v1`;
- controller/action path: `/bookings`;
- OpenAPI path: `/api/v1/bookings`.

Так Swagger UI curl examples совпадают с реальным URL приложения.

## Группы Маршрутов

`RestApi.group()` регистрирует маршруты с общим prefix и унаследованными
OpenAPI metadata:

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

Сгенерированная operation выходит как `get`, содержит `tags`, `security` и
общие responses, а bearer scheme попадает в OpenAPI components.

Endpoint metadata может переопределить унаследованную авторизацию:

```python
@documents.init("/login", method="POST", auth=False)
def login(request):
    return {"token": "issued-token"}
```

`auth=False` очищает унаследованный security для operation и говорит WSGI
pipeline пропустить matching auth guards.

## Производительность

Регистрация маршрутов должна происходить во время startup/imports приложения.
Повторные imports не должны добавлять duplicate named routes, иначе каждый
request станет медленнее. Core itinerary индексирует routes и кеширует matches,
поэтому WSGI использует эту структуру напрямую.

WSGI кеширует найденный route, matching itinerary и path parameters вместе,
повторяя поведение ASGI route cache для повторяющихся запросов.

## Swagger/OpenAPI Defaults

`RestApi` использует такие defaults:

- `docs_url` = `/docs`
- `swagger_url` = `/swagger`
- `openapi_url` = `/openapi.json`
- `schema_url` = `schema`
- `prefix` = `/`

По умолчанию UI доступен на `/swagger`, а OpenAPI JSON - на `/openapi.json`.
Также регистрируются compatibility aliases:

- `/docs` как docs alias
- `/schema` как openapi alias
- `/healthz`, `/ready`, `/live` service endpoints

Когда `prefix="/api/v1"`, defaults становятся:

- UI: `/api/v1/docs`, `/api/v1/swagger`, `/api/v1/redoc`
- OpenAPI: `/api/v1/openapi.json`, `/api/v1/schema`

Route names можно переопределить прямо в `RestApi(...)`:

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

`python-magic` необязателен. Если он не установлен, uploads продолжают
работать, а MIME detection использует headers или `application/octet-stream`.
