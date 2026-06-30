import os
import io
import traceback
import logging

from muscles.core import NotFoundException, ApplicationException, ErrorException
from muscles.core import AttributeErrorException
from muscles.core import inject, EventsStorageInterface
from muscles.core import BackendPipeline
from muscles.core import BaseResponse as CoreBaseResponse
from muscles.core import normalize_problem_payload
from .request import RequestMaker
from .response import MakeResponse, BaseResponse
from .routers import routes, itinerary
from urllib.parse import unquote

MAX_LINE = 64 * 1024
MAX_HEADERS = 100
TIMEOUT = 2
MAX_CONNECTIONS = 1000


class Transport:
    """
    Транспорт протокола стратегии
    """

    server = None

    def __init__(self):
        pass

    def init_server(self, server):
        self.server = server

    def make_response(self, response):
        pass

    def make_request(self):
        pass


class WsgiTransport(Transport):
    """
    Транспорт стратегии WSGI
    """

    def execute(self, *args, **kwargs):
        """
        Исполняем условия транспорта
        :param args:
        :param kwargs[environ]: Окружение запроса
        :param kwargs[start_response]: Метод для ответа
        :return:
        """
        self.environ = kwargs['environ']
        self.start_response = kwargs['start_response']
        return self.handler(self.environ, self.start_response)

    def handler(self, environ, start_response):
        """
        Обработчик транспорта

        :param environ: Переменные окружения запроса
        :param start_response: Метод ответа
        :return:
        """
        request = self.make_request(environ)
        if request is None:
            raise ApplicationException(status=400, reason='Bad request', body='Malformed request line')
        return self.server.handler(request)

    def make_response(self, response: BaseResponse):
        """
        Отправляем ответ
        :param response: объект ответа
        :return:
        """
        try:
            response = MakeResponse(response=response)
            self.server.logger.debug("WSGI response status=%s", response.http_status)
            self.send_header(response.http_status, response.headers)
            body = response.body if isinstance(response.body, list) else [response.body]
            return body
        except Exception as ae:
            self.server.logger.exception("WSGI transport response error")
            raise ApplicationException(status=500, reason=ae, body=traceback.format_exc())

    def send_header(self, http_status, headers):
        """
        Передаем заголовки ответа
        :param http_status: HTTP статус ответа
        :param headers: Заголовки
        :return:
        """
        self.start_response(http_status, headers)

    def make_request(self, environ):
        """
        Формируем обхект запроса на основании переменных запроса
        :param environ: Переменные запроса
        :return: Request
        """
        try:
            requestMaker = RequestMaker(environ)
            request = requestMaker.make()
            return request
        except ApplicationException as ae:
            self.server.logger.exception("WSGI request maker error")
            raise ApplicationException(status=500, reason=ae, body=traceback.format_exc())
        except Exception as ae:
            self.server.logger.exception("WSGI request build error")
            raise ApplicationException(status=500, reason=ae, body=traceback.format_exc())



