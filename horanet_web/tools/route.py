from io import BytesIO
import json
import logging
from collections import Iterable
from functools import wraps

import lxml.etree as etree
import werkzeug.exceptions

from odoo import http
from odoo.http import request, Response, JsonRequest

_logger = logging.getLogger(__name__)

old_JsonRequest_init = http.JsonRequest.__init__


def new_JsonRequest_init(self, httprequest, *args):
    if httprequest.mimetype == 'application/json':
        self._request_args = None
        if not (httprequest.args and httprequest.args.get('jsonp', False)):
            request_data = httprequest.stream.read()
            if request_data == '':
                request_data = '{}'
            try:
                jsonrequest_data = json.loads(request_data)
                if not isinstance(jsonrequest_data, dict):
                    request_data = '{}'
                    self._request_args = jsonrequest_data
            except ValueError as ve:
                msg = "Invalid JSON data: {error_message}".format(error_message=unicode(ve))
                _logger.info('%s: %s', httprequest.path, msg)
                raise werkzeug.exceptions.BadRequest(msg)
            finally:
                httprequest.stream = BytesIO(request_data)
                httprequest.stream.seek(0)

    args = (httprequest,) + args
    old_JsonRequest_init(self, *args)


http.JsonRequest.__init__ = new_JsonRequest_init


def jsonRoute(route=None, **kw):
    """Décorateur d'implémentation de gestion de requêtes JSON dans le context d'Odoo.

    see :func:`http.route` for the complete argument list

    Sucessful request::

        structured JSON :
            --> {"params": {"context": {},
                          "arg1": "val1" },
               "id": null}

            <-- {"result": { "res1": "val1"
                            "error": {"code": code, "message": message}},
               "id": null}

        JSON :
            --> [2,5]
            or
            --> {"arg1": "val1","arg2": "val2"}

            <-- {"result": { "res1": "val1"
                            "error": {"code": code, "message": message}},
               "id": null}
        RPC like :
            --> {"jsonrpc": "2.0",
               "method": "call",
               "params": {"context": {},
                          "arg1": "val1" },
               "id": null}

            <-- {"jsonrpc": "2.0",
               "result": { "res1": "val1" },
               "id": null}
    """
    routing = kw.copy()
    # force le type en json
    routing['type'] = 'json'

    def real_decorator(func):
        """Méthode pour créer un décorateur avec arguments."""
        if route:
            if isinstance(route, list):
                routes = route
            else:
                routes = [route]
            routing['routes'] = routes

        @wraps(func)
        def wrapper(*args, **kwargs):
            """Wrapper permettant de surcharger les arguments d'appel ET réponse."""
            # surchage des arguments de méthode si request args n'est pas un dictionnaire
            if request._request_args:
                if isinstance(request._request_args, Iterable):
                    args += tuple(request._request_args)
                else:
                    args += (request._request_args,)
            # Update args with jsonrequest if exist
            kwargs.update(getattr(request, 'jsonrequest', {}))
            # binding des kwargs dans le cas d'une méthode non jsonrpc
            request_kwargs = {key: value for key, value in list(request.httprequest.args.items()) if
                              not key.startswith('_')}
            kwargs.update(request_kwargs)

            # appel de la méthode décoré (et des éventuels autres décorateurs)
            response = func(*args, **kwargs)

            def _json_response_with_http_code(self, result=None, error=None):
                """Custom réponse json permettant la gestion des codes HTTP.

                Permet aussi la possibilité de prendre la main sur le contenu de la réponse au besoin.

                :param self: explicite
                :param result: réponse du web service, si type http.Response, la réponse n'est pas altéré
                :param error:
                :return: http.Response
                """
                if isinstance(result, http.Response):
                    return result
                else:
                    data = {}
                    # dans le cas de la présence d'un ID de query, l'ID est retourné dans la réponse
                    if self.jsonrequest.get('id', False):
                        data['id'] = self.jsonrequest.get('id')
                    status_code = 200
                    if isinstance(result, werkzeug.exceptions.HTTPException):
                        status_code = str(result.code or 500) + (' ' + result.name if result.name else '')
                        data['result'] = make_error(result.description, result.code)
                    elif isinstance(result, Exception):
                        status_code = 500
                        data['result'] = make_error(str(result), result.code)
                    elif result is not None:
                        data['result'] = result
                    if error is not None:
                        data['result'] = {'error': error}

                    mime = 'application/json'
                    body = json.dumps(data)

                    return Response(body, status=status_code,
                                    headers=[('Content-Type', mime), ('Content-Length', len(body))])

            # Monkey patch response method
            request._json_response = type(request._json_response)(_json_response_with_http_code, request,
                                                                  JsonRequest)
            return response

        # nécessaire pour référencer la route lors de la génération de la routing map
        wrapper.routing = routing
        wrapper.original_func = func
        return wrapper

    return real_decorator


