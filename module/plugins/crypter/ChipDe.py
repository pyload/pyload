# -*- coding: utf-8 -*-

import re
from module.plugins.Crypter import Crypter


class ChipDe(Crypter):
    __name__ = "ChipDe"
    __type__ = "crypter"
    __pattern__ = r'http://(?:www\.)?chip.de/video/.*\.html'
    __version__ = "0.1"
    __description__ = """Chip.de decrypter plugin"""
    __author_name__ = "4Christopher"
    __author_mail__ = "4Christopher@gmx.de"

    def decrypt(self, pyfile):
        self.html = self.load(pyfile.url)
        try:
            url = re.search(r'"(http://video.chip.de/\d+?/.*)"', self.html).group(1)
            self.logDebug('The file URL is %s' % url)
        except:
            self.fail('Failed to find the URL')

        self.packages.append((pyfile.package().name, [url], pyfile.package().folder))
