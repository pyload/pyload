#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re

from module.plugins.Crypter import Crypter

class FourChanOrg(Crypter):
    # Based on 4chandl by Roland Beermann
    # https://gist.github.com/enkore/3492599
    __name__ = "FourChanOrg"
    __type__ = "container"
    __version__ = "0.3"
    __pattern__ = r"http://boards\.4chan.org/\w+/res/(\d+)"
    __description__ = "Downloader for entire 4chan threads"

    def decrypt(self, pyfile):
        pagehtml = self.load(pyfile.url)

        images = set(re.findall(r'(images\.4chan\.org/[^/]*/src/[^"<]*)', pagehtml))
        urls = []
        for image in images:
            urls.append("http://" + image)

        self.core.files.addLinks(urls, self.pyfile.package().id)
