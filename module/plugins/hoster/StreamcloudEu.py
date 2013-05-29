#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
from module.plugins.Hoster import Hoster

class StreamcloudEu(Hoster):
    __name__ = 'StreamcloudEu'
    __type__ = 'hoster'
    __pattern__ = r'http://streamcloud.eu/.*'
    __version__ = '0.1'
    __description__ = """Streamcloud Video Download Hoster"""
    __author_name__ = ("Seoester")
    __author_mail__ = ("seoester@googlemail.com")

    def process(self, pyfile):
        html = self.load(pyfile.url, decode=True)

        sc_op = re.search(r'<input type="hidden" name="op" value="(.*)">', html)
        sc_usr_login = re.search(r'<input type="hidden" name="usr_login" value="(.*)">', html)
        sc_id = re.search(r'<input type="hidden" name="id" value="(.*)">', html)
        sc_fname = re.search(r'<input type="hidden" name="fname" value="(.*)">', html)
        sc_hash = re.search(r'<input type="hidden" name="hash" value="(.*)">', html)

        pyfile.name = sc_fname.group(1)
        self.logDebug('Filename='+pyfile.name)

        post = {
            "op": sc_op.group(1),
            "usr_login": sc_usr_login.group(1),
            "id": sc_id.group(1),
            "fname": sc_fname.group(1),
            "referer": "",
            "hash": sc_hash.group(1),
            "imhuman": "Watch video now"
        }
        html = self.load(pyfile.url, decode=True, post=post)

        sc_file = re.search(r'file: "(https?://.*/video.mp4)",', html)
        downloadURL = sc_file.group(1)

        self.logDebug(downloadURL)
        self.download(downloadURL)
