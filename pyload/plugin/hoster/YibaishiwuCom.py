# -*- coding: utf-8 -*-

import re

from pyload.utils import json_loads
from pyload.plugin.internal.SimpleHoster import SimpleHoster


class YibaishiwuCom(SimpleHoster):
    __name    = "YibaishiwuCom"
    __type    = "hoster"
    __version = "0.14"

    __pattern = r'http://(?:www\.)?(?:u\.)?115\.com/file/(?P<ID>\w+)'
    __config  = [("use_premium", "bool", "Use premium account if available", True)]

    __description = """115.com hoster plugin"""
    __license     = "GPLv3"
    __authors     = [("zoidberg", "zoidberg@mujmail.cz")]


    NAME_PATTERN = r'file_name: \'(?P<N>.+?)\''
    SIZE_PATTERN = r'file_size: \'(?P<S>.+?)\''
    OFFLINE_PATTERN = ur'<h3><i style="color:red;">哎呀！提取码不存在！不妨搜搜看吧！</i></h3>'

    LINK_FREE_PATTERN = r'(/\?ct=(pickcode|download)[^"\']+)'


    def handleFree(self, pyfile):
        m = re.search(self.LINK_FREE_PATTERN, self.html)
        if m is None:
            self.error(_("LINK_FREE_PATTERN not found"))

        url = m.group(1)

        self.logDebug(('FREEUSER' if m.group(2) == 'download' else 'GUEST') + ' URL', url)

        res = json_loads(self.load("http://115.com" + url, decode=False))
        if "urls" in res:
            mirrors = res['urls']

        elif "data" in res:
            mirrors = res['data']

        else:
            mirrors = None

        for mr in mirrors:
            try:
                url = mr['url'].replace("\\", "")
                self.logDebug("Trying URL: " + url)
                self.download(url)
                break
            except Exception:
                continue
        else:
            self.fail(_("No working link found"))
