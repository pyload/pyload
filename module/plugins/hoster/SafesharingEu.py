# -*- coding: utf-8 -*-

from module.plugins.internal.XFSHoster import XFSHoster, create_getInfo


class SafesharingEu(XFSHoster):
    __name__    = "SafesharingEu"
    __type__    = "hoster"
    __version__ = "0.05"

    __pattern__ = r'https?://(?:www\.)?safesharing\.eu/\w{12}'

    __description__ = """Safesharing.eu hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("zapp-brannigan", "fuerst.reinje@web.de")]


    HOSTER_DOMAIN = "safesharing.eu"

    WAIT_PATTERN = r'You have to wait (\d+) minutes'

    ERROR_PATTERN = r'(?:<div class="alert alert-danger">)(.+?)(?:</div>)'


getInfo = create_getInfo(SafesharingEu)
