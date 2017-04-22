# -*- coding: utf-8 -*-
#
# Test links:
# http://d-h.st/users/shine/?fld_id=37263#files

import re
import urlparse

from ..internal.SimpleCrypter import SimpleCrypter


class DevhostStFolder(SimpleCrypter):
    __name__ = "DevhostStFolder"
    __type__ = "crypter"
    __version__ = "0.12"
    __status__ = "testing"

    __pattern__ = r'http://(?:www\.)?d-h\.st/users/(?P<USER>\w+)(/\?fld_id=(?P<ID>\d+))?'
    __config__ = [("activated", "bool", "Activated", True),
                  ("use_premium", "bool", "Use premium account if available", True),
                  ("folder_per_package", "Default;Yes;No",
                   "Create folder for each package", "Default"),
                  ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10)]

    __description__ = """D-h.st folder decrypter plugin"""
    __license__ = "GPLv3"
    __authors__ = [("zapp-brannigan", "fuerst.reinje@web.de"),
                   ("Walter Purcaro", "vuolter@gmail.com")]

    LINK_PATTERN = r'(?:/> |;">)<a href="(.+?)"(?!>Back to \w+<)'
    OFFLINE_PATTERN = r'"/cHP">test\.png<'

    # TODO: Rewrite
    def check_name_size(self, getinfo=True):
        if not self.info or getinfo:
            self.log_debug("File info (BEFORE): %s" % self.info)
            self.info.update(self.get_info(self.pyfile.url, self.data))
            self.log_debug("File info (AFTER): %s" % self.info)

        try:
            if self.info['pattern']['ID'] == "0":
                raise Exception

            p = r'href="(.+?)">Back to \w+<'
            m = re.search(p, self.data)
            html = self.load(urlparse.urljoin("http://d-h.st/", m.group(1)),
                             cookies=False)

            p = '\?fld_id=%s.*?">(.+?)<' % self.info['pattern']['ID']
            m = re.search(p, html)
            self.pyfile.name = m.group(1)

        except Exception, e:
            self.log_debug(e, trace=True)
            self.pyfile.name = self.info['pattern']['USER']

        try:
            folder = self.info['folder'] = self.pyfile.name

        except Exception:
            pass

        self.log_debug("File name: %s" % self.pyfile.name,
                       "File folder: %s" % self.pyfile.name)
