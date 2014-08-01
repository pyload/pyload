# -*- coding: utf-8 -*-
#
# Test links:
# http://novafile.com/vfun4z6o2cit
# http://novafile.com/s6zrr5wemuz4

from module.plugins.hoster.XFileSharingPro import XFileSharingPro, create_getInfo


class NovafileCom(XFileSharingPro):
    __name__ = "NovafileCom"
    __type__ = "hoster"
    __version__ = "0.02"

    __pattern__ = r'http://(?:www\.)?novafile\.com/\w{12}'

    __description__ = """Novafile.com hoster plugin"""
    __author_name__ = ("zoidberg", "stickell")
    __author_mail__ = ("zoidberg@mujmail.cz", "l.stickell@yahoo.it")

    HOSTER_NAME = "novafile.com"

    FILE_SIZE_PATTERN = r'<div class="size">(?P<S>.+?)</div>'
    ERROR_PATTERN = r'class="alert[^"]*alert-separate"[^>]*>\s*(?:<p>)?(.*?)\s*</'
    LINK_PATTERN = r'<a href="(http://s\d+\.novafile\.com/.*?)" class="btn btn-green">Download File</a>'
    WAIT_PATTERN = r'<p>Please wait <span id="count"[^>]*>(\d+)</span> seconds</p>'


    def setup(self):
        self.multiDL = False


getInfo = create_getInfo(NovafileCom)
