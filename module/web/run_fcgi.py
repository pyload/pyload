#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys

from flup.server.fcgi_base import BaseFCGIServer
from flup.server.fcgi_base import FCGI_RESPONDER
from flup.server.threadedserver import ThreadedServer


os.environ["DJANGO_SETTINGS_MODULE"] = 'settings'

def handle(*args, **options):
    from django.conf import settings
    from django.utils import translation
    # Activate the current language, because it won't get activated later.
    try:
        translation.activate(settings.LANGUAGE_CODE)
    except AttributeError:
        pass
    #from django.core.servers.fastcgi import runfastcgi
    runfastcgi(args)


FASTCGI_OPTIONS = {
    'protocol': 'fcgi',
    'host': None,
    'port': None,
    'socket': None,
    'method': 'fork',
    'daemonize': None,
    'workdir': '/',
    'pidfile': None,
    'maxspare': 5,
    'minspare': 2,
    'maxchildren': 50,
    'maxrequests': 0,
    'debug': None,
    'outlog': None,
    'errlog': None,
    'umask': None,
}


def runfastcgi(argset=[], **kwargs):
    options = FASTCGI_OPTIONS.copy()
    options.update(kwargs)
    for x in argset:
        if "=" in x:
            k, v = x.split('=', 1)
        else:
            k, v = x, True
        options[k.lower()] = v

    try:
        import flup
    except ImportError, e:
        print >> sys.stderr, "ERROR: %s" % e
        print >> sys.stderr, "  Unable to load the flup package.  In order to run django"
        print >> sys.stderr, "  as a FastCGI application, you will need to get flup from"
        print >> sys.stderr, "  http://www.saddi.com/software/flup/   If you've already"
        print >> sys.stderr, "  installed flup, then make sure you have it in your PYTHONPATH."
        return False

    flup_module = 'server.' + options['protocol']

    if options['method'] in ('prefork', 'fork'):
        wsgi_opts = {
            'maxSpare': int(options["maxspare"]),
            'minSpare': int(options["minspare"]),
            'maxChildren': int(options["maxchildren"]),
            'maxRequests': int(options["maxrequests"]),
        }
        flup_module += '_fork'
    elif options['method'] in ('thread', 'threaded'):
        wsgi_opts = {
            'maxSpare': int(options["maxspare"]),
            'minSpare': int(options["minspare"]),
            'maxThreads': int(options["maxchildren"]),
        }
    else:
        print "ERROR: Implementation must be one of prefork or thread."

    wsgi_opts['debug'] = options['debug'] is not None

    #try:
    #    module = importlib.import_module('.%s' % flup_module, 'flup')
    #    WSGIServer = module.WSGIServer
    #except:
    #    print "Can't import flup." + flup_module
    #    return False

    # Prep up and go
    from django.core.handlers.wsgi import WSGIHandler

    if options["host"] and options["port"] and not options["socket"]:
        wsgi_opts['bindAddress'] = (options["host"], int(options["port"]))
    elif options["socket"] and not options["host"] and not options["port"]:
        wsgi_opts['bindAddress'] = options["socket"]
    elif not options["socket"] and not options["host"] and not options["port"]:
        wsgi_opts['bindAddress'] = None
    else:
        return fastcgi_help("Invalid combination of host, port, socket.")

    daemon_kwargs = {}
    if options['outlog']:
        daemon_kwargs['out_log'] = options['outlog']
    if options['errlog']:
        daemon_kwargs['err_log'] = options['errlog']
    if options['umask']:
        daemon_kwargs['umask'] = int(options['umask'])

    ownWSGIServer(WSGIHandler(), **wsgi_opts).run()

class ownThreadedServer(ThreadedServer):
    def _installSignalHandlers(self):
        return

    def _restoreSignalHandlers(self):
        return


class ownWSGIServer(BaseFCGIServer, ownThreadedServer):

    def __init__(self, application, environ=None,
                 multithreaded=True, multiprocess=False,
                 bindAddress=None, umask=None, multiplexed=False,
                 debug=True, roles=(FCGI_RESPONDER,), forceCGI=False, **kw):
        BaseFCGIServer.__init__(self, application,
                                environ=environ,
                                multithreaded=multithreaded,
                                multiprocess=multiprocess,
                                bindAddress=bindAddress,
                                umask=umask,
                                multiplexed=multiplexed,
                                debug=debug,
                                roles=roles,
                                forceCGI=forceCGI)
        for key in ('jobClass', 'jobArgs'):
            if kw.has_key(key):
                del kw[key]
        ownThreadedServer.__init__(self, jobClass=self._connectionClass,
                                jobArgs=(self,), **kw)

    def _isClientAllowed(self, addr):
        return self._web_server_addrs is None or \
               (len(addr) == 2 and addr[0] in self._web_server_addrs)

    def run(self):
        """
        The main loop. Exits on SIGHUP, SIGINT, SIGTERM. Returns True if
        SIGHUP was received, False otherwise.
        """
        self._web_server_addrs = os.environ.get('FCGI_WEB_SERVER_ADDRS')
        if self._web_server_addrs is not None:
            self._web_server_addrs = map(lambda x: x.strip(),
                                         self._web_server_addrs.split(','))

        sock = self._setupSocket()

        ret = ownThreadedServer.run(self, sock)

        self._cleanupSocket(sock)

        return ret

if __name__ == "__main__":
    handle(*sys.argv[1:])

