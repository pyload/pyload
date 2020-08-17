# -*- coding: utf-8 -*-

import re
import urllib.parse

from ..convert import to_str
from . import purge

_RE_URL = re.compile(r"(?<!:)/{2,}")


def url(obj):
    url = urllib.parse.unquote(to_str(obj).decode("unicode-escape"))
    url = purge.text(url).lstrip(".").lower()
    url = _RE_URL.sub("/", url).rstrip("/")
    return url
