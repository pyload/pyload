#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals

import sys
import io
import mimetools
import mimetypes
from os import remove, write

from six.moves import cStringIO
from six.moves.urllib.parse import urlencode
from six.moves.urllib.request import BaseHandler, HTTPHandler, build_opener

# 02/2006 Will Holcomb <wholcomb@gmail.com>
# 7/26/07 Slightly modified by Brian Schneider in order to support unicode
# files ( multipart_encode function )

"""
Usage:
  Enables the use of multipart/form-data for posting forms

Inspirations:
  Upload files in python:
    http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/146306
  urllib2_file:
    Fabien Seisen: <fabien@seisen.org>

Example:
  import MultipartPostHandler, urllib2, cookielib

  cookies = cookielib.CookieJar()
  opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookies),
                                MultipartPostHandler.MultipartPostHandler)
  params = { "username" : "bob", "password" : "riviera",
             "file" : open("filename", "rb") }
  opener.open("http://wwww.bobsite.com/upload/", params)

Further Example:
  The main function of this file is a sample which downloads a page and
  then uploads it to the W3C validator.
"""


class Callable:
    def __init__(self, anycallable):
        self.__call__ = anycallable


# Controls how sequences are uncoded. If true, elements may be given multiple values by
#  assigning a sequence.
doseq = 1


class MultipartPostHandler(BaseHandler):
    handler_order = HTTPHandler.handler_order - 10  # needs to run first

    def http_request(self, request):
        data = request.get_data()
        if data is not None and not isinstance(data, str):
            v_files = []
            v_vars = []
            try:
                for(key, value) in data.items():
                    if isinstance(value, io.IOBase):  # check io.IOBase (as py2 file)
                        v_files.append((key, value))
                    else:
                        v_vars.append((key, value))
            except TypeError:
                systype, value, traceback = sys.exc_info()
                raise TypeError(
                    "not a valid non-string sequence or mapping object").with_traceback(traceback)

            if len(v_files) == 0:
                data = urlencode(v_vars, doseq)
            else:
                boundary, data = self.multipart_encode(v_vars, v_files)

                contenttype = 'multipart/form-data; boundary={}'.format(boundary)
                if(request.has_header('Content-Type')
                   and request.get_header('Content-Type').find('multipart/form-data') != 0):
                    print(
                        "Replacing {} with {}".format(
                            request.get_header('content-type'),
                            'multipart/form-data'))
                request.add_unredirected_header('Content-Type', contenttype)

            request.add_data(data)

        return request

    def multipart_encode(self, vars, files, boundary=None, buf=None):
        if boundary is None:
            boundary = mimetools.choose_boundary()
        if buf is None:
            buf = cStringIO()
        for(key, value) in vars:
            buf.write('--{}\r\n'.format(boundary))
            buf.write('Content-Disposition: form-data; name="{}"'.format(key))
            buf.write('\r\n\r\n' + value + '\r\n')
        for(key, fd) in files:
            #file_size = os.fstat(fd.fileno())[stat.ST_SIZE]
            filename = fd.name.split('/')[-1]
            contenttype = mimetypes.guess_type(
                filename)[0] or 'application/octet-stream'
            buf.write('--{}\r\n'.format(boundary))
            buf.write(
                'Content-Disposition: form-data; name="{}"; filename="{}"\r\n'.format(key, filename))
            buf.write('Content-Type: {}\r\n'.format(contenttype))
            # buffer += 'Content-Length: {}\r\n'.format(file_size)
            fd.seek(0)
            buf.write('\r\n' + fd.read() + '\r\n')
        buf.write('--' + boundary + '--\r\n\r\n')
        buf = buf.getvalue()
        return boundary, buf
    multipart_encode = Callable(multipart_encode)

    https_request = http_request


def main():
    import tempfile
    import sys

    validatorURL = "http://validator.w3.org/check"
    opener = build_opener(MultipartPostHandler)

    def validateFile(url):
        temp = tempfile.mkstemp(suffix=".html")
        write(temp[0], opener.open(url).read())
        params = {"ss": "0",            # show source
                  "doctype": "Inline",
                  "uploaded_file": open(temp[1], "rb")}
        print(opener.open(validatorURL, params).read())
        remove(temp[1])

    if len(sys.argv[1:]) > 0:
        for arg in sys.argv[1:]:
            validateFile(arg)
    else:
        validateFile("http://www.google.com")


if __name__ == "__main__":
    main()
