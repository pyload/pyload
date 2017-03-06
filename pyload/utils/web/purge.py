# -*- coding: utf-8 -*-
# @author: vuolter

from __future__ import absolute_import, division, unicode_literals

import re

import html.parser
from future import standard_library

from ..decorator import iterate

standard_library.install_aliases()


__all__ = ['comments', 'escape', 'tags', 'text']


_re_comments = re.compile(r' *<!--.*?--> *', flags=re.S)


@iterate
def comments(value):
    return _re_comments.sub(" ", value).strip()


@iterate
def escape(text):
    """
    Removes HTML or XML character references and entities from a text string.
    """
    h = html.parser.HTMLParser()
    return h.unescape(text)


_re_tags = re.compile(r'\s*<.+?>\s*', flags=re.S)


@iterate
def tags(value):
    return _re_tags.sub(" ", value).strip()


# NOTE: No lower-case conversion
@iterate
def text(value):
    res = escape(value)
    res = tags(res)
    return res.strip('\'" ')
