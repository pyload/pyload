#!/usr/bin/env python
# -*- coding: utf-8 -*-

from bottle import ServerAdapter as BaseAdapter

class ServerAdapter(BaseAdapter):
    SSL = False
    NAME = ""

    def __init__(self, host, port, key, cert, connections, debug, **kwargs):
        BaseAdapter.__init__(self, host, port, **kwargs)
        self.key = key
        self.cert = cert
        self.connection = connections
        self.debug = debug

    @classmethod
    def find(cls):
        """ Check if server is available by trying to import it

        :raises Exception: importing  C dependant library could also fail with other reasons
        :return: True on success
        """
        try:
            __import__(cls.NAME)
            return True
        except ImportError:
            return False

    def run(self, handler):
        raise NotImplementedError


class CherryPyWSGI(ServerAdapter):
    SSL = True
    NAME = "threaded"

    @classmethod
    def find(cls):
        return True

    def run(self, handler):
        from wsgiserver import CherryPyWSGIServer

        if self.cert and self.key:
            CherryPyWSGIServer.ssl_certificate = self.cert
            CherryPyWSGIServer.ssl_private_key = self.key

        server = CherryPyWSGIServer((self.host, self.port), handler, numthreads=self.connection)
        server.start()


class FapwsServer(ServerAdapter):
    """ Does not work very good currently  """

    NAME = "fapws"

    def run(self, handler): # pragma: no cover
        import fapws._evwsgi as evwsgi
        from fapws import base, config

        port = self.port
        if float(config.SERVER_IDENT[-2:]) > 0.4:
            # fapws3 silently changed its API in 0.5
            port = str(port)
        evwsgi.start(self.host, port)
        evwsgi.set_base_module(base)

        def app(environ, start_response):
            environ['wsgi.multiprocess'] = False
            return handler(environ, start_response)

        evwsgi.wsgi_cb(('', app))
        evwsgi.run()


# TODO: ssl
class MeinheldServer(ServerAdapter):
    SSL = True
    NAME = "meinheld"

    def run(self, handler):
        from meinheld import server

        if self.quiet:
            server.set_access_logger(None)
            server.set_error_logger(None)

        server.listen((self.host, self.port))
        server.run(handler)

# todo:ssl
class TornadoServer(ServerAdapter):
    """ The super hyped asynchronous server by facebook. Untested. """

    SSL = True
    NAME = "tornado"

    def run(self, handler): # pragma: no cover
        import tornado.wsgi, tornado.httpserver, tornado.ioloop

        container = tornado.wsgi.WSGIContainer(handler)
        server = tornado.httpserver.HTTPServer(container)
        server.listen(port=self.port)
        tornado.ioloop.IOLoop.instance().start()


class BjoernServer(ServerAdapter):
    """ Fast server written in C: https://github.com/jonashaag/bjoern """

    NAME = "bjoern"

    def run(self, handler):
        from bjoern import run

        run(handler, self.host, self.port)


# todo: ssl
class EventletServer(ServerAdapter):

    SSL = True
    NAME = "eventlet"

    def run(self, handler):
        from eventlet import wsgi, listen

        try:
            wsgi.server(listen((self.host, self.port)), handler,
                log_output=(not self.quiet))
        except TypeError:
            # Needed to ignore the log
            class NoopLog:
                def write(self, *args):
                    pass

            # Fallback, if we have old version of eventlet
            wsgi.server(listen((self.host, self.port)), handler, log=NoopLog())


class FlupFCGIServer(ServerAdapter):

    SSL = False
    NAME = "flup"

    def run(self, handler): # pragma: no cover
        import flup.server.fcgi
        from flup.server.threadedserver import ThreadedServer

        def noop(*args, **kwargs):
            pass

        # Monkey patch signal handler, it does not work from threads
        ThreadedServer._installSignalHandlers = noop

        self.options.setdefault('bindAddress', (self.host, self.port))
        flup.server.fcgi.WSGIServer(handler, **self.options).run()

# Order is important and gives every server precedence over others!
all_server = [BjoernServer, TornadoServer, EventletServer, CherryPyWSGI]
# Some are deactivated because they have some flaws
##all_server = [FapwsServer, MeinheldServer, BjoernServer, TornadoServer, EventletServer, CherryPyWSGI]