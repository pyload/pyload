# -*- coding: utf-8 -*-

from __future__ import unicode_literals
from pyload.network.requestfactory import get_url
from pyload.plugin.internal.multihoster import MultiHoster


class Premium4Me(MultiHoster):
    __name__ = "Premium4Me"
    __version__ = "0.03"
    __type__ = "hook"

    __config__ = [("activated", "bool", "Activated", False),
                  ("hosterListMode", "all;listed;unlisted", "Use for downloads from supported hosters:", "all"),
                  ("hosterList", "str", "Hoster list (comma separated)", "")]
    __description__ = """Premium.to hook plugin"""
    __author_name__ = ("RaNaN", "zoidberg", "stickell")
    __author_mail__ = ("Mast3rRaNaN@hotmail.de", "zoidberg@mujmail.cz", "l.stickell@yahoo.it")

    def get_hoster(self):
        page = get_url("http://premium.to/api/hosters.php?authcode=%s" % self.account.authcode)
        return [x.strip() for x in page.replace("\"", "").split(";")]

    def core_ready(self):
        self.account = self.pyload.accountmanager.get_account_plugin("Premium4Me")

        user = self.account.select_account()[0]

        if not user:
            self.log_error(_("Please add your premium.to account first and restart pyLoad"))
            return

        return MultiHoster.coreReady(self)
