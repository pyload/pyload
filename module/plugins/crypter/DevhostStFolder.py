# -*- coding: utf-8 -*-
#
# Test links:
# http://d-h.st/users/shine/?fld_id=37263#files

import re

from urlparse import urljoin

from module.plugins.internal.SimpleCrypter import SimpleCrypter


class DevhostStFolder(SimpleCrypter):
    __name__ = "DevhostStFolder"
    __type__ = "crypter"
    __version__ = "0.02"

    __pattern__ = r'http://(?:www\.)?d-h\.st/users/(?P<USER>\w+)(/\?fld_id=(?P<ID>\d+))?'

    __description__ = """d-h.st folder decrypter plugin"""
    __authors__ = [("zapp-brannigan", "fuerst.reinje@web.de"),
                   ("Walter Purcaro", "vuolter@gmail.com")]


    LINK_PATTERN = r'(?:/> |;">)<a href="(.+?)"(?!>Back to \w+<)'
    OFFLINE_PATTERN = r'"/cHP">test\.png<'


    def getPackageNameAndFolder(self):
        try:
            id = re.match(self.__pattern__, self.pyfile.url).group('ID')
            if id == "0":
                raise

            p = r'href="(.+?)">Back to \w+<'
            m = re.search(p, self.html)
            html = self.load(urljoin("http://d-h.st", m.group(1)),
                             cookies=False)

            p = '\?fld_id=%s.*?">(.+?)<' % id
            m = re.search(p, html)
            name = folder = m.group(1)

        except Exception, e:
            self.logDebug(str(e))
            name = folder = re.match(self.__pattern__, self.pyfile.url).group('USER')

        return name, folder


    def getLinks(self):
        return [urljoin("http://d-h.st", link) for link in re.findall(self.LINK_PATTERN, self.html)]
