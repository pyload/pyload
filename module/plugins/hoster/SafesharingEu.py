# -*- coding: utf-8 -*-
#
# Test link:
# http://safesharing.eu/h1ijvcrpl9ys

# Test link (offline):
# http://safesharing.eu/h1ijvcrpl9ysgggggg

from module.plugins.internal.XFSPHoster import XFSPHoster, create_getInfo


class SafesharingEu(XFSPHoster):
    __name__ = "SafesharingEu"
    __type__ = "hoster"
    __version__ = "0.02"

    __pattern__ = r'https?://(?:\w+\.)?safesharing.eu/\w+'

    __description__ = """Safesharing.eu hoster plugin"""
    __license__ = "GPLv3"
    __authors__ = [("zapp-brannigan", "fuerst.reinje@web.de")]

    HOSTER_NAME = "safesharing.eu"

    FILE_NAME_PATTERN = r'Filename:</b></td><td nowrap>(?P<N>.*)</td></tr>'
    FILE_SIZE_PATTERN = r'Size:</b></td><td>(?P<S>.*) (?P<U>[kKmMbB]*) <small>'

    FILE_ID_PATTERN = r'<input type="hidden" name="id" value="(.*)">'
    FILE_OFFLINE_PATTERN = r'<Title>File Not Found</Title>'

    WAIT_PATTERN = r'You have to wait (\d+) minutes'
    COUNTDOWN_PATTERN = r'<br><span id="countdown_str">Wait <span id=".*">(\d+)</span> seconds</span>'

    RECAPTCHA_KEY_PATTERN = r'<script type="text/javascript" src="http://www.google.com/recaptcha/api/challenge\?k=(.*)"></script>'
    RANDOM_STRING_PATTERN = r'<input type="hidden" name="rand" value="(.*)">'


getInfo = create_getInfo(SafesharingEu)
