# -*- coding: utf-8 -*-

import re

from ..internal.XFSHoster import XFSHoster


class ClicknuploadCom(XFSHoster):
    __name__ = "ClicknuploadCom"
    __type__ = "hoster"
    __version__ = "0.06"
    __status__ = "testing"

    __pattern__ = r'https?://(?:www\.)?clicknupload\.(?:com|org|me|link)/(?P<ID>\w{12})'
    __config__ = [("activated", "bool", "Activated", True),
                  ("use_premium", "bool", "Use premium account if available", True),
                  ("fallback", "bool", "Fallback to free download if premium fails", True),
                  ("chk_filesize", "bool", "Check file size", True),
                  ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10)]

    __description__ = """Clicknupload.com hoster plugin"""
    __license__ = "GPLv3"
    __authors__ = [("tbsn", "tbsnpy_github@gmx.de"),
                   ("GammaC0de", "nitzo2001[AT]yahoo[DOT]com")]

    PLUGIN_DOMAIN = "clicknupload.org"

    URL_REPLACEMENTS = [(__pattern__ + '.*', "https://clicknupload.org/\g<ID>")]

    NAME_PATTERN = r'name="fname" value="(?P<N>.+?)">'
    SIZE_PATTERN = r'<b>Size: (?P<S>[\d.,]+) (?P<U>[\w^_]+)'
    LINK_PATTERN = r'onClick="window.open\(\'(.+?)\'\);"'

    OFFLINE_PATTERN = r'<b>File Not Found</b>'

    WAIT_PATTERN = r'>Please wait <.+?>(\d+)<'
