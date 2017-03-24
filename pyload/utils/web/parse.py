# -*- coding: utf-8 -*-
# @author: vuolter

from __future__ import absolute_import, unicode_literals

import re

import requests
import tld
from future import standard_library
standard_library.install_aliases()

from . import convert as webconvert
from . import purge as webpurge
from .. import format
from ..check import isiterable
from ..struct import HeaderDict


__all__ = ['attr', 'domain', 'form', 'header', 'name']


# TODO: Recheck result format
def attr(html, name=None):
    pattr = r'{}\s*=\s*(["\']?)((?<=")[^"]+|(?<=\')[^\']+|[^>\s"\'][^>\s]*)\1'
    pattr = pattr.format(name or '\w+')
    m = re.search(pattr, html, flags=re.I)
    return m.group(2) if m else None


def domain(url):
    return tld.get_tld(format.url(url), fail_silently=True)


_re_form = re.compile(
    r'(<(input|textarea).*?>)([^<]*(?=</\2)|)',
    flags=re.I | re.S)
    
def _extract_inputs(form):
    taginputs = {}
    for inputtag in _re_form.finditer(
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
                   
        
def form(html, name=None, inputs={}):
    pattr = r'(?P<TAG><form[^>]*{}.*?>)(?P<CONTENT>.*?)</?(form|body|html).*?>'
    pattr = pattr.format(name or "")
    for form in re.finditer(pattr, html, flags=re.I | re.S):
        taginputs = _extract_inputs(form)
        formaction = attr(form.group('TAG'), "action")
        #: Check input attributes
        if not inputs or _same_inputs(taginputs, inputs):
            return formaction, taginputs  #: Passed attribute check
    return None, {}  #: No matching form found


_re_header = re.compile(r' *(?P<key>.+?) *: *(?P<value>.+?) *\r?\n')

# TODO: Rewrite...
def header(html):
    hdict = HeaderDict()
    for key, value in _re_header.findall(html):
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


# TODO: Recheck in 0.5.x
def name(url, *args, **kwargs):
    kwargs.setdefault('allow_redirects', True)
    kwargs.setdefault('verify', False)
    r = requests.head(url, *args, **kwargs)
    cd = r.headers.get('content-disposition')
    return webconvert.url_to_name(cd or url)
