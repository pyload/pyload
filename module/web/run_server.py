#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import sys
import django
from django.core.servers.basehttp import AdminMediaHandler, WSGIServerException, WSGIServer, WSGIRequestHandler
from django.core.handlers.wsgi import WSGIHandler

os.environ["DJANGO_SETTINGS_MODULE"] = 'settings'

class Output:
     def __init__(self, stream):
        self.stream = stream
     def write(self, data): # Do nothing
        return None
         #self.stream.write(data)
         #self.stream.flush()
     def __getattr__(self, attr):
        return getattr(self.stream, attr)

#sys.stderr = Output(sys.stderr)
#sys.stdout = Output(sys.stdout)

def handle(* args):
    try:
	if len(args) == 1:
	    try:
		addr, port = args[0].split(":")
	    except:
		addr = "127.0.0.1"
		port = args[0]
	else:
	    addr = args[0]
	    port = args[1]
    except:
	addr = '127.0.0.1'
	port = '8000'

    #print addr, port

    admin_media_path = ''
    shutdown_message = ''
    quit_command = (sys.platform == 'win32') and 'CTRL-BREAK' or 'CONTROL-C'

    from django.conf import settings
    from django.utils import translation

    print "Django version %s, using settings %r" % (django.get_version(), settings.SETTINGS_MODULE)
    print "Development server is running at http://%s:%s/" % (addr, port)
    #print "Quit the server with %s." % quit_command

    translation.activate(settings.LANGUAGE_CODE)

    try:
        handler = AdminMediaHandler(WSGIHandler(), admin_media_path)
        run(addr, int(port), handler)

    except WSGIServerException, e:
        # Use helpful error messages instead of ugly tracebacks.
        ERRORS = {
            13: "You don't have permission to access that port.",
            98: "That port is already in use.",
            99: "That IP address can't be assigned-to.",
        }
        try:
            error_text = ERRORS[e.args[0].args[0]]
        except (AttributeError, KeyError):
            error_text = str(e)
        sys.stderr.write(("Error: %s" % error_text) + '\n')
        # Need to use an OS exit because sys.exit doesn't work in a thread
        #os._exit(1)
    except KeyboardInterrupt:
        if shutdown_message:
            print shutdown_message
        sys.exit(0)

class ownRequestHandler(WSGIRequestHandler):
    def log_message(self, format, *args):
        return


def run(addr, port, wsgi_handler):
    server_address = (addr, port)
    httpd = WSGIServer(server_address, ownRequestHandler)
    httpd.set_app(wsgi_handler)
    httpd.serve_forever()

if __name__ == "__main__":
    handle(*sys.argv[1:])
