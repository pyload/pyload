# -*- coding: utf-8 -*-
# @author: vuolter

from __future__ import absolute_import, unicode_literals

import html.parser
import re

from future import standard_library

standard_library.install_aliases()


__re_comments = re.compile(r'<!--.*?-->', flags=re.S)

def comments(value):
    return __re_comments.sub('', value).strip()


def escape(text):
    """
    Removes HTML or XML character references and entities from a text string.
    """
    h = html.parser.HTMLParser()
    return h.unescape(text)


__re_tags = re.compile(r'<[^<]+?>')

def tags(value):
    return __re_tags.sub('', value).strip()


# NOTE: No case conversion here
def text(value):
    return tags(escape(value)).strip('\'" ')
