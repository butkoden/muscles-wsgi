import os
import io
import traceback

from muscles.core import NotFoundException, ApplicationException, ErrorException
from muscles.core import AttributeErrorException
from muscles.core import inject, EventsStorageInterface
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
            print("--------------------------------:")
            print("HTTP make_response:", response)
            print("HTTP STATUS:", response.http_status)
            print("HTTP HEADERS:", response.headers)
            print("HTTP BODY:", response.body)
            self.send_header(response.http_status, response.headers)
            body = response.body if isinstance(response.body, list) else [response.body]
            return body
        except Exception as ae:
            print(ae)
            print(traceback.format_exc())
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
            # print(ae)
            print(traceback.format_exc())
            raise ApplicationException(status=500, reason=ae, body=traceback.format_exc())
        except Exception as ae:
            # print(ae)
            print(traceback.format_exc())
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

    def __init__(self, host, port, error_handler):
        self.__host = host
        self.__port = port
        self.__error_handler = error_handler

        self.__transport = self.__transport_class()
        self.__transport.init_server(self)

    def init_transport(self, transport):
        """
        Инициализируем транспортный протокол
        :param transport: Транспорт
        :return:
        """
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
            print(ex)
            traceback.print_stack()
            return self.send_error(ex)

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

    @inject(EventsStorageInterface)
    def handle_request(self, request, evnetStorage: EventsStorageInterface):
        """
        Обработчик запроса к серверу
        :param request: Объект запроса
        :return:
        """
        try:
            before_request = evnetStorage.get('before_request')
            if before_request:
                for handler in before_request:
                    resp = handler(request)
                    if resp:
                        if isinstance(resp, str):
                            resp = BaseResponse(status=200, body=resp)
                        return self.__transport.make_response(resp)

            for key, instance in itinerary.instance_list():
                call, dictionary = instance.get_current_route(request)
                if call:
                    request.route = call
                    request.itinerary = instance
                    if 'instance' in call.keys():
                        for func in call['instance'].get_event('before_request'):
                            func(request)
                    break

        except ErrorException as ae:
            traceback.print_stack()
            print(ae)
            ae.body = traceback.format_exc()
            return self.send_error(ae, request)
        except ImportError as ae:
            traceback.print_stack()
            print(ae)
            ae = ApplicationException(status=500, reason=ae, body=traceback.format_exc().splitlines())
            return self.send_error(ae, request)
        except KeyError as ae:
            traceback.print_stack()
            print(ae)
            ae = ApplicationException(status=500, reason=ae, body=traceback.format_exc())
            return self.send_error(ae, request)
        except Exception as ae:
            traceback.print_stack()
            print(ae)
            ae = ApplicationException(status=500, reason=ae, body=traceback.format_exc())
            return self.send_error(ae, request)

        if request.route:
            if request.route['redirect'] and request.route['redirect'] is not None:
                resp = BaseResponse.redirect(request.route['redirect'])
            else:
                try:
                    if hasattr(request.route['handler'], 'controller'):
                        resp = request.route['handler'](request.route['handler'].controller(), request=request,
                                                        **dictionary)
                    else:
                        resp = request.route['handler'](request=request, **dictionary)
                    if not isinstance(resp, BaseResponse) and isinstance(resp, str):
                        resp = BaseResponse(status=200, body=resp, request=request)
                    elif not isinstance(resp, BaseResponse) and isinstance(resp, bytes):
                        resp = BaseResponse(status=200, body=resp, request=request)
                    elif not isinstance(resp, BaseResponse) and isinstance(resp, dict):
                        resp = BaseResponse(status=200, body=resp, request=request)
                    elif not isinstance(resp, BaseResponse) and isinstance(resp, tuple):
                        kwargs = {}
                        status = 200
                        if len(resp) >= 1:
                            kwargs['body'] = resp[0]
                        if len(resp) >= 2:
                            status = resp[1]
                        if len(resp) >= 3:
                            kwargs['headers'] = resp[2]
                        resp = BaseResponse(status=status, request=request, **kwargs)
                    elif not isinstance(resp, BaseResponse):
                        resp = BaseResponse(status=200, body=resp, request=request)

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
                    traceback.print_stack()
                    print(ae)
                    ae = ApplicationException(status=400, reason=ae, body=traceback.format_exc().splitlines())
                    return self.send_error(ae, request)
                except ErrorException as ae:
                    traceback.print_stack()
                    print(ae)
                    ae.body = traceback.format_exc().splitlines()
                    return self.send_error(ae, request)
                except ImportError as ae:
                    traceback.print_stack()
                    print(ae)
                    ae = ApplicationException(status=500, reason=ae, body=traceback.format_exc().splitlines())
                    return self.send_error(ae, request)
                except KeyError as ae:
                    traceback.print_stack()
                    print(ae)
                    ae = AttributeErrorException(status=500, reason=ae, body=traceback.format_exc().splitlines())
                    return self.send_error(ae, request)
                except Exception as ae:
                    traceback.print_stack()
                    print(ae)
                    ae = ApplicationException(status=500, reason=ae, body=traceback.format_exc().splitlines())
                    return self.send_error(ae, request)
        return self.send_error(NotFoundException(status=404, reason="Not Found"), request)

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
        print('================ERROR/send_error>', err)
        try:
            status = err.status if hasattr(err, 'status') else 500
            reason = err.reason if hasattr(err, 'reason') else str(err)
            body = err.body if hasattr(err, 'body') else str(err)
        except Exception as e:
            print('-----------------------------4')
            print("Error while handling error:", e)
            status = 500
            reason = b'Internal Server Error'
            body = b'Internal Server Error'
        print('================ERROR/status/reason/body>', status, reason)
        print("\n".join(body) if isinstance(body, list) else body)
        # traceback.print_stack()

        if issubclass(self.__error_handler, Exception):
            resp = self.__error_handler().handler(status=status, reason=reason, body=body)
        else:
            resp = BaseResponse(status=status, reason=reason, body=body)
        # traceback.print_exc(file=sys.stdout)
        # call = routes.get_current_error_handler(resp)

        for key, instance in itinerary.instance_list():
            call = instance.get_current_error_handler(resp)
            if call:
                resp.body = call['handler'](resp, request)
                break

        headers = []
        for header in resp.headers:
            headers.append('%s: %s' % (header[0], header[1]))
        return self.__transport.make_response(resp)
