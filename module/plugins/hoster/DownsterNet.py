# -*- coding: utf-8 -*-
import random
import string

import pycurl

from ..internal.misc import json
from ..internal.MultiHoster import MultiHoster
from ...network.HTTPRequest import BadHeader


class DownsterNet(MultiHoster):
    __name__ = "DownsterNet"
    __type__ = "hoster"
    __version__ = "0.2"
    __status__ = "testing"

    #: Since we want to allow the user to specify the list of hoster to use we let MultiHoster.activate
    # Note: Falling back to ddl leads to wrong file offline recognition for ddl.to
    __pattern__ = r'^unmatchable$'
    __config__ = [
        ("activated", "bool", "Activated", True),
        ("use_premium", "bool", "Use premium account if available", True),
        ("fallback", "bool", "Fallback to free download if premium fails", False),
        ("chk_filesize", "bool", "Check file size", True),
        ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10),
        ("revert_failed", "bool", "Revert to standard download if fails", False)
    ]

    __description__ = """Downster.net hoster plugin"""
    __license__ = "GPLv3"
    __authors__ = [(None, None)]

    FILE_ERRORS = [("Error", r'{"state":"error"}'),
                   ("Retry", r'{"state":"retry"}')]

    # Overwrite this function to prevent cleanCookies to don't remove token cookie
    def clean(self):
        try:
            self.req.close()
        except Exception:
            pass

    def handle_free(self, pyfile):
        try:
            result = self.account.api_request('/download/get', get={'url': pyfile.url})
        except BadHeader as e:
            result = json.loads(e.content)

        if not result['success']:
            if 'offline' in result['error']:
                self.offline()
            else:
                self.fail(result['error'])

        # Setting status may be better for reporting errors seee Base.py:235
        pyfile.name = result['data']['name']
        pyfile.size = int(result['data']['size'])

        self.link = result['data']['downloadUrl']
