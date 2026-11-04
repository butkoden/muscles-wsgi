# Запуск WSGI-приложения

`muscles-wsgi` предоставляет `WsgiStrategy`, базовый класс `MuscularWsgiApp`
и фабрику `wsgi_app`. Фабрика возвращает WSGI callable для сервера:

```python
from muscles.wsgi import MuscularWsgiApp, wsgi_app


class App(MuscularWsgiApp):
    pass


application = wsgi_app(App())
```

Передайте `application` WSGI-серверу. Для тестирования можно использовать
встроенный `TestClient`:

```python
from muscles.wsgi import TestClient

client = TestClient(application)
response = client.get("/")
```

## Принцип обработки запросов


1. WSGI-сервер передаёт приложению `environ` и `start_response`.
2. `wsgi_app` передаёт параметры в контекст приложения.
3. Передача управления в текущую стратегию, основанную на `BaseStrategy` в метод `execute` с передачей всех параметров
4. Стратегия выполняет обработку запроса через WSGI runtime.
5. Вызывается метод `execute` выбранной транспортной реализации, которая формирует ответ на запрос и отвечает за его доставку обратно.


## WSGI transport

1. Runtime формирует объект `Request` из входящего WSGI-запроса.
2. Класс `RequestMaker` формирует объект `Request` исходя из заголовков, которые направлены в исходном запросе
3. Затем вызывается обработчик объекта `WsgiServer` и в зависимости от типа запроса объект `Request` передается в соответсвующий обработчик
4. Происходит получения текущего роутер, который соответствует текущему запросу
5. Проверяется являться ли тип запроса, запросом на редирект, и если да происходит перенаправления
6. Иначе вызывается обработчик роутера, который возвращает тело будущего ответа
7. На основании этого ответа формируется объект `BaseResponse`
8. Объект `BaseResponse` передается в дополнительный обработчик роутера `modify_response` (который может быть переопределен) 
для модификации ответа под требования роутера
9. Формируются заголовки ответа и сам ответ в виде объекта `BaseResponse` передается в текущий транспортный объект в метод `make_response`
10. Ответ возвращается WSGI-серверу в соответствии с протоколом WSGI.

**Важно:** В случае ошибки на каком либо шаге, информация об ошибке направляется в метод `send_error` объекта `WsgiServer`, 
который в роутере ошибок может отрисовать ошибку в браузере направив ее в транспортный объект через метод `make_response`


## Логирование и debug

Логирование теперь управляется на стороне проекта, а не внутри фреймворка.
Передайте логгер через `Context(..., options=...)` или через `context.set_param(...)`.

```python
import logging
from muscles import Context
from muscles.wsgi import WsgiStrategy

context = Context(
    WsgiStrategy,
    options={
        "logger": logging.getLogger("butko.site"),
        "debug": False,
    },
)
```

- `logger`: объект `logging.Logger` или строка с именем логгера.
- `debug=True`: включает расширенные debug-сообщения фреймворка.
- если `logger` не передан, используется логгер `muscles.wsgi`.


## Совместимость с ASGI

WSGI runtime поддерживает тот же application-level контракт, что и ASGI:
route groups, OpenAPI metadata, guards, `auth=False`, response helpers,
typed handler arguments и file uploads. Если приложение не использует
transport-specific код, замена `AsgiStrategy` на `WsgiStrategy` не должна
ломать маршруты и handlers.

Для серверов и тестов можно использовать WSGI entrypoint и in-process client:

```python
from muscles.wsgi import MuscularWsgiApp, TestClient, wsgi_app

application = wsgi_app(MuscularWsgiApp())
client = TestClient(application).with_bearer("token")
response = client.post("/api/documents", json={"title": "Spec"})
```


## Изменения стабильности и скорости

- убраны синхронные `print` в критическом пути обработки запроса;
- добавлен кэш сопоставления роутера для повторяющихся запросов;
- снижены накладные расходы на обработку ошибок/ответов в runtime.
