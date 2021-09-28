# -*- coding: utf-8 -*-

import re
import urllib.parse

from ..convert import to_str
from . import purge

_RE_DOUBLE_SLASH = re.compile(r"(?<!:)/{2,}")
_RE_UNICODE_ESCAPE = re.compile(r"\\[uU]([\da-fA-F]{4})")


def url(value):
    url = urllib.parse.unquote(to_str(value))

    #: Translate 'unicode-escape' escapes
    url = re.sub(_RE_UNICODE_ESCAPE, lambda x: chr(int(x.group(1), 16)), url)

    #: Removes HTML tags and translate HTML escape characters
    url = purge.text(url)

    #: Decode RFC2047 email message header
    url = purge.rfc2047(url)

    #: Remove redundant '/'
    url = _RE_DOUBLE_SLASH.sub("/", url)

    #: Final cleanup
    url = url.lstrip(".").rstrip("/")

    return url