def standard_response(func):  # noqa 901
    @wraps(func)
    def wrap_args(*args, **kwargs):
        if request._request_type == 'json':
            def _json_response_with_http_code(self, result=None, error=None):
                response = {
                    'id': self.jsonrequest.get('id')
                }
                status_code = 200
                if isinstance(result, werkzeug.exceptions.HTTPException):
                    status_code = str(result.code or 500) + (' ' + result.name if result.name else '')
                    response['result'] = make_error(result.description, result.code)
                elif isinstance(result, Exception):
                    status_code = 500
                    response['result'] = make_error(str(result), result.code)
                elif result is not None:
                    response['result'] = result
                if error is not None:
                    response['result'] = {'error': error}

                if self.jsonp:
                    # If we use jsonp, that's mean we are called from another host
                    # Some browser (IE and Safari) do no allow third party cookies
                    # We need then to manage http sessions manually.
                    response['session_id'] = self.session.sid
                    mime = 'application/javascript'
                    body = "%s(%s);" % (self.jsonp, json.dumps(response),)
                else:
                    mime = 'application/json'
                    body = json.dumps(response)

                resp = Response(body, status=status_code,
                                headers=[('Content-Type', mime), ('Content-Length', len(body))])
                return resp

            # Monkey patch response method
            request._json_response = type(request._json_response)(_json_response_with_http_code, request,
                                                                  JsonRequest)
            # request._json_response = types.MethodType(JsonRequestcustom._json_response, request)
            # request._json_response = JsonRequestcustom._json_response(request)
            return func(*args, **kwargs)
        else:
            def data2xml(d, name='data'):
                r = etree.Element(name)
                return etree.tostring(buildxml(r, d))

            def buildxml(r, d):
                if isinstance(d, dict):
                    for k, v in list(d.items()):
                        s = etree.SubElement(r, k)
                        buildxml(s, v)
                elif isinstance(d, tuple) or isinstance(d, list):
                    for v in d:
                        s = etree.SubElement(r, 'i')
                        buildxml(s, v)
                elif isinstance(d, str):
                    r.text = d
                else:
                    r.text = str(d)
                return r

            result = func(*args, **kwargs)
            if isinstance(result, dict):
                result = data2xml(result, 'result')
            return result

    return wrap_args


def gzip_response(response, compress_level=6):
    """Utility method to zip a response."""
    from io import BytesIO
    import gzip
    # Compress the response
    if response.status_code != 200 or len(response.data) < 500 or 'Content-Encoding' in response.headers:
        return response

    gzip_buffer = BytesIO()
    gzip_file = gzip.GzipFile(mode='wb', compresslevel=compress_level, fileobj=gzip_buffer)
    gzip_file.write(response.data)
    gzip_file.close()
    response.data = gzip_buffer.getvalue()
    response.headers['Content-Encoding'] = 'gzip'
    response.headers['Content-Length'] = str(len(response.data))

    return response


def make_error(message, code=500):
    """Méthode standard de retour d'erreur."""
    return {'error': {'code': code, 'message': message}}
