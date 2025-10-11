# -*- coding: utf-8 -*-
#       ____________
#   ___/       |    \_____________ _                 _ ___
#  /        ___/    |    _ __ _  _| |   ___  __ _ __| |   \
# /    \___/  ______/   | '_ \ || | |__/ _ \/ _` / _` |    \
# \            ◯ |      | .__/\_, |____\___/\__,_\__,_|    /
#  \_______\    /_______|_|   |__/________________________/
#           \  /
#            \/

import re
import urllib.parse

from ..web.purge import unescape as html_unescape


# def save_join(*args):
# """
# joins a path, encoding aware.
# """
# return fs_encode(
# os.path.join(*[x if isinstance(x, str) else decode(x) for x in args])
# )


# TODO: Remove in 0.6.x
def fixurl(url, unquote=None):
    old = url
    url = urllib.parse.unquote(url)

    if unquote is None:
        unquote = url == old

    # try:
    # url = url.decode("unicode-escape")
    # except UnicodeDecodeError:
    # pass

    url = html_unescape(url)
    url = re.sub(r"(?<!:)/{2,}", "/", url).strip().lstrip(".")

    if not unquote:
        url = urllib.parse.quote(url)

    return url
