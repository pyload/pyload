# -*- coding: utf-8 -*-
# @author: vuolter

from __future__ import absolute_import, unicode_literals

import os
import re
from builtins import map

import IPy
import bottle
import requests
import validators

from future import standard_library
standard_library.install_aliases()

from . import convert as webconvert
from .. import format, parse


__all__ = [
    'ishostname',
    'isonline',
    'isresource',
    'isurl',
    'local_addr',
    'remote_addr']


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


_re_ish = re.compile(r'(?!-)[\w^_]{1,63}(?<!-)$', flags=re.I)

def ishostname(value):
    try:
        name = value.encode('idna')
    except AttributeError:
        name = value
    if name.endswith('.'):
        name = name[:-1]
    if len(name) < 1 or len(name) > 253:
        return False
    try:
        IPy.IP(name)
    except ValueError:
        pass
    else:
        return False
    return all(map(_re_ish.match, name.split('.')))


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
        name = webconvert.url_to_name(url)
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


def local_addr():
    """
    Retrieve current local ip address.
    """
    return bottle.request.urlparts.netloc


def remote_addr():
    return bottle.request.remote_addr
