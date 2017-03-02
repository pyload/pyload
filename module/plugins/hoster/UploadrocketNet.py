# -*- coding: utf-8 -*-

import re

from ..internal.XFSHoster import XFSHoster


class UploadrocketNet(XFSHoster):
    __name__ = "UploadrocketNet"
    __type__ = "hoster"
    __version__ = "0.02"
    __status__ = "testing"

    __pattern__ = r'http://(?:www\.)?uploadrocket\.net/\w{12}'
    __config__ = [("activated", "bool", "Activated", True),
                  ("use_premium", "bool", "Use premium account if available", True),
                  ("fallback", "bool",
                   "Fallback to free download if premium fails", True),
                  ("chk_filesize", "bool", "Check file size", True),
                  ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10)]

    __description__ = """Uploadrocket.net hoster plugin"""
    __license__ = "GPLv3"
    __authors__ = [("Nico5206", "nico5206git@gmail.com")]

    PLUGIN_DOMAIN = "uploadrocket.net"
    OFFLINE_PATTERN = r'>The file was removed'
    TEMP_OFFLINE_PATTERN = ''
    LINK_PATTERN = r'(https?://(?:www\.)?(?:[^/]*?uploadrocket\.net|\d+\.\d+\.\d+\.\d+)(?:\:\d+)?(?:/d/|(?:/files)?/\d+/\w+/).+?)["\'<]'

    def setup(self):
        self.resume_download = True
        self.multiDL = True

    def _post_parameters(self):
        inputs = XFSHoster._post_parameters(self)

        # Remove parameters added by XFSHoster (method_free/method_premium) and
        # remove the inappropriate inputs
        if not self.premium:
            if 'method_isfree' in inputs:
                inputs.pop('method_free', None)
                inputs.pop('method_ispremium', None)
        elif 'method_ispremium' in inputs:
            inputs.pop('method_isfree', None)
            inputs.pop('method_premium', None)

        return inputs

    def process(self, pyfile):
        # If filename present in url, remove it (else hoster will redirect)
        m = re.search("(.*)/.*.html", pyfile.url, re.S)

        if m is not None and m.group(1):
            self.pyfile.url = m.group(1)

        XFSHoster.process(self, pyfile)

    def download(self, url, get={}, post={}, ref=True, cookies=True,
                 disposition=True, resume=None, chunks=None):
        # Read filename from download url as only present there
        m = re.search(".*/(.*)", url, re.S)

        if m is not None and m.group(1):
            self.pyfile.name = m.group(1)

        XFSHoster.download(
            self, url, get, post, ref, cookies, disposition, resume, chunks)