#
# class TCPSocketTransport(HttpTransport):
#     __charset = 'iso-8859-1'
#
#     def execute(self, *args, **kwargs):
#         '''
#         :param args[0]: host
#         :param args[1]: port
#         :param kwargs:
#         :return:
#         '''
#         self.host = args[0]
#         self.port = args[1]
#         server = socket.socket(socket.AF_INET, socket.SOCK_STREAM, proto=0)
#         # server.setblocking(0)
#         server.settimeout(TIMEOUT)
#         all_threads = []
#         try:
#             server.bind((self.host, self.port))
#             server.listen(MAX_CONNECTIONS)
#             while True:
#                 try:
#                     connect, _ = server.accept()
#                     t = threading.Thread(target=self.handler, args=(connect,))
#                     t.start()
#
#                     all_threads.append(t)
#                 except ConnectionResetError:
#                     connect = None
#                 except Exception as e:
#                     # self.send_error(connect, e)
#                     traceback.print_exc(file=sys.stdout)
#         finally:
#             if server:
#                 server.close()
#             for t in all_threads:
#                 t.join()
#         return
#
#     def handler(self, connect):
#         try:
#             self.reader = connect.makefile('rb')
#             self.writer = connect.makefile('wb')
#             request = self.make_request()
#             if request is None:
#                 raise MuscularError(400, 'Bad request', 'Malformed request line')
#             self.server.handler(request)
#         except ConnectionResetError:
#             connect = None
#         except Exception as e:
#             # self.send_error(connect, e)
#             traceback.print_exc(file=sys.stdout)
#         if connect:
#             connect.close()
#
#     def make_response(self, response):
#         try:
#             status_line = f'HTTP/1.1 {response.status} {response.reason}\r\n'
#             self.writer.write(status_line.encode('iso-8859-1'))
#
#             if response.headers:
#                 for (key, value) in response.headers:
#                     header_line = f'{key}: {value}\r\n'
#                     self.writer.write(header_line.encode('iso-8859-1'))
#
#             self.writer.write(b'\r\n')
#
#             if response.body:
#                 self.writer.write(response.body)
#
#             if hasattr(self.writer, 'flush'):
#                 self.writer.flush()
#             if self.writer:
#                 self.writer.close()
#         except Exception as err:
#             print('Internal Error:', err)
#             traceback.print_exc(file=sys.stdout)
#         return
#
#     def make_request(self):
#         headers = []
#         size = 0
#         while True:
#             line = self.reader.readline()
#             if len(line) > MAX_LINE:
#                 raise MuscularError(494, 'Request header too large')
#             if b'Content-Length' in line:
#                 s = re.sub("[\r\n]", "", line)
#                 h = s.split(':')
#                 size = h[1]
#             if line in (b'\r\n', b'\n', b''):
#                 break
#             headers.append(line)
#
#         if len(headers[1:]) > MAX_HEADERS:
#             raise MuscularError(494, 'Too many headers')
#         headers = Parser().parsestr(b''.join(headers[1:]).decode(self.__charset))
#
#         words = headers[0].decode(self.__charset).split()
#         if len(words) != 3:
#             raise HTTPErrorMuscularError(400, 'Bad request', 'Malformed request line')
#         method, target, protocol = words
#         if protocol != 'HTTP/1.1':
#             raise HTTPErrorMuscularError(505, 'HTTP Version Not Supported')
#
#         host = self.headers.get('Host')
#         if not host:
#             raise MuscularError(400, 'Bad request', 'Host header is missing')
#
#         if not size:
#             body = b''
#         else:
#             body = self.reader.read(size)
#
#         request = Request(
#             method=method,
#             protocol=protocol,
#             url=target,
#             server=(self.host, self.port),
#             remote_addr=None,
#             headers=headers,
#             body=body,
#         )
#         if self.reader and hasattr(self.reader, 'close'):
#             self.reader.close()
#         return request


