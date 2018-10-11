# -*- coding: utf-8 -*-
from builtins import _

from pyload.plugins.internal.DeadHoster import DeadHoster


class MegauploadCom(DeadHoster):
    __name__ = "MegauploadCom"
    __type__ = "hoster"
    __version__ = "0.36"
    __status__ = "stable"

    __pattern__ = r'http://(?:www\.)?megaupload\.com/\?.*&?(d|v)=\w+'
    __config__ = []  # TODO: Remove in 0.6.x

    __description__ = """Megaupload.com hoster plugin"""
    __license__ = "GPLv3"
    __authors__ = [("spoob", "spoob@pyload.net")]
