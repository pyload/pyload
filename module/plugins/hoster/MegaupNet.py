# -*- coding: utf-8 -*-

import re

from ..internal.SimpleHoster import SimpleHoster
from ..internal.misc import json


class MegaupNet(SimpleHoster):
    __name__ = "MegaupNet"
    __type__ = "hoster"
    __version__ = "0.03"
    __status__ = "testing"

    __pattern__ = r'https?://megaup.net/.+'
    __config__ = [("activated", "bool", "Activated", True),
                  ("use_premium", "bool", "Use premium account if available", True),
                  ("fallback", "bool", "Fallback to free download if premium fails", True),
                  ("chk_filesize", "bool", "Check file size", True),
                  ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10)]

    __description__ = """Megaup.net hoster plugin"""
    __license__ = "GPLv3"
    __authors__ = [("GammaC0de", "nitzo2001[AT]yahoo[DOT]com")]

    NAME_PATTERN = r'File: (?P<N>.+?)<'
    SIZE_PATTERN = r'Size: (?P<S>[\d.,]+) (?P<U>[\w^_]+)'

    OFFLINE_PATTERN = r'The file you are trying to download is no longer available!'
    WAIT_PATTERN = r'var seconds = (\d+);'
    LINK_PATTERN = r'window.location.replace\("(.+?)"\)'

    def handle_free(self, pyfile):
        s = [x for x in re.findall(r"<script[\s\S]*?>([\s\S]*?)</script>", self.data, re.I)
             if "function DeObfuscate_String_and_Create_Form_With_Mhoa_URL" in x]
        if len(s) != 1:
            self.fail(_("deobfuscate function not found"))

        init = """window = {
                    innerWidth: 1280,
                    innerHeight: 567,
                  };
                  var document = {
                    documentElement: {clientWidth: 1280, clientHeight: 567},
                    body: {clientWidth: 1280, clientHeight: 567}
                  };"""
        deobfuscate_script = init + s[0]
        deobfuscate_script = re.sub(r"if\s*\(width_trinh_duyet[\s\S]*",
                                    "return JSON.stringify({idurl:url_da_encrypt, idfilename:FileName, idfilesize:FileSize})};",
                                    deobfuscate_script)

        m = re.search(r"if \(seconds == 0\)[\s\S]+?(DeObfuscate_String_and_Create_Form_With_Mhoa_URL\(.+?\);)", self.data)
        if m is None:
            self.fail(_("deobfuscate function call not found"))

        deobfuscate_script += m.group(1)
        json_data = self.js.eval(deobfuscate_script)

        if not json_data.startswith('{'):
            self.fail(_("Unexpected response, expected JSON data"))

        params = json.loads(json_data)

        self.data = self.load("https://download.megaup.net/", get=params)
        m = re.search(self.LINK_PATTERN, self.data)
        if m is not None:
            self.link = m.group(1)

