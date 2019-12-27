# -*- coding: utf-8 -*-

from ..internal.DeadHoster import DeadHoster

class ShareonlineBiz(DeadHoster):
    __name__ = "ShareonlineBiz"
    __type__ = "hoster"
    __version__ = "0.73"
    __status__ = "testing"

    __pattern__ = r'https?://(?:www\.)?(share-online\.biz|egoshare\.com)/(download\.php\?id=|dl/)(?P<ID>\w+)'
    __config__ = []

    __description__ = """Shareonline.biz hoster plugin"""
    __license__ = "GPLv3"
    __authors__ = [("spoob", "spoob@pyload.org"),
                   ("mkaay", "mkaay@mkaay.de"),
                   ("zoidberg", "zoidberg@mujmail.cz"),
                   ("Walter Purcaro", "vuolter@gmail.com"),
                   ("GammaC0de", "nitzo2001[AT]yahoo[DOT]com")]
