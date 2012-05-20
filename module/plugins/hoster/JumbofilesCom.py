# -*- coding: utf-8 -*-
import re
from module.plugins.hoster.XFileSharingPro import XFileSharingPro, create_getInfo
from module.utils import html_unescape

class JumbofilesCom(XFileSharingPro):
    __name__ = "JumbofilesCom"
    __type__ = "hoster"
    __pattern__ = r"http://(?:\w*\.)*(jumbofiles.com)/\w{12}"
    __version__ = "0.01"
    __description__ = """JumboFiles.com hoster plugin"""
    __author_name__ = ("zoidberg")
    __author_mail__ = ("zoidberg@mujmail.cz")
    
    FILE_INFO_PATTERN = '<TR><TD>(?P<N>[^<]+?)\s*<small>\((?P<S>[\d.]+)\s*(?P<U>[KMG][bB])\)</small></TD></TR>'
    FILE_OFFLINE_PATTERN = 'Not Found or Deleted / Disabled due to inactivity or DMCA'
    DIRECT_LINK_PATTERN = '<FORM METHOD="LINK" ACTION="(.*?)"'

getInfo = create_getInfo(JumbofilesCom)