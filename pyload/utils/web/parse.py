# -*- coding: utf-8 -*-
#@author: vuolter

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import re

import requests
import tld
from future import standard_library

from pyload.utils import format
from pyload.utils.struct import HeaderDict
from pyload.utils.web import convert as webconvert
from pyload.utils.web import purge as webpurge

standard_library.install_aliases()


# TODO: Recheck result format
def attr(html, name=None):
    pattr = r'{}\s*=\s*(["\']?)((?<=")[^"]+|(?<=\')[^\']+|[^>\s"\'][^>\s]*)\1'
    pattr = pattr.format(name or '\w+')
    m = re.search(pattr, html, re.I)
    return m.group(2) if m else None


def domain(url):
    return tld.get_tld(format.url(url), fail_silently=True)


def form(html, name=None, inputs={}):
    pattr = r'(?P<TAG><form[^>]*{}.*?>)(?P<CONTENT>.*?)</?(form|body|html).*?>'
    pattr = pattr.format(name or "")
    for form in re.finditer(pattr, html, re.I | re.S):
        taginputs = {}
        formaction = attr(form.group('TAG'), "action")

        for inputtag in re.finditer(r'(<(input|textarea).*?>)([^<]*(?=</\2)|)',
                                    webpurge.comments(
                                        form.group('CONTENT')),
                                    re.I | re.S):
            tagname = attr(inputtag.group(1), "name")
            if not tagname:
                continue

            tagvalue = attr(inputtag.group(1), "value")
            taginputs[tagname] = tagvalue or inputtag.group(3) or ""

        if not inputs:
            return formaction, taginputs  #: No attribute check

        #: Check input attributes
        for key, value in inputs.items():
            if key in taginputs:
                if isinstance(value, str) and taginputs[key] == value:
                    continue
                elif isinstance(value, tuple) and taginputs[key] in value:
                    continue
                elif hasattr(value, "search") and re.match(value, taginputs[key]):
                    continue
                else:
                    break  #: Attibute value does not match
            else:
                break  #: Attibute name does not match
        else:
            return formaction, taginputs  #: Passed attribute check

    return None, {}  #: No matching form found


# TODO: Rewrite...
def header(html):
    hdict = HeaderDict()
    pattr = r' *(?P<key>.+?) *: *(?P<value>.+?) *\r?\n'
    for key, value in re.findall(pattr, html):
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
