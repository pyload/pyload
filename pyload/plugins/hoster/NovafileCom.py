# -*- coding: utf-8 -*-
#
# Test links:
# http://novafile.com/vfun4z6o2cit
# http://novafile.com/s6zrr5wemuz4

from pyload.plugins.internal.XFSHoster import XFSHoster, create_getInfo


class NovafileCom(XFSHoster):
    __name    = "NovafileCom"
    __type    = "hoster"
    __version = "0.05"

    __pattern = r'http://(?:www\.)?novafile\.com/\w{12}'

    __description = """Novafile.com hoster plugin"""
    __license     = "GPLv3"
    __authors     = [("zoidberg", "zoidberg@mujmail.cz"),
                       ("stickell", "l.stickell@yahoo.it")]


    HOSTER_DOMAIN = "novafile.com"

    SIZE_PATTERN = r'<div class="size">(?P<S>.+?)</div>'
    ERROR_PATTERN = r'class="alert[^"]*alert-separate"[^>]*>\s*(?:<p>)?(.*?)\s*</'
    LINK_PATTERN = r'<a href="(http://s\d+\.novafile\.com/.*?)" class="btn btn-green">Download File</a>'
    WAIT_PATTERN = r'<p>Please wait <span id="count"[^>]*>(\d+)</span> seconds</p>'


getInfo = create_getInfo(NovafileCom)
