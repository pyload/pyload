# -*- coding: utf-8 -*-

import html
import re
from email.header import decode_header as decode_rfc2047_header

_RE_COMMENTS = re.compile(r"<!--(?:(?!<!--).)*-->", flags=re.S)
_RE_TAGS = re.compile(r"<[^<]+?>")
_RE_RFC2047 = re.compile(r"=\?([^?]+)\?([QB])\?([^?]*)\?=")


def comments(value):
    """Removes HTML comments from a text string."""
    return _RE_COMMENTS.sub("", value).strip()


def unescape(value):
    """Translates HTML or XML escape character references and entities from a text string."""
    return html.unescape(value)


def tags(value):
    """Removes HTML tags from a text string."""
    return _RE_TAGS.sub("", value).strip()


def rfc2047(value):
    """Decodes RFC2047 email message header value"""
    def decode_chunk(m):
        data, encoding = decode_rfc2047_header(m.group(0))[0]
        try:
            res = data.decode(encoding)
        except (LookupError, UnicodeEncodeError):
            res = m.group(0)

        return res

    return _RE_RFC2047.sub(decode_chunk, value, re.I)


def text(value):
    """Removes HTML tags, translate HTML escape characters and removes surrounding quotation marks"""
    return tags(unescape(value)).strip("'\" ")
