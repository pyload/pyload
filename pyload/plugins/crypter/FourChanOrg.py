# -*- coding: utf-8 -*-
#
# Based on 4chandl by Roland Beermann (https://gist.github.com/enkore/3492599)

import re

from pyload.plugins.Crypter import Crypter


class FourChanOrg(Crypter):
    __name__ = "FourChanOrg"
    __type__ = "crypter"
    __version__ = "0.3"

    __pattern__ = r'http://(?:www\.)?boards\.4chan.org/\w+/res/(\d+)'

    __description__ = """4chan.org folder decrypter plugin"""
    __author_name__ = None
    __author_mail__ = None


    def decrypt(self, pyfile):
        pagehtml = self.load(pyfile.url)
        images = set(re.findall(r'(images\.4chan\.org/[^/]*/src/[^"<]*)', pagehtml))
        self.urls = ["http://" + image for image in images]
