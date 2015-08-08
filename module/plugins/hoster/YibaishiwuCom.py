# -*- coding: utf-8 -*-

import re
import urlparse

from module.common.json_layer import json_loads
from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo


class YibaishiwuCom(SimpleHoster):
    __name__    = "YibaishiwuCom"
    __type__    = "hoster"
    __version__ = "0.15"
    __status__  = "testing"

    __pattern__ = r'http://(?:www\.)?(?:u\.)?115\.com/file/(?P<ID>\w+)'
    __config__  = [("use_premium", "bool", "Use premium account if available", True)]

    __description__ = """115.com hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("zoidberg", "zoidberg@mujmail.cz")]


    NAME_PATTERN = r'file_name: \'(?P<N>.+?)\''
    SIZE_PATTERN = r'file_size: \'(?P<S>.+?)\''
    OFFLINE_PATTERN = ur'<h3><i style="color:red;">哎呀！提取码不存在！不妨搜搜看吧！</i></h3>'

    LINK_FREE_PATTERN = r'(/\?ct=(pickcode|download)[^"\']+)'


    def handle_free(self, pyfile):
        m = re.search(self.LINK_FREE_PATTERN, self.html)
        if m is None:
            self.error(_("LINK_FREE_PATTERN not found"))

        url = m.group(1)

        self.log_debug(('FREEUSER' if m.group(2) == "download" else 'GUEST') + ' URL', url)

        res = json_loads(self.load(urlparse.urljoin("http://115.com", url), decode=False))
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
                continue
        else:
            self.fail(_("No working link found"))


getInfo = create_getInfo(YibaishiwuCom)
