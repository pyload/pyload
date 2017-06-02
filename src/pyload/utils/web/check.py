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

from .. import format, parse
from .convert import splitaddress

standard_library.install_aliases()


# TODO: Recheck
# def ismobile():
# if 'mobile' in bottle.request.cookies:
# return parse.boolean(bottle.request.cookies['mobile'])

# if 'application/vnd.wap.xhtml+xml' in bottle.request.headers.get('Accept', '').lower():
# return True

# ua = bottle.request.headers.get('User-Agent', '').lower()
# ua_entries = parse.entries(ua)
# if 'windows' in ua_entries:
# return False
# if 'opera mini' in ua_entries:
# return True
# pattr = r'up.browser|up.link|mmp|symbian|smartphone|midp|wap|phone|android|ios|watchos'
# if re.search(pattr, ua):
# return True

# ua_agent = ua[:4]
# mobile_agents = ['w3c ', 'acs-', 'alav', 'alca', 'amoi', 'audi', 'avan',
# 'benq', 'bird', 'blac', 'blaz', 'brew', 'cell', 'cldc',
# 'cmd-', 'dang', 'doco', 'eric', 'hipt', 'inno', 'ipaq',
# 'java', 'jigs', 'kddi', 'keji', 'leno', 'lg-c', 'lg-d',
# 'lg-g', 'lge-', 'maui', 'maxo', 'midp', 'mits', 'mmef',
# 'mobi', 'mot-', 'moto', 'mwbp', 'nec-', 'newt', 'noki',
# 'palm', 'pana', 'pant', 'phil', 'play', 'port', 'prox',
# 'qwap', 'sage', 'sams', 'sany', 'sch-', 'sec-', 'send',
# 'seri', 'sgh-', 'shar', 'sie-', 'siem', 'smal', 'smar',
# 'sony', 'sph-', 'symb', 't-mo', 'teli', 'tim-', 'tosh',
# 'tsm-', 'upg1', 'upsi', 'vk-v', 'voda', 'wap-', 'wapa',
# 'wapi', 'wapp', 'wapr', 'webc', 'winw', 'winw', 'xda ',
# 'xda-']

# if ua_agent in mobile_agents:
# return True

# return False


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


__re_ish = re.compile(r'(?!-)[\w^_]{1,63}(?<!-)$', flags=re.I)

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
    return all(map(__re_ish.match, value.split('.')))


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
        mime, delemiter, charset = content.rpartition("charset=")
    else:
        name = parse.name(url)
        root, ext = os.path.splitext(name)
        if ext:
            mime = parse.mime(name) or "application/octet-stream"

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
