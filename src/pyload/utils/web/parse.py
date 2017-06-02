# -*- coding: utf-8 -*-
# @author: vuolter

from __future__ import absolute_import, unicode_literals

import re
import urllib.parse

import requests

import tld
from future import standard_library

from . import purge as webpurge
from .. import format, purge
from ..check import isiterable
from ..struct import HeaderDict
from .check import ishost, isip, isport
from .convert import host_to_ip, ip_to_host, splitaddress

standard_library.install_aliases()


@purge.args
def socket(text):
    addr, port = splitaddress(text)
    ip = addr if isip(addr) else host_to_ip(addr)
    if port is not None and not isport(port):
        raise ValueError(port)
    return ip, port


@purge.args
def endpoint(text):
    addr, port = splitaddress(text)
    host = addr if ishost(addr) else ip_to_host(addr)
    if port is not None and not isport(port):
        raise ValueError(port)
    return host, port


# TODO: Recheck result format
def attr(text, name=None):
    pattr = r'{}\s*=\s*(["\']?)((?<=")[^"]+|(?<=\')[^\']+|[^>\s"\'][^>\s]*)\1'
    pattr = pattr.format(name or '\w+')
    m = re.search(pattr, text, flags=re.I)
    return m.group(2) if m is not None else None


def domain(url):
    return tld.get_tld(format.url(url), fail_silently=True)


__re_form = re.compile(
    r'(<(input|textarea).*?>)([^<]*(?=</\2)|)', flags=re.I | re.S)

def _extract_inputs(form):
    taginputs = {}
    for inputtag in __re_form.finditer(
            webpurge.comments(form.group('CONTENT'))):
        tagname = attr(inputtag.group(1), "name")
        if not tagname:
            continue
        tagvalue = attr(inputtag.group(1), "value")
        taginputs[tagname] = tagvalue or inputtag.group(3) or ""
    return taginputs


def _same_inputs(taginputs, inputs):
    for key, value in inputs.items():
        if key not in taginputs:
            return False
        tagvalue = taginputs[key]
        if hasattr(value, 'search') and re.match(value, tagvalue):
            continue
        elif isinstance(value, str) and tagvalue == value:
            continue
        elif isiterable(value) and tagvalue in value:
            continue
        return False
    return True


def form(text, name=None, inputs={}):
    pattr = r'(?P<TAG><form[^>]*{}.*?>)(?P<CONTENT>.*?)</?(form|body|html).*?>'
    pattr = pattr.format(name or "")
    for form in re.finditer(pattr, text, flags=re.I | re.S):
        taginputs = _extract_inputs(form)
        formaction = attr(form.group('TAG'), "action")
        #: Check input attributes
        if not inputs or _same_inputs(taginputs, inputs):
            return formaction, taginputs  #: Passed attribute check
    return None, {}  #: No matching form found


__re_header = re.compile(r' *(?P<key>.+?) *: *(?P<value>.+?) *\r?\n')

# TODO: Rewrite...
def header(text):
    hdict = HeaderDict()
    for key, value in __re_header.findall(text):
        key = key.lower()
        if key not in hdict:
            hdict[key] = value
        else:
            header_key = hdict.get(key)
            if isinstance(header_key, list):
                header_key.append(value)
            else:
                hdict[key] = [header_key, value]
    return hdict


def name(url):
    url = format.url(url)
    up = urllib.parse.urlparse(url)
    name = up.path.split('/')[-1]
    if not name:
        name = up.query.split('=', 1)[::-1][0].split('&', 1)[0]
    if not name:
        name = up.netloc.split('.', 1)[0]
    return name.strip()


# TODO: Recheck in 0.5.x
# def grab_name(url, *args, **kwargs):
    # kwargs.setdefault('allow_redirects', True)
    # kwargs.setdefault('verify', False)
    # r = requests.head(url, *args, **kwargs)
    # cd = r.headers.get('content-disposition')
    # return url_to_name(cd or url)
