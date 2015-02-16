# -*- coding: utf-8 -*-
#
# Test links:
# http://novafile.com/vfun4z6o2cit
# http://novafile.com/s6zrr5wemuz4

from pyload.plugin.internal.XFSHoster import XFSHoster


class NovafileCom(XFSHoster):
    __name    = "NovafileCom"
    __type    = "hoster"
    __version = "0.05"

    __pattern = r'http://(?:www\.)?novafile\.com/\w{12}'

    __description = """Novafile.com hoster plugin"""
    __license     = "GPLv3"
    __authors     = [("zoidberg", "zoidberg@mujmail.cz"),
                       ("stickell", "l.stickell@yahoo.it")]


    ERROR_PATTERN = r'class="alert[^"]*alert-separate"[^>]*>\s*(?:<p>)?(.*?)\s*</'
    WAIT_PATTERN  = r'<p>Please wait <span id="count"[^>]*>(\d+)</span> seconds</p>'

    LINK_PATTERN = r'<a href="(http://s\d+\.novafile\.com/.*?)" class="btn btn-green">Download File</a>'
