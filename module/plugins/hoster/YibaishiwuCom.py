# -*- coding: utf-8 -*-

import re
import urlparse

from ..internal.misc import json
from ..internal.SimpleHoster import SimpleHoster


class YibaishiwuCom(SimpleHoster):
    __name__ = "YibaishiwuCom"
    __type__ = "hoster"
    __version__ = "0.19"
    __status__ = "testing"

    __pattern__ = r'http://(?:www\.)?(?:u\.)?115\.com/file/(?P<ID>\w+)'
    __config__ = [("activated", "bool", "Activated", True),
                  ("use_premium", "bool", "Use premium account if available", True),
                  ("fallback", "bool",
                   "Fallback to free download if premium fails", True),
                  ("chk_filesize", "bool", "Check file size", True),
                  ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10)]

    __description__ = """115.com hoster plugin"""
    __license__ = "GPLv3"
    __authors__ = [("zoidberg", "zoidberg@mujmail.cz")]

    NAME_PATTERN = r'file_name: \'(?P<N>.+?)\''
    SIZE_PATTERN = r'file_size: \'(?P<S>.+?)\''
    OFFLINE_PATTERN = ur'<h3><i style="color:red;">哎呀！提取码不存在！不妨搜搜看吧！</i></h3>'

    LINK_FREE_PATTERN = r'(/\?ct=(pickcode|download)[^"\']+)'

    def handle_free(self, pyfile):
        m = re.search(self.LINK_FREE_PATTERN, self.data)
        if m is None:
            self.error(_("LINK_FREE_PATTERN not found"))

        url = m.group(1)

        self.log_debug(
            ('FREEUSER' if m.group(2) == "download" else 'GUEST') +
            ' URL',
            url)

        html = self.load(
            urlparse.urljoin(
                "http://115.com/",
                url),
            decode=False)
        res = json.loads(html)
        if "urls" in res:
            mirrors = res['urls']

        elif "data" in res:
            mirrors = res['data']

        else:
            mirrors = None

        for mr in mirrors:
            try:
                self.link = mr['url'].replace("\\", "")
                self.log_debug("Trying URL: " + self.link)
                break

            except Exception:
                pass
        else:
            self.fail(_("No working link found"))
