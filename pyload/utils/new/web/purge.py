# -*- coding: utf-8 -*-
#@author: vuolter

from __future__ import unicode_literals
from future import standard_library
standard_library.install_aliases()

import html.parser
import re

from pyload.utils.new import convert
from pyload.utils.new.decorator import iterable


@iterate
def comments(value):
    return re.sub(r' *<!--.*?--> *', " ", value, flags=re.S).strip()


@iterate
def escape(text):
    """
    Removes HTML or XML character references and entities from a text string
    """
    h = html.parser.HTMLParser()
    return h.unescape(text)


@iterate
def tags(value):
    return re.sub(r'\s*<.+?>\s*', " ", value, flags=re.S).strip()


#@NOTE: No lower-case conversion
@iterate
def text(value):
    res = escape(value)
    res = tags(res)
    return res.strip('\'" ')
