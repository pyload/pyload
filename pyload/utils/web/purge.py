# -*- coding: utf-8 -*-
#@author: vuolter

from __future__ import unicode_literals

import re

import html.parser
from future import standard_library

from pyload.utils.decorator import iterate

standard_library.install_aliases()




@iterate
def comments(value):
    return re.sub(r' *<!--.*?--> *', " ", value, flags=re.S).strip()


@iterate
def escape(text):
    """
    Removes HTML or XML character references and entities from a text string.
    """
    h = html.parser.HTMLParser()
    return h.unescape(text)


@iterate
def tags(value):
    return re.sub(r'\s*<.+?>\s*', " ", value, flags=re.S).strip()


# NOTE: No lower-case conversion
@iterate
def text(value):
    res = escape(value)
    res = tags(res)
    return res.strip('\'" ')
