# -*- coding: utf-8 -*-

import re
from module.plugins.Crypter import Crypter


class ChipDe(Crypter):
    __name__ = "ChipDe"
    __type__ = "crypter"
    __version__ = "0.1"

    __pattern__ = r'http://(?:www\.)?chip.de/video/.*\.html'

    __description__ = """Chip.de decrypter plugin"""
    __author_name__ = "4Christopher"
    __author_mail__ = "4Christopher@gmx.de"


    def decrypt(self, pyfile):
        self.html = self.load(pyfile.url)
        try:
            f = re.search(r'"(http://video.chip.de/\d+?/.*)"', self.html)
        except:
            self.fail('Failed to find the URL')
        else:
            self.urls = [f.group(1)]
            self.logDebug('The file URL is %s' % self.urls[0])
