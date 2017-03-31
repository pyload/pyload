# -*- coding: utf-8 -*-
# @author: vuolter

from __future__ import absolute_import, unicode_literals

import urllib.parse
from builtins import int

from future import standard_library
standard_library.install_aliases()

from pyload.utils import format


__all__ = ['code_to_status', 'url_to_name']


def code_to_status(code):
    code = int(code)
    if code < 400:
        status = 'online'
    elif code < 500:
        status = 'offline'
    elif code < 600:
        status = 'tempoffline'
    else:
        status = 'unknown'
    return status


def url_to_name(url, strict=False):
    url = format.url(url)
    url_p = urllib.parse.urlparse(url)
    name = url_p.path.split('/')[-1]
    if not name:
        name = url_p.query.split('=', 1)[::-1][0].split('&', 1)[0]
    if not name:
        name = url_p.netloc.split('.', 1)[0]
    return name.strip() if strict else format.name(name)
