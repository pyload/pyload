# -*- coding: utf-8 -*-

import html.parser
import re

_RE_COMMENTS = re.compile(r"<!--.*?-->", flags=re.S)


def comments(value):
    return _RE_COMMENTS.sub("", value).strip()


def escape(text):
    """Removes HTML or XML character references and entities from a text
    string."""
    h = html.parser.HTMLParser()
    return h.unescape(text)


_RE_TAGS = re.compile(r"<[^<]+?>")


def tags(value):
    return _RE_TAGS.sub("", value).strip()


# NOTE: No case conversion here
def text(value):
    return tags(escape(value)).strip("'\" ")
