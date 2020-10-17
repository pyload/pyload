# -*- coding: utf-8 -*-
import re

from ..internal.XFSHoster import XFSHoster
from ..internal.misc import search_pattern

class FileuploadCom(XFSHoster):
    __name__ = "FileuploadCom"
    __type__ = "hoster"
    __version__ = "0.01"
    __status__ = "testing"

    __pattern__ = r'https://www.file-upload\.com/\w{12}'
    __config__ = [("activated", "bool", "Activated", True),
                  ("use_premium", "bool", "Use premium account if available", True),
                  ("fallback", "bool", "Fallback to free download if premium fails", True),
                  ("chk_filesize", "bool", "Check file size", True),
                  ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10)]

    __description__ = """Fileupload.com hoster plugin"""
    __license__ = "GPLv3"
    __authors__ = [("OzzieIsaacs", "ozzie.fernandez.isaacs@gmail.com")]

    PLUGIN_DOMAIN = "fileupload.com"

    NAME_PATTERN = r'<input type="hidden" name="fname" value="(?P<N>.+?)">'
    SIZE_PATTERN = r'</span> ((?P<S>[\d.,]+) (?P<U>[\w^_]+))</p>'
    WAIT_PATTERN = '<span class="label label-danger seconds">(\d+)</span>'

    LINK_PATTERN = r'<a id="download-btn" class="btn btn-sm btn-success" href="(.+?)">Click here to download</a>'

    '''def handle_free(self, pyfile):
        self.check_errors()
        self.data = self.load(pyfile.url,
                              post=self._post_parameters(),
                              ref=self.pyfile.url,
                              redirect=False)

        m = search_pattern(self.LINK_PATTERN, self.data, flags=re.M)
        if m is not None:
            self.link = m.group(1)
            return'''
