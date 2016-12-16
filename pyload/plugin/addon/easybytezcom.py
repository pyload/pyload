# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import re

from pyload.plugin.internal.multihoster import MultiHoster


class EasybytezCom(MultiHoster):
    __name__ = "EasybytezCom"
    __version__ = "0.03"
    __type__ = "hook"
    __config__ = [("activated", "bool", "Activated", False),
                  ("hosterListMode", "all;listed;unlisted", "Use for hosters (if supported)", "all"),
                  ("hosterList", "str", "Hoster list (comma separated)", "")]
    __description__ = """EasyBytez.com hook plugin"""
    __author_name__ = "zoidberg"
    __author_mail__ = "zoidberg@mujmail.cz"

    def get_hoster(self):
        self.account = self.pyload.accountmanager.get_account_plugin(self.__name__)
        user = self.account.select_account()[0]

        try:
            req = self.account.get_account_request(user)
            page = req.load("http://www.easybytez.com")

            found = re.search(r'</textarea>\s*Supported sites:(.*)', page)
            return found.group(1).split(',')
        except Exception as e:
            self.log_debug(e)
            self.log_warning("Unable to load supported hoster list, using last known")
            return ['bitshare.com', 'crocko.com', 'ddlstorage.com', 'depositfiles.com', 'extabit.com', 'hotfile.com',
                    'mediafire.com', 'netload.in', 'rapidgator.net', 'rapidshare.com', 'uploading.com', 'uload.to',
                    'uploaded.to']
