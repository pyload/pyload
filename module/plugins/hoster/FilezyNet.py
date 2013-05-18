# -*- coding: utf-8 -*-
from module.plugins.hoster.XFileSharingPro import XFileSharingPro, create_getInfo

class FilezyNet(XFileSharingPro):
  __name__ = "FilezyNet"
  __type__ = "hoster"
  __version__ = "0.1"
  __pattern__ = r"http://filezy.net/.*/.*.html"
  __description__ = """filezy.net hoster plugin"""

  HOSTER_NAME = "filezy.net"

  FILE_SIZE_PATTERN = r'<span class="plansize">(?P<S>[0-9.]+) (?P<U>[kKMG])i?B</span>'
  WAIT_PATTERN = r'<div id="countdown_str" class="seconds">\n<!--Wait--> <span id=".*?">(\d+)</span>'

  def setup(self):
    self.resumeDownload = True
    self.multiDL = self.premium

getInfo = create_getInfo(FilezyNet)
