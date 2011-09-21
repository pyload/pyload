#!/usr/bin/env python
# -*- coding: utf-8 -*-

import gzip

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

class StripPathMiddleware(object):
    def __init__(self, app):
        self.app = app

    def __call__(self, e, h):
        e['PATH_INFO'] = e['PATH_INFO'].rstrip('/')
        return self.app(e, h)


class PrefixMiddleware(object):
    def __init__(self, app, prefix="/pyload"):
        self.app = app
        self.prefix = prefix

    def __call__(self, e, h):
        path = e["PATH_INFO"]
        if path.startswith(self.prefix):
            e['PATH_INFO'] = path.replace(self.prefix, "", 1)
        return self.app(e, h)

# (c) 2005 Ian Bicking and contributors; written for Paste (http://pythonpaste.org)
# Licensed under the MIT license: http://www.opensource.org/licenses/mit-license.php

# (c) 2005 Ian Bicking and contributors; written for Paste (http://pythonpaste.org)
# Licensed under the MIT license: http://www.opensource.org/licenses/mit-license.php

# WSGI middleware
# Gzip-encodes the response.

class GZipMiddleWare(object):

    def __init__(self, application, compress_level=6):
        self.application = application
        self.compress_level = int(compress_level)

    def __call__(self, environ, start_response):
        if 'gzip' not in environ.get('HTTP_ACCEPT_ENCODING', ''):
            # nothing for us to do, so this middleware will
            # be a no-op:
            return self.application(environ, start_response)
        response = GzipResponse(start_response, self.compress_level)
        app_iter = self.application(environ,
                                    response.gzip_start_response)
        if app_iter is not None:
            response.finish_response(app_iter)

        return response.write()

def header_value(headers, key):
    for header, value in headers:
        if key.lower() == header.lower():
            return value

def update_header(headers, key, value):
    remove_header(headers, key)
    headers.append((key, value))

def remove_header(headers, key):
    for header, value in headers:
        if key.lower() == header.lower():
            headers.remove((header, value))
            break

class GzipResponse(object):

    def __init__(self, start_response, compress_level):
        self.start_response = start_response
        self.compress_level = compress_level
        self.buffer = StringIO()
        self.compressible = False
        self.content_length = None
        self.headers = ()

    def gzip_start_response(self, status, headers, exc_info=None):
        self.headers = headers
        ct = header_value(headers,'content-type')
        ce = header_value(headers,'content-encoding')
        cl = header_value(headers, 'content-length')
        if cl:
            cl = int(cl)
        else:
            cl = 201
        self.compressible = False
        if ct and (ct.startswith('text/') or ct.startswith('application/')) \
            and 'zip' not in ct and cl > 200:
            self.compressible = True
        if ce:
            self.compressible = False
        if self.compressible:
            headers.append(('content-encoding', 'gzip'))
        remove_header(headers, 'content-length')
        self.headers = headers
        self.status = status
        return self.buffer.write

    def write(self):
        out = self.buffer
        out.seek(0)
        s = out.getvalue()
        out.close()
        return [s]

    def finish_response(self, app_iter):
        if self.compressible:
            output = gzip.GzipFile(mode='wb', compresslevel=self.compress_level,
                fileobj=self.buffer)
        else:
            output = self.buffer
        try:
            for s in app_iter:
                output.write(s)
            if self.compressible:
                output.close()
        finally:
            if hasattr(app_iter, 'close'):
                try:
                    app_iter.close()
                except :
                    pass

        content_length = self.buffer.tell()
        update_header(self.headers, "Content-Length" , str(content_length))
        self.start_response(self.status, self.headers)