class WsgiServer:
    """
    Объект сервера WSGI
    """

    __transport_class = WsgiTransport
    __transport = WsgiTransport
    __host = 'localhost'
    __port = 80

    def __init__(self, host, port, error_handler, logger=None, debug=False):
        self.__host = host
        self.__port = port
        self.__error_handler = error_handler
        self.logger = logger or logging.getLogger("muscles.wsgi")
        self.debug = debug
        self._route_cache = {}
        self._backend_pipeline = BackendPipeline()

        self.__transport = self.__transport_class()
        self.__transport.init_server(self)

    def init_transport(self, transport):
        """
        Инициализируем транспортный протокол
        :param transport: Транспорт
        :return:
        """
        if (
            self.__transport is not None
            and self.__transport_class is transport
            and isinstance(self.__transport, transport)
        ):
            return
        self.__transport_class = transport
        self.__transport = transport()
        self.__transport.init_server(self)

    def execute(self, *args, **kwargs):
        """
        Метод исполнения протокола сервера
        :param args:
        :param kwargs:
        :return:
        """
        try:
            return self.__transport.execute(*args, **kwargs)
        except Exception as ex:
            self.logger.exception("WSGI execute error")
            return self.send_error(ex)

    def _to_protocol_response(self, response, request=None):
        if isinstance(response, BaseResponse):
            return response
        if isinstance(response, ApplicationException):
            return BaseResponse(
                status=response.status,
                body=response.body or {"error": str(response.reason)},
                request=request,
                content_type="application/problem+json",
            )
        if isinstance(response, BaseException) and hasattr(response, "status"):
            return BaseResponse(
                status=getattr(response, "status"),
                body=normalize_problem_payload(response, request=request, include_trace=self.debug),
                request=request,
                content_type="application/problem+json",
            )
        if isinstance(response, CoreBaseResponse):
            if response.redirect:
                return BaseResponse.redirect(response.redirect, status=response.status)
            headers = [(k, v) for k, v in (response.headers or {}).items()]
            return BaseResponse(
                status=response.status,
                body=response.body,
                headers=headers,
                request=request,
                content_type=response.content_type,
            )

        # Legacy path: keep transport-native serialization behavior.
        if isinstance(response, str):
            return BaseResponse(status=200, body=response, request=request)
        if isinstance(response, bytes):
            return BaseResponse(status=200, body=response, request=request)
        if isinstance(response, dict):
            return BaseResponse(status=200, body=response, request=request)
        if isinstance(response, tuple):
            kwargs = {}
            status = 200
            if len(response) >= 1:
                kwargs["body"] = response[0]
            if len(response) >= 2:
                status = response[1]
            if len(response) >= 3:
                kwargs["headers"] = response[2]
            return BaseResponse(status=status, request=request, **kwargs)
        return BaseResponse(status=200, body=response, request=request)

    def handler(self, request):
        """
        Обработчик сервера
        :param request: Запрос к серверу
        :return:
        """
        headers = []
        for header in request.headers:
            headers.append('%s: %s' % (header, request.headers[header]))
        if request.is_exception:
            return self.send_error(request.exception, request)
        static = routes.get_current_static(request)
        if static:
            return self.handle_static(static, request)
        else:
            return self.handle_request(request)

    def _resolve_route(self, request):
        """
        Разрешение маршрута по кэшу/реестру.
        :param request: Запрос
        :return: Параметры найденного маршрута.
        """
        route_key = (
            request.path,
            request.method.lower() if request.method else "",
            (request.content_type or "").lower(),
        )
        dictionary = {}
        cached_route = self._route_cache.get(route_key)
        if cached_route is not None:
            cached_instance, cached_call, dictionary = cached_route
            if cached_call:
                request.route = cached_call
                request.itinerary = cached_instance
            return dictionary
        if request.route is None:
            for instance in self._runtime_instances():
                call, dictionary = instance.get_current_route(request)
                if call:
                    request.route = call
                    request.itinerary = instance
                    self._route_cache[route_key] = (instance, call, dictionary)
                    break
            if request.route is None:
                self._route_cache[route_key] = (None, None, {})
        if request.route and 'instance' in request.route.keys():
            for func in request.route['instance'].get_event('before_request'):
                func(request)
        return dictionary

    @inject(EventsStorageInterface)
    def handle_request(self, request, evnetStorage: EventsStorageInterface):
        """
        Обработчик запроса к серверу
        :param request: Объект запроса
        :return:
        """
        try:
            before_request = evnetStorage.get('before_request')
            cors_response = self._cors_preflight_response(request)
            if cors_response is not None:
                return self.__transport.make_response(self._to_protocol_response(cors_response, request=request))

            if before_request:
                for handler in before_request:
                    resp = handler(request)
                    if resp:
                        if isinstance(resp, str):
                            resp = BaseResponse(status=200, body=resp)
                        return self.__transport.make_response(resp)

            dictionary = self._resolve_route(request)

        except ErrorException as ae:
            self.logger.exception("WSGI route resolution error")
            ae.body = traceback.format_exc()
            return self.send_error(ae, request)
        except ImportError as ae:
            self.logger.exception("WSGI import error")
            ae = ApplicationException(status=500, reason=ae, body=traceback.format_exc().splitlines())
            return self.send_error(ae, request)
        except KeyError as ae:
            self.logger.exception("WSGI key error")
            ae = ApplicationException(status=500, reason=ae, body=traceback.format_exc())
            return self.send_error(ae, request)
        except Exception as ae:
            self.logger.exception("WSGI unexpected route error")
            ae = ApplicationException(status=500, reason=ae, body=traceback.format_exc())
            return self.send_error(ae, request)

        if request.route:
            if request.route['redirect'] and request.route['redirect'] is not None:
                resp = BaseResponse.redirect(request.route['redirect'])
            else:
                try:
                    guard_response = self._run_guards(request)
                    if guard_response is not None:
                        return self.__transport.make_response(self._to_protocol_response(guard_response, request=request))
                    self._run_security(request)
                    resp = self._call_route_handler(request, dictionary)
                    resp = self._to_protocol_response(resp, request=request)

                    if hasattr(request.itinerary, 'modify_response'):
                        resp = request.itinerary.modify_response(resp)

                    headers = []
                    for header in resp.headers:
                        headers.append('%s: %s' % (header[0], header[1]))

                    before_response = evnetStorage.get('before_response')
                    if before_response:
                        for handler in before_response:
                            resp = handler(resp)
                    return self.__transport.make_response(resp)
                except ApplicationException as ae:
                    self.logger.exception("WSGI application exception")
                    ae = ApplicationException(status=ae.status, reason=ae.reason, body=ae.body, traceback=traceback.format_exc().splitlines())
                    return self.send_error(ae, request)
                except ErrorException as ae:
                    self.logger.exception("WSGI error exception")
                    ae.body = traceback.format_exc().splitlines()
                    return self.send_error(ae, request)
                except ImportError as ae:
                    self.logger.exception("WSGI import exception")
                    ae = ApplicationException(status=500, reason=ae, body=traceback.format_exc().splitlines())
                    return self.send_error(ae, request)
                except KeyError as ae:
                    self.logger.exception("WSGI handler key error")
                    if self._has_exception_mapping(ae, request):
                        return self.send_error(ae, request)
                    ae = AttributeErrorException(status=500, reason=ae, body=traceback.format_exc().splitlines())
                    return self.send_error(ae, request)
                except Exception as ae:
                    self.logger.exception("WSGI handler unexpected exception")
                    if self._has_exception_mapping(ae, request):
                        return self.send_error(ae, request)
                    ae = ApplicationException(status=500, reason=ae, body=traceback.format_exc().splitlines())
                    return self.send_error(ae, request)
        if self._has_matching_path(request.path):
            return self.__transport.make_response(BaseResponse(status=404, body={}, request=request))
        return self.send_error(NotFoundException(status=404, reason="Not Found"), request)

    def _matching_path_instances(self, path: str):
        matched = []
        for instance in self._runtime_instances():
            route_node, _ = instance.match_with_params(path)
            if route_node is not None:
                matched.append(instance)
        return matched

    def _runtime_instances(self):
        for _, instance in itinerary.instance_list():
            if instance.__class__.__module__.startswith("muscles.wsgi"):
                yield instance

    def _cors_preflight_response(self, request):
        if (request.method or "").upper() != "OPTIONS":
            return None
        for instance in self._matching_path_instances(request.path):
            for middleware in getattr(instance, "get_middlewares", lambda: [])():
                if getattr(middleware, "is_cors_middleware", False):
                    return middleware.preflight_response(request)
        return None

    def _header_lookup(self, headers, name):
        return self._backend_pipeline.header_lookup(headers, name)

    def _coerce_value(self, annotation, value):
        return self._backend_pipeline.coerce_value(annotation, value)

    def _coerce_body(self, annotation, payload):
        return self._backend_pipeline.coerce_body(annotation, payload)

    def _resolve_dependency(self, annotation):
        return self._backend_pipeline.resolve_dependency(annotation)

    def _build_handler_kwargs(self, handler, request, dictionary):
        return self._backend_pipeline.build_handler_kwargs(handler, request, dictionary)

    def _run_guards(self, request):
        return self._backend_pipeline.run_guards(request)

    def _has_exception_mapping(self, error, request):
        current_itinerary = getattr(request, "itinerary", None)
        finder = getattr(current_itinerary, "_find_exception_error_mapping", None)
        if finder is None:
            return False
        status, handler = finder(error)
        return status is not None or handler is not None

    def _prepare_error(self, err, request=None):
        current_itinerary = getattr(request, "itinerary", None)
        if current_itinerary is None:
            return err, None
        call = current_itinerary.get_current_error_handler(err)
        if call and call.get("handler"):
            return err, call
        return err, None

    def _run_security(self, request):
        return self._backend_pipeline.run_security(request)

    def _call_route_handler(self, request, dictionary):
        return self._backend_pipeline.call_route_handler(request, dictionary)

    def _call_handler(self, request, dictionary):
        return self._backend_pipeline.call_handler(request, dictionary)

    def _has_matching_path(self, path: str) -> bool:
        for instance in self._runtime_instances():
            route_node, _ = instance.match_with_params(path)
            if route_node is not None:
                return True
        return False

    def handle_static(self, static, request):
        """
        Обработчик статических файлов
        :param static: Путь к диреткории с файлами
        :param request: Объект запроса
        :return:
        """
        path = request.path.replace(static['prefix'] + '/', '', 1)
        resp_file = os.path.join(static['directory'], unquote(path))

        if not os.path.isfile(resp_file):
            raise NotFoundException(status=404, reason='Not found')
        try:
            resp = BaseResponse(status=200, file=resp_file)

            if static['handler'] is not None:
                resp = static['handler'](resp)

            response = MakeResponse(response=resp)
            self.__transport.send_header(response.http_status, response.headers)
            with io.open(resp_file, "rb") as f:
                yield f.read()
        except Exception as e:
            raise NotFoundException(status=404, reason='Not found')

    def send_error(self, err, request=None):
        """
        Отправляет ответ ошибки
        :param err: Объект ошибки или текст ошибки
        :param request: Объект запроса
        :return:
        """
        err, mapped_call = self._prepare_error(err, request=request)
        payload = normalize_problem_payload(err, request=request, include_trace=self.debug)
        status = payload.get("status", 500)
        title = payload.get("title")
        self.logger.error("WSGI error status=%s reason=%s", status, title)

        if self.debug:
            trace = payload.get("trace")
            self.logger.debug("%s", "\n".join(trace) if isinstance(trace, list) else trace)

        if issubclass(self.__error_handler, Exception):
            resp = self.__error_handler().handler(
                status=status,
                reason=title,
                body=payload,
                trace=payload.get("trace"),
                request=request,
            )
            if isinstance(resp, dict):
                response = BaseResponse(
                    status=status,
                    body=resp,
                    headers=[("Content-Type", "application/problem+json")],
                    request=request,
                    content_type='application/problem+json',
                )
            elif not isinstance(resp, BaseResponse):
                response = BaseResponse(
                    status=status,
                    body=payload,
                    headers=[("Content-Type", "application/problem+json")],
                    request=request,
                    content_type='application/problem+json',
                )
            else:
                response = resp
        else:
            response = BaseResponse(
                status=status,
                body=payload,
                headers=[("Content-Type", "application/problem+json")],
                request=request,
                content_type='application/problem+json',
            )
        # traceback.print_exc(file=sys.stdout)
        # call = routes.get_current_error_handler(resp)

        if mapped_call:
            response.body = mapped_call['handler'](response, request)
        else:
            for instance in self._runtime_instances():
                call = instance.get_current_error_handler(response)
                if call:
                    response.body = call['handler'](response, request)
                    break

        return self.__transport.make_response(response)
