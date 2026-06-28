# Backend pipeline

English version: [backend-pipeline.md](backend-pipeline.md)

WSGI использует общие контракты ядра `muscles`: группы маршрутов, middleware,
guards, сопоставление исключений, auth-метаданные, помощники ответов и CORS.

## Совместимость ASGI И WSGI

WSGI повторяет поведение ASGI на уровне приложения. Проект должен иметь
возможность заменить `AsgiStrategy` на `WsgiStrategy` без изменения групп
маршрутов, OpenAPI-метаданных, guards, auth overrides, помощников ответов,
обработчиков загрузки файлов и типизированных аргументов handlers.

Когда сервер ожидает обычный WSGI callable, используйте wrapper:

```python
from muscles.wsgi import MuscularWsgiApp, wsgi_app

application = wsgi_app(MuscularWsgiApp())
```

## Группы Маршрутов И OpenAPI

```python
from dataclasses import dataclass

from muscles import BearerJwtAuth, JsonResponseBody, cors
from muscles.wsgi import RestApi

api = RestApi(prefix="/api")
jwt_auth = BearerJwtAuth(secret=settings.jwt_secret)

documents = api.group(
    "/documents",
    tags=["Documents"],
    security=[jwt_auth],
    response={401: JsonResponseBody(description="Unauthorized")},
)

api.use(cors(allow_origins=settings.allowed_origins, allow_credentials=True))
```

Обработчики, зарегистрированные через `documents`, наследуют group tags,
security и общие responses. OpenAPI builder выводит методы в нижнем регистре и
добавляет схемы безопасности маршрутов в `components.securitySchemes`.

## Аргументы Handler

WSGI строит аргументы handler из path-параметров, JSON body, query-параметров,
headers, cookies и core-зависимостей:

```python
@dataclass
class CreateDocument:
    title: str


class DocumentStore:
    ...


@documents.init("", method="post")
def create_document(body: CreateDocument, store: DocumentStore, trace_id: str):
    return store.create(title=body.title, trace_id=trace_id)
```

`body` создаётся из JSON. Поддерживаются dataclasses, Pydantic-style models и
простые Python classes с keyword-конструкторами. Отсутствующие обязательные
аргументы и ошибки валидации body возвращают `422`.

## Guards, Auth И Ошибки

```python
def require_workspace(request):
    if not request.user:
        return {"error": "unauthorized"}, 401


api.guard("/api/**", require_workspace, except_=["/api/public/**"])
api.map_error(PermissionError, status=403)
api.map_error(ValueError, status=422)
```

Для публичного endpoint внутри защищённого API используйте `auth=False`:

```python
@api.init("/api/login", method="post", auth=False)
def login(request):
    return {"token": "issued-token"}
```

WSGI пропускает matching guards и route-level security для endpoint,
помеченных `auth=False`.

Если handler выбрасывает сопоставленное исключение, WSGI сохраняет назначенный
статус перед созданием problem response.

## Нормализация Ответов

WSGI принимает те же формы возврата handler, что и ASGI:

```python
return {"ok": True}
return [1, "a", {"b": True}]
return ({"created": True}, 201, [("X-Trace-Id", "abc")])
return b"raw bytes"
```

Core helpers `JsonResponse`, `HtmlResponse`, `BytesResponse`, `FileResponse` и
`NoContentResponse` нормализуются runtime.

## Загрузка Файлов

Multipart files доступны как `FileStorage`:

```python
def upload(request):
    file = request.files["image"]
    file.validate(max_size=5_000_000, allowed_content_types={"image/png"})
    saved_path = file.save("/srv/uploads", safe=True)
    return {"path": saved_path}
```

`safe=True` сохраняет файл под безопасным basename.

## Test Client

`muscles.wsgi.testing.TestClient` вызывает WSGI app in-process и повторяет API
ASGI test client:

```python
from muscles.wsgi.testing import TestClient

client = TestClient(application).with_bearer(token)
response = client.post("/api/documents", json={"title": "Spec"})

assert response.status_code == 201
assert response.json()["title"] == "Spec"
```
