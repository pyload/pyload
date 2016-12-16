# -*- coding: utf-8 -*-

from __future__ import unicode_literals
from pyload.network.requestfactory import get_url
from pyload.plugins.internal.multihoster import MultiHoster


class RehostTo(MultiHoster):
    __name__ = "RehostTo"
    __version__ = "0.43"
    __type__ = "hook"

    __config__ = [("activated", "bool", "Activated", False),
                  ("hosterListMode", "all;listed;unlisted", "Use for hosters (if supported)", "all"),
                  ("hosterList", "str", "Hoster list (comma separated)", ""),
                  ("unloadFailing", "bool", "Revert to stanard download if download fails", False),
                  ("interval", "int", "Reload interval in hours (0 to disable)", 24)]

    __description__ = """Rehost.to hook plugin"""
    __author_name__ = "RaNaN"
    __author_mail__ = "Mast3rRaNaN@hotmail.de"

    def get_hoster(self):
        page = get_url("http://rehost.to/api.php?cmd=get_supported_och_dl&long_ses=%s" % self.long_ses)
        return [x.strip() for x in page.replace("\"", "").split(",")]

    def core_ready(self):
        self.account = self.pyload.accountManager.get_account_plugin("RehostTo")

        user = self.account.selectAccount()[0]

        if not user:
            self.logError("Rehost.to: " + _("Please add your rehost.to account first and restart pyLoad"))
            return

        data = self.account.getAccountInfo(user)
        self.ses = data["ses"]
        self.long_ses = data["long_ses"]

        return MultiHoster.coreReady(self)
