# -*- coding: utf-8 -*-

from pyload.plugin.internal.XFSHoster import XFSHoster


class SafesharingEu(XFSHoster):
    __name    = "SafesharingEu"
    __type    = "hoster"
    __version = "0.05"

    __pattern = r'https?://(?:www\.)?safesharing\.eu/\w{12}'

    __description = """Safesharing.eu hoster plugin"""
    __license     = "GPLv3"
    __authors     = [("zapp-brannigan", "fuerst.reinje@web.de")]


    ERROR_PATTERN = r'(?:<div class="alert alert-danger">)(.+?)(?:</div>)'
