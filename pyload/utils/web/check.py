# -*- coding: utf-8 -*-
# @author: vuolter

from __future__ import absolute_import, unicode_literals

import os
import re
from builtins import map

import idna
import requests
import validators
from future import standard_library

from . import format
from .convert import splitaddress

standard_library.install_aliases()


def isipv4(value):
    try:
        validators.ipv4(value)
    except validators.ValidationFailure:
        return False
    return True


def isipv6(value):
    try:
        validators.ipv6(value)
    except validators.ValidationFailure:
        return False
    return True


def isip(value):
    return isipv4(value) or isipv6(value)


def isport(value):
    return 0 <= value <= 65535


_RE_ISH = re.compile(r'(?!-)[\w^_]{1,63}(?<!-)$', flags=re.I)

def ishost(value):
    MAX_HOSTNAME_LEN = 253
    try:
        value = idna.encode(value)
    except AttributeError:
        pass
    if value.endswith('.'):
        value = value[:-1]
    if not value or len(value) > MAX_HOSTNAME_LEN:
        return False
    return all(map(_RE_ISH.match, value.split('.')))


def issocket(value):
    ip, port = splitaddress(value)
    return isip(ip) and isport(port)


def isendpoint(value):
    host, port = splitaddress(value)
    return ishost(host) and isport(port)


def isonline(url, *args, **kwargs):
    online = True
    url = format.url(url)

    kwargs.setdefault('allow_redirects', True)
    kwargs.setdefault('verify', False)
    try:
        requests.head(url, *args, **kwargs).raise_for_status()
    except requests.TooManyRedirects:
        online = True
    except (requests.ConnectionError, requests.ConnectTimeout):
        online = None
    except requests.RequestException:
        online = False

    return online


def isresource(url, *args, **kwargs):
    url = format.url(url)

    kwargs.setdefault('allow_redirects', True)
    kwargs.setdefault('verify', False)
    r = requests.head(url, *args, **kwargs)

    if 'content-disposition' in r.headers:
        return True

    mime = ""
    content = r.headers.get('content-type')
    if content:
        mime, _, _ = content.rpartition("charset=")
    else:
        from . import parse

        name = parse.name(url)
        _, ext = os.path.splitext(name)
        if ext:
            mime = parse.mime(name)

    if 'html' not in mime:
        return True

    return False


# TODO: Recheck in 0.5.x
def isurl(url):
    url = format.url(url)
    try:
        return validators.url(url)
    except validators.ValidationFailure:
        return False